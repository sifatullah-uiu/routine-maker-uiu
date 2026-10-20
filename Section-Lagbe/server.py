"""Local planner server with durable SQLite uploads. Python 3.10+, no dependencies."""
import argparse
from contextlib import closing
import hashlib
import json
import mimetypes
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, urlparse

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB = APP_DIR.parent / ".planner-data" / "uploads.sqlite3"
MAX_FILE_BYTES = 20 * 1024 * 1024
PUBLIC_FILES = {"index.html", "design.css", "workflow.css", "design.js", "preloaded-data.js"}


def initialize(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    raw_directory(db_path).mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, digest TEXT UNIQUE NOT NULL,
            content BLOB NOT NULL, created_at TEXT NOT NULL
        )""")
        # Raw originals also allow recovery if the database was moved/deleted.
        for file in raw_directory(db_path).glob("*/*"):
            if not file.is_file() or file.suffix.lower() not in {".xlsx", ".xls", ".csv"}:
                continue
            content = file.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if file.parent.name != digest:
                continue
            db.execute("INSERT OR IGNORE INTO uploads(name,digest,content,created_at) VALUES(?,?,?,?)",
                       (file.name, digest, content, datetime.fromtimestamp(file.stat().st_mtime, timezone.utc).isoformat()))
        # Backfill files saved by earlier versions that only stored SQLite BLOBs.
        for name, digest, content in db.execute("SELECT name,digest,content FROM uploads"):
            save_original(db_path, name, digest, content)


def raw_directory(db_path):
    return db_path.parent / (db_path.stem + "-files")


def save_original(db_path, name, digest, content):
    folder = raw_directory(db_path) / digest
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    if target.is_file() and target.read_bytes() == content:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=folder, delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


class PlannerServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, db_path=DEFAULT_DB):
        self.db_path = Path(db_path).resolve()
        initialize(self.db_path)
        super().__init__(address, PlannerHandler)


class PlannerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP_DIR), **kwargs)

    def json_response(self, status, value):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def ensure_storage(self):
        # sqlite.connect silently creates an empty DB: initialize its schema too.
        if not self.server.db_path.exists():
            initialize(self.server.db_path)

    def storage_error(self, error):
        self.log_error("Upload storage error: %s", error)
        self.json_response(503, {"error": "Storage could not be written. Check the server's data-folder permissions and free disk space.",
                                 "code": "storage_unavailable"})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/uploads":
            try:
                self.ensure_storage()
                with closing(sqlite3.connect(self.server.db_path)) as db, db:
                    rows = db.execute(
                        "SELECT id,name,created_at,length(content) FROM uploads ORDER BY id DESC"
                    ).fetchall()
            except (sqlite3.Error, OSError) as error:
                return self.storage_error(error)
            return self.json_response(200, [
                dict(id=r[0], name=r[1], createdAt=r[2], size=r[3]) for r in rows
            ])
        if path.startswith("/api/uploads/"):
            upload_id = path.removeprefix("/api/uploads/")
            if not upload_id.isdigit():
                return self.json_response(404, {"error": "File not found"})
            with closing(sqlite3.connect(self.server.db_path)) as db, db:
                row = db.execute("SELECT name,content FROM uploads WHERE id=?", (upload_id,)).fetchone()
            if not row:
                return self.json_response(404, {"error": "File not found"})
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(row[0])[0] or "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(row[0]))
            self.send_header("Content-Length", str(len(row[1])))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(row[1])
            return
        if path not in {"/"} and path.lstrip("/") not in PUBLIC_FILES:
            return self.send_error(404)
        super().do_GET()

    def do_HEAD(self):
        path = urlparse(self.path).path
        if path != "/" and path.lstrip("/") not in PUBLIC_FILES:
            return self.send_error(404)
        super().do_HEAD()

    def do_POST(self):
        if urlparse(self.path).path != "/api/uploads":
            return self.json_response(404, {"error": "Unknown endpoint"})
        # Same-origin JSON-free binary requests carry a custom header. Cross-origin
        # browsers cannot set it without a preflight; this server grants no CORS.
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.json_response(403, {"error": "Use the planner's own upload screen"})
        if self.headers.get("X-Planner-Upload") != "1":
            return self.json_response(403, {"error": "Missing upload header"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            name = json.loads(self.headers.get("X-File-Name", '""'))
            if not isinstance(name, str):
                raise ValueError()
            name = name.replace("\\", "/").split("/")[-1]
            if not name or len(name) > 255 or any(ord(c) < 32 for c in name):
                raise ValueError()
            if Path(name).suffix.lower() not in {".xlsx", ".xls", ".csv"}:
                return self.json_response(400, {"error": "Use an Excel or CSV file"})
            if not 0 < length <= MAX_FILE_BYTES:
                return self.json_response(413, {"error": "File must be between 1 byte and 20 MB"})
        except (ValueError, TypeError):
            return self.json_response(400, {"error": "Invalid file metadata"})
        self.connection.settimeout(30)
        content = self.rfile.read(length)
        if len(content) != length:
            return self.json_response(400, {"error": "Incomplete upload"})
        digest = hashlib.sha256(content).hexdigest()
        try:
            self.ensure_storage()
            with closing(sqlite3.connect(self.server.db_path)) as db, db:
                db.execute(
                    "INSERT OR IGNORE INTO uploads(name,digest,content,created_at) VALUES(?,?,?,?)",
                    (name, digest, content, datetime.now(timezone.utc).isoformat()),
                )
                row = db.execute("SELECT id,name,created_at FROM uploads WHERE digest=?", (digest,)).fetchone()
                save_original(self.server.db_path, row[1], digest, content)
            return self.json_response(201, dict(id=row[0], name=row[1], createdAt=row[2]))
        except (sqlite3.Error, OSError) as error:
            return self.storage_error(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    server = PlannerServer(("127.0.0.1", args.port), args.database)
    print(f"Planner: http://127.0.0.1:{args.port}\nDatabase: {args.database}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
