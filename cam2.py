import cv2

# 0번 카메라 열기 (대부분 노트북/첫 번째 USB 카메라가 0번)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Windows면 CAP_DSHOW 추천

if not cap.isOpened():
    print("❌ 카메라를 열 수 없습니다. 인덱스를 확인하세요.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ 프레임을 받아오지 못했습니다.")
        break

    # 화면에 출력
    cv2.imshow("Camera", frame)

    # q 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
