import cv2

CAM_INDEX = 0  
cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError(".")


cap.set(cv2.CAP_PROP_EXPOSURE, -9)  

print("AUTO_EXPOSURE:", cap.get(cv2.CAP_PROP_AUTO_EXPOSURE))
print("EXPOSURE:", cap.get(cv2.CAP_PROP_EXPOSURE))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("C270 Exposure Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
