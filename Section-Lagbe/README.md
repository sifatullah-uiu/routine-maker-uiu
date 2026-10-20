# Section Lagbe

**Build a class routine that fits your semester.** Section Lagbe helps students compare course sections, set schedule preferences, and generate conflict-free routine options.

🌐 **Live app:** [sectionlagbe.netlify.app](https://sectionlagbe.netlify.app/)

## Features

- Load the bundled department schedule, upload a spreadsheet, or enter sections manually.
- Select courses and optionally prefer or lock faculty and sections.
- Set class-day limits, daily class limits, time preferences, and blocked periods.
- Generate, filter, compare, share, and export routine options.
- Use the responsive interface on desktop and mobile.

## Run locally

There is no frontend build step. Python 3.10 or newer runs the local server and SQLite upload library, with no additional Python packages.

1. Double-click `start-planner.cmd`, or run `python server.py` in this folder.
2. Open `http://127.0.0.1:4173`.

Use `--port 4174` to choose another port. Stop with Ctrl+C and run the same command to restart.

Uploaded Excel/CSV files are stored intact in `../.planner-data/uploads.sqlite3` and as original files in `../.planner-data/uploads-files/<file-hash>/<original-name>`. They appear under **Saved schedules**, where you can reopen or download the originals. Identical file contents are deduplicated; revised files remain separate. Storage survives browser reloads, clearing preferences, and server restarts. Back up the entire `.planner-data` folder when moving the project. If the database is missing, the server recreates it and recovers the library from the original-file folder. Override its location with `--database PATH`; its sibling `<database-stem>-files` folder holds originals.

Failed saves show the server's actual error and a **Retry saving file** button on the home screen. The selected file remains available for retry until the page is reloaded. Starting a generic static server (`python -m http.server`, Live Server, etc.) serves the UI but cannot save files; use the supplied launcher. Clients access the server's upload API and do not need a copy of the database on their own computer.

This database belongs to the local server on this computer. It is not cloud storage or a multi-user service. A static host can still run the planner, but permanent uploads require this backend and a durable disk; the UI explicitly reports when storage is unavailable. Supported formats remain `.xlsx`, `.xls`, and `.csv`, up to 20 MB. Files are saved before parsing, so an invalid schedule can still be recovered from the library.

The preloaded schedule is loaded from `preloaded-data.js` before the app starts. Copy the whole folder when moving or deploying the app.

The redesigned interface uses warm ivory surfaces, an ink sidebar, terracotta accents, and matching light/dark themes. It includes responsive bottom navigation, keyboard focus indicators, reduced-motion support, and an on-demand **Quick guide**. The original import, selection, preference, generation, comparison, sharing, and export logic stays in `index.html`.

Course selection updates existing cards in place. Selecting a course does not rebuild or reorder the catalog, reset loaded pages, or replay card entrance animations. Faculty choices, pinned sections, scroll position, and focused controls are preserved. The selected-course summary has its own Continue button.

The start screen presents one primary action, with compact file-upload and manual-entry alternatives. The visual direction draws on the restrained hierarchy of [Linear](https://linear.app/), the calendar-first clarity of [Notion Calendar](https://www.notion.com/product/calendar), and the focused interactions of [Raycast](https://www.raycast.com/).

Generation searches every combination permitted by course, faculty, section, time, and day constraints. The search yields between small batches and can be cancelled. The exact result total, filters, sorting, and best match use the full set. Cards appear automatically as you scroll, with timetables drawn only near the viewport; no manual loading is required. Very large selections can still take time and memory because every valid combination must be enumerated.

Results use compact icon-and-button filters. Choosing **3 days** shows exactly three class days; the earlier Preferences screen still sets a maximum. Routine statistics share one compact header, and timetable rows grow with their content while empty days stay short. Course and faculty names continue to wrap fully.

Run checks with `python -m unittest discover -s tests -p test_storage.py` and `node tests/search.test.cjs`. They cover storage across restarts, original-file recovery, duplicate handling, input restrictions, exhaustive search beyond the former cap, and cancellation.

## Update the preloaded schedule

Edit **`preloaded-data.js`**. You do not need to edit the app code in `index.html`.

The file contains two values:

- `window.SECTION_LAGBE_PRELOADED_DATA`: an array with one record for each course section.
- `window.SECTION_LAGBE_PRELOADED_UPDATED`: the date and time shown to users as the data update timestamp.

Each section record follows this format:

```js
{
  "id": 0,
  "type": "Theory",
  "course_code": "CSE 1111",
  "course_name": "Structured Programming Language",
  "section": "A",
  "faculty": "Faculty Name",
  "day": "Sat,Tue",
  "time": "8:30 AM - 9:50 AM",
  "room": "801"
}
```

### Data entry notes

- Add one record per section. Reuse the same course code and course name for all sections of that course.
- Give every record a unique numeric `id`.
- Use `Theory` or `Lab` for `type`.
- Use day abbreviations such as `Sat`, `Sun`, `Mon`, `Tue`, `Wed`, or `Thu`. For a section meeting twice weekly, separate days with a comma, such as `Sat,Tue`.
- Write `time` as a 12-hour range, for example `8:30 AM - 9:50 AM`.
- Use an empty string (`""`) when faculty or room is not known. Use `TBA` for an announced-to-be-determined faculty.
- Keep the JavaScript array syntax valid: records are separated by commas, and the last record has no trailing comma for broad browser compatibility.
- Update the timestamp after changing the schedule.

After editing, reload the app and choose **Preloaded Data** to confirm the new term's sections appear.

## Project structure

```text
.
├── index.html          # App interface, styles, and routine-generation logic
├── design.css          # Theme tokens, app shell, landing page, and responsive layout
├── workflow.css        # Course cards, preferences, timetables, and dialogs
├── design.js           # UI icons, navigation labels, and theme accessibility
├── preloaded-data.js   # Bundled course-section schedule and update timestamp
├── server.py           # Local HTTP server and durable SQLite upload library
├── tests/              # Storage, search, and sample-upload checks
└── README.md           # Project and maintenance guide
```
