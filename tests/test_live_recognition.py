import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Initialize InsightFace detector + embedder
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera not detected!")
    exit()

print("Camera OK. Starting real-time test... Press Q to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame.")
        break

    # Run detector + embedder
    faces = app.get(frame)

    # Draw boxes
    for face in faces:
        box = face.bbox.astype(int)
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.putText(frame, "Detected", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Live Recognition Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
