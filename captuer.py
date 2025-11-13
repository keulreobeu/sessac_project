import cv2

CAM_INDEX = 0  # 실제 사용하는 인덱스로 수정

cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("카메라를 열 수 없습니다.")

# 1) 자동 노출 끄기
#   DirectShow 쪽에서는 0.25가 수동, 0.75가 자동인 경우가 많음
# cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 수동 모드 시도

# 2) 노출(셔터) 값 설정
#   C270은 보통 -13 ~ -1 사이 값이 들어가고,
#   숫자가 더 작을수록(예: -13) 셔터가 짧아져서 어두워집니다.
cap.set(cv2.CAP_PROP_EXPOSURE, -9)  # 중간 정도 값, 직접 바꿔보면서 조정

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
