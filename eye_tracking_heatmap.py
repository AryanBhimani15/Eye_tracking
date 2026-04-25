"""Standalone webcam eye-tracking heatmap.

Captures gaze points via MediaPipe Face Mesh, then renders and saves a
KDE heatmap when the user presses Q. Cross-platform: picks the right
OpenCV capture backend per OS, with a fallback for headless setups.
"""

import os
import platform
import sys
from datetime import datetime

import cv2
import matplotlib.pyplot as plt
import mediapipe as mp
import seaborn as sns

# Eye landmark indices (MediaPipe Face Mesh)
LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]

OUTPUT_DIR = "output"


def open_camera():
    """Open the system camera using a backend appropriate to the OS."""
    system = platform.system()
    if system == "Darwin":
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    elif system == "Windows":
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        # Linux / RaspberryPi default
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        # Fall back to the default backend in case the OS-specific one fails
        cap = cv2.VideoCapture(0)

    return cap


def estimate_gaze(face_landmarks, frame_w, frame_h):
    """Return the (x, y) pixel midpoint between the four eye corners."""
    coords = []
    for idx in LEFT_EYE + RIGHT_EYE:
        lm = face_landmarks.landmark[idx]
        coords.append((int(lm.x * frame_w), int(lm.y * frame_h)))

    avg_x = sum(c[0] for c in coords) // len(coords)
    avg_y = sum(c[1] for c in coords) // len(coords)
    return avg_x, avg_y, coords


def render_heatmap(gaze_points, frame_size):
    """Render a KDE heatmap from the recorded gaze points and save it to disk."""
    if not gaze_points:
        print("No gaze data collected — skipping heatmap.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"heatmap_{timestamp}.png")

    xs = [p[0] for p in gaze_points]
    ys = [p[1] for p in gaze_points]

    print(f"Generating consumer attention heatmap from {len(gaze_points)} points...")

    plt.figure(figsize=(8, 6))
    sns.kdeplot(x=xs, y=ys, cmap="Reds", fill=True, thresh=0)
    plt.title("Consumer Attention Heatmap")
    plt.xlabel("Screen X Position")
    plt.ylabel("Screen Y Position")
    if frame_size:
        plt.xlim(0, frame_size[0])
        plt.ylim(frame_size[1], 0)  # invert Y so origin matches the camera
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    print(f"Saved heatmap to {output_path}")

    plt.show()


def main():
    cap = open_camera()
    if not cap.isOpened():
        print("Error: Could not open camera. Try `python camera_test.py` first.")
        sys.exit(1)

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    gaze_points = []
    frame_size = None
    frames_without_face = 0

    print("Eye tracking started")
    print("Press Q to stop and generate the heatmap")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Camera frame not received — stopping.")
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            frame_size = (w, h)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if results.multi_face_landmarks:
                frames_without_face = 0
                for face_landmarks in results.multi_face_landmarks:
                    gx, gy, eye_corners = estimate_gaze(face_landmarks, w, h)

                    for ex, ey in eye_corners:
                        cv2.circle(frame, (ex, ey), 3, (0, 255, 0), -1)

                    gaze_points.append((gx, gy))
                    cv2.circle(frame, (gx, gy), 5, (0, 0, 255), -1)
            else:
                frames_without_face += 1
                if frames_without_face % 60 == 0:
                    print("(no face detected — make sure you're in frame)")

            cv2.imshow("Eye Tracking", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        face_mesh.close()

    render_heatmap(gaze_points, frame_size)


if __name__ == "__main__":
    main()
