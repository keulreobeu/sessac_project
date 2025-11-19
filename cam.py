import cv2

def find_cameras(max_index=5):
    available = []
    for i in range(max_index + 1):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Windows면 CAP_DSHOW 추천
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Camera index {i}: OK")
                available.append(i)
            cap.release()
    return available

if __name__ == "__main__":
    cams = find_cameras(5)
    print("Available cameras:", cams)
