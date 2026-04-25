# Eye Tracking — Consumer Attention Analysis

A browser-based eye-tracking system that measures where users look while browsing a vehicle gallery, then renders heatmaps, attention metrics, hotspots, and cold zones for each car.

The project is built around a Flask backend that records gaze data from a webcam-driven study and runs analysis on it server-side. Two standalone Python scripts (using OpenCV + MediaPipe) are also included for local heatmap generation without the web stack.

---

## What's in this repo

| Path | Purpose |
| --- | --- |
| `app.py` | Flask web server. Serves the study UI and exposes the `/api/...` endpoints that record gaze points and produce per-session and per-study analysis. |
| `templates/index.html` | Single-page study UI. Calibrates the webcam, runs a rapid-fire 5-cars-x-5-seconds study, posts gaze points to the backend, and renders the resulting heatmaps. |
| `eye_tracking_heatmap.py` | Standalone desktop script. Opens a camera with OpenCV, tracks eye landmarks via MediaPipe Face Mesh, and plots a KDE heatmap with seaborn after you press `q`. |
| `camera_test.py` | One-screen sanity check that the camera is reachable. |
| `tests/` | Unit tests for the analyzer functions in `app.py` (heatmap grid, attention metrics, hotspots, cold zones, gaze path). |
| `Procfile`, `runtime.txt` | Render / Heroku deployment config. `gunicorn app:app` on Python 3.11.9. |

---

## Running the web app locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000. The page asks for camera permission, walks you through a 9-point calibration, and runs the rapid-fire study.

For production-style serving (mirrors how Render runs it):

```bash
gunicorn app:app
```

---

## Running the standalone heatmap script

This path doesn't go through the browser — it opens a native OpenCV window.

```bash
pip install opencv-python mediapipe numpy matplotlib seaborn
python eye_tracking_heatmap.py
```

Press `q` to stop. A KDE heatmap of your gaze positions will pop up in matplotlib, and a PNG is saved to `output/heatmap_<timestamp>.png`.

---

## API reference

All endpoints live in `app.py`. Sessions and studies are kept in memory — restarting the server clears them.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Serves the study UI. |
| `GET` | `/api/cars` | Returns the list of cars shown in the study (id, name, image URL). |
| `POST` | `/api/study/start` | Starts a rapid-fire study. Body: `{ screen_resolution }`. Returns a `study_id`. |
| `POST` | `/api/session/start` | Starts a single-car session inside a study. Body: `{ car_id, car_name, car_index, screen_resolution, image_dimensions }`. |
| `POST` | `/api/session/<id>/gaze` | Records one gaze point. Body: `{ x, y, relativeX, relativeY, timestamp, confidence, pupil_dilation, head_pose }`. |
| `POST` | `/api/session/<id>/stop` | Ends a session. Returns `total_points`, `duration_seconds`, `first_gaze`, `heatmap_grid`, `attention_metrics`, `hotspots`, `cold_zones`, `gaze_path`. |
| `POST` | `/api/study/<id>/complete` | Closes a study and returns comparative analysis across all cars. |
| `GET` | `/api/session/<id>/export` | Raw JSON dump of a session. |
| `GET` | `/api/study/<id>/export` | Raw JSON dump of a study and all its sessions. |

---

## How the analysis works

When `/api/session/<id>/stop` is called, the server runs five passes over the recorded gaze points:

1. **Heatmap grid** — `generate_heatmap_grid` bins gaze points into a 50×50 grid, applies a Gaussian spread (radius 2 cells, weight `1 - dist/2.5`), and normalizes the max cell to 1.0.
2. **Attention metrics** — `calculate_attention_metrics` computes mean gaze position, dispersion (`sqrt(var_x + var_y)`), total scan-path length, and scan-path efficiency (length per point).
3. **Hotspots** — `identify_hotspots` returns up to the 10 highest-density cells (intensity ≥ 0.8).
4. **Cold zones** — `identify_cold_zones` BFS-floods contiguous low-attention regions (intensity ≤ 0.05) and returns the 5 largest.
5. **Gaze path** — `generate_gaze_path` downsamples to ≤50 points for visualization.

The frontend then draws all of this on top of the car image.

---

## Tests

```bash
pip install pytest
pytest
```

The tests cover the five analyzer functions above, including the empty-input edge cases that previously crashed the API.

---

## Deployment

Configured for one-click deploy on Render.com (or any Procfile-based host):

- `Procfile` → `web: gunicorn app:app`
- `runtime.txt` → `python-3.11.9`
- `requirements.txt` → `Flask`, `Flask-Cors`, `gunicorn`

Sessions are stored in a Python dict, so a single dyno is required. For multi-dyno deploys, swap the `sessions` and `study_sessions` dicts for Redis.

---

## Limitations

- Gaze estimation is approximate — it's a webcam, not a Tobii.
- Calibration drifts when the user moves their head significantly. The new ridge-regression calibration in the latest commit reduces this but doesn't eliminate it.
- All session data is in process memory and is lost on restart.

---

## Author

Aryan Bhimani — Eye Tracking Consumer Attention Analysis (Computer Vision / UX Analytics).
