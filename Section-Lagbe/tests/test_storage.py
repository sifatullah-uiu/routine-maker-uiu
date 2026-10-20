"""Persistence and HTTP contract checks; all files live in an isolated temp DB."""
import json
import hashlib
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import PlannerServer, raw_directory


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="planner-storage-test-")
        self.db = Path(self.temp.name) / "uploads.sqlite3"
        self.start()

    def start(self):
        self.server = PlannerServer(("127.0.0.1", 0), self.db)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def tearDown(self):
        self.stop()
        self.temp.cleanup()

    def upload(self, name, body, **headers):
        request = Request(self.url + "/api/uploads", data=body, headers={
            "X-Planner-Upload": "1", "X-File-Name": json.dumps(name), **headers
        })
        with urlopen(request) as response:
            return json.load(response)

    def test_original_bytes_and_library_survive_server_restart(self):
        content = b"Course Code,Day,Time\r\nCSE 1111,Sat,8:30 AM - 9:50 AM\r\n"
        saved = self.upload("Schedule.csv", content)
        self.assertEqual(saved["id"], self.upload("Duplicate.csv", content)["id"])
        self.stop()
        self.start()
        with urlopen(self.url + "/api/uploads") as response:
            files = json.load(response)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "Schedule.csv")
        with urlopen(self.url + f"/api/uploads/{saved['id']}") as response:
            self.assertEqual(response.read(), content)

    def test_unicode_filename_and_binary_workbook(self):
        content = bytes(range(256))
        saved = self.upload("রুটিন.xlsx", content)
        self.assertEqual(saved["name"], "রুটিন.xlsx")
        with urlopen(self.url + f"/api/uploads/{saved['id']}") as response:
            self.assertEqual(response.read(), content)

    def test_raw_original_and_recovery_after_database_disappears(self):
        content = b"original uploaded workbook bytes"
        self.upload("Original.xlsx", content)
        raw = raw_directory(self.db) / hashlib.sha256(content).hexdigest() / "Original.xlsx"
        self.assertEqual(raw.read_bytes(), content)
        # Only this test's database is removed; original files remain intact.
        self.db.unlink()
        with urlopen(self.url + "/api/uploads") as response:
            files = json.load(response)
        self.assertEqual(files[0]["name"], "Original.xlsx")
        with urlopen(self.url + f"/api/uploads/{files[0]['id']}") as response:
            self.assertEqual(response.read(), content)
        self.upload("Next.csv", b"next original")

    def test_storage_failure_returns_actionable_error_and_can_retry(self):
        with patch("server.save_original", side_effect=PermissionError("Data folder is read-only")):
            with self.assertRaises(HTTPError) as error:
                self.upload("Retry.csv", b"retry contents")
        self.assertEqual(error.exception.code, 503)
        message = json.load(error.exception)
        error.exception.close()
        self.assertIn("permissions", message["error"])
        self.assertTrue(self.upload("Retry.csv", b"retry contents")["id"])

    def test_rejects_invalid_uploads_and_cross_origin_writes(self):
        for name, content, headers, expected in [
            ("script.exe", b"test", {}, 400),
            ("empty.csv", b"", {}, 413),
            ("test.csv", b"test", {"Origin": "https://other.example"}, 403),
        ]:
            with self.subTest(name=name, headers=headers):
                with self.assertRaises(HTTPError) as error:
                    self.upload(name, content, **headers)
                self.assertEqual(error.exception.code, expected)
                error.exception.close()

    def test_database_and_source_are_not_public(self):
        for path in ["/server.py", "/../.planner-data/uploads.sqlite3", "/api/uploads/999"]:
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as error:
                    urlopen(self.url + path)
                self.assertEqual(error.exception.code, 404)
                error.exception.close()


if __name__ == "__main__":
    unittest.main()
