.PHONY: install run prod test heatmap clean help

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help:
	@echo "Available targets:"
	@echo "  install   Install web-app dependencies (Flask, gunicorn)"
	@echo "  install-cv Install OpenCV/MediaPipe deps for the standalone script"
	@echo "  run       Start the Flask dev server on http://localhost:5000"
	@echo "  prod      Start gunicorn the way Render runs the app"
	@echo "  test      Run the pytest suite"
	@echo "  heatmap   Run the standalone webcam heatmap script"
	@echo "  clean     Remove build artifacts and cached pyc files"

install:
	$(PIP) install -r requirements.txt

install-cv:
	$(PIP) install opencv-python mediapipe numpy matplotlib seaborn

run:
	$(PYTHON) app.py

prod:
	gunicorn app:app

test:
	$(PYTHON) -m pytest tests/ -v

heatmap:
	$(PYTHON) eye_tracking_heatmap.py

clean:
	rm -rf __pycache__ tests/__pycache__ .pytest_cache build dist *.egg-info
	find . -type f -name "*.pyc" -delete
