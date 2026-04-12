import cv2
import mediapipe as mp
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Initialize mediapipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Eye landmark indices
LEFT_EYE = [33, 133]
RIGHT_EYE = [362, 263]

# Store gaze points
gaze_points = []

# Open iPhone camera through macOS (AVFoundation backend)
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

print("Eye tracking started")
print("Press Q to stop and generate heatmap")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera frame not received")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        for face_landmarks in results.multi_face_landmarks:

            # LEFT eye
            lx1 = int(face_landmarks.landmark[LEFT_EYE[0]].x * w)
            ly1 = int(face_landmarks.landmark[LEFT_EYE[0]].y * h)

            lx2 = int(face_landmarks.landmark[LEFT_EYE[1]].x * w)
            ly2 = int(face_landmarks.landmark[LEFT_EYE[1]].y * h)

            # RIGHT eye
            rx1 = int(face_landmarks.landmark[RIGHT_EYE[0]].x * w)
            ry1 = int(face_landmarks.landmark[RIGHT_EYE[0]].y * h)

            rx2 = int(face_landmarks.landmark[RIGHT_EYE[1]].x * w)
            ry2 = int(face_landmarks.landmark[RIGHT_EYE[1]].y * h)

            # Draw eye corners
            cv2.circle(frame, (lx1, ly1), 3, (0,255,0), -1)
            cv2.circle(frame, (lx2, ly2), 3, (0,255,0), -1)
            cv2.circle(frame, (rx1, ry1), 3, (0,255,0), -1)
            cv2.circle(frame, (rx2, ry2), 3, (0,255,0), -1)

            # Estimate gaze position
            gaze_x = int((lx1 + lx2 + rx1 + rx2) / 4)
            gaze_y = int((ly1 + ly2 + ry1 + ry2) / 4)

            gaze_points.append((gaze_x, gaze_y))

            # Draw gaze point
            cv2.circle(frame, (gaze_x, gaze_y), 5, (0,0,255), -1)

    cv2.imshow("Eye Tracking (iPhone Camera)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Generate heatmap
if len(gaze_points) > 0:

    x = [p[0] for p in gaze_points]
    y = [p[1] for p in gaze_points]

    print("Generating consumer attention heatmap...")

    plt.figure(figsize=(6,5))
    sns.kdeplot(x=x, y=y, cmap="Reds", fill=True, thresh=0)

    plt.title("Consumer Attention Heatmap")
    plt.xlabel("Screen X Position")
    plt.ylabel("Screen Y Position")

    plt.show()

else:
    print("No gaze data collected")