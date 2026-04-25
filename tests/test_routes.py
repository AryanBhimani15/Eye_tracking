"""Integration tests for the Flask routes in app.py."""

import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    # Reset in-memory stores between tests
    app_module.sessions.clear()
    app_module.study_sessions.clear()


class TestStartStudy:
    def test_no_body_still_starts(self, client):
        # Missing JSON body should not crash; we accept it as an empty dict.
        resp = client.post("/api/study/start")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "started"
        assert "study_id" in body

    def test_with_body(self, client):
        resp = client.post(
            "/api/study/start", json={"screen_resolution": "1920x1080"}
        )
        assert resp.status_code == 200


class TestStartSession:
    def test_missing_car_id_returns_400(self, client):
        resp = client.post("/api/session/start", json={})
        assert resp.status_code == 400
        assert "car_id" in resp.get_json()["error"]

    def test_no_body_returns_400(self, client):
        resp = client.post("/api/session/start")
        assert resp.status_code == 400

    def test_valid_request_starts_session(self, client):
        resp = client.post(
            "/api/session/start",
            json={"car_id": "bmw-m3", "car_name": "BMW M3"},
        )
        assert resp.status_code == 200
        assert "session_id" in resp.get_json()


class TestRecordGaze:
    def test_unknown_session_returns_404(self, client):
        resp = client.post("/api/session/missing/gaze", json={"x": 100, "y": 100})
        assert resp.status_code == 404

    def test_missing_coords_returns_400(self, client):
        start = client.post("/api/session/start", json={"car_id": "bmw-m3"})
        sid = start.get_json()["session_id"]
        resp = client.post(f"/api/session/{sid}/gaze", json={})
        assert resp.status_code == 400

    def test_records_a_point(self, client):
        start = client.post("/api/session/start", json={"car_id": "bmw-m3"})
        sid = start.get_json()["session_id"]
        resp = client.post(
            f"/api/session/{sid}/gaze",
            json={"x": 100, "y": 200, "relativeX": 0.5, "relativeY": 0.5,
                  "timestamp": 1000},
        )
        assert resp.status_code == 200
        assert resp.get_json()["point_count"] == 1


class TestStopSession:
    def test_unknown_session_returns_404(self, client):
        resp = client.post("/api/session/missing/stop")
        assert resp.status_code == 404

    def test_stops_with_no_gaze_points(self, client):
        # Previously, stopping a session with no points could crash on the
        # timestamp arithmetic. It should now return cleanly with duration 0.
        start = client.post("/api/session/start", json={"car_id": "bmw-m3"})
        sid = start.get_json()["session_id"]
        resp = client.post(f"/api/session/{sid}/stop")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["total_points"] == 0
        assert body["duration_seconds"] == 0


class TestNotFoundHandler:
    def test_unknown_route_returns_json_404(self, client):
        resp = client.get("/api/this-does-not-exist")
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Not found"}


class TestGetCars:
    def test_returns_list_of_cars(self, client):
        resp = client.get("/api/cars")
        assert resp.status_code == 200
        cars = resp.get_json()
        assert isinstance(cars, list)
        assert len(cars) >= 1
        assert all("id" in c and "name" in c and "image" in c for c in cars)
