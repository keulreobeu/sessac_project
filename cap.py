import cv2
import os
import glob
import re
import time

# =========================
# 1. 카메라 설정
# =========================
CAMERA_INDEX = 0
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720
FPS          = 30
EXPOSURE     = -9   # 장비에 따라 적용되지 않을 수 있음

# =========================
# 2. 저장 설정
# =========================
BASE_DIR      = "photo"     # 사진 저장 최상위 폴더
SCENARIO_DIR  = "normal"    # 하위 폴더
SCENARIO_CODE = "normal"    # 파일 이름에 사용할 코드


# =========================
# 3. 유틸 함수
# =========================

def init_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          FPS)

    if EXPOSURE is not None:
        cap.set(cv2.CAP_PROP_EXPOSURE, EXPOSURE)

    return cap


def get_output_dir():
    out_dir = os.path.join(BASE_DIR, SCENARIO_DIR)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def get_next_index(out_dir):
    """
    photo_<code>_<번호>.jpg 의 번호 자동 증가
    """
    pattern = os.path.join(out_dir, f"photo_{SCENARIO_CODE}_*.jpg")
    paths = glob.glob(pattern)

    indices = []
    for path in paths:
        name = os.path.basename(path)
        m = re.match(rf"photo_{re.escape(SCENARIO_CODE)}_(\d+)\.jpg", name)
        if m:
            indices.append(int(m.group(1)))

    return max(indices) + 1 if indices else 1


def save_photo(frame):
    out_dir = get_output_dir()
    idx = get_next_index(out_dir)
    filename = os.path.join(out_dir, f"photo_{SCENARIO_CODE}_{idx:03d}.jpg")
    cv2.imwrite(filename, frame)
    print(f"[INFO] Saved photo → {filename}")


# =========================
# 4. 메인 루프
# =========================

def main():
    cap = init_camera()
    print("[INFO] Press SPACE to capture a photo. Press Q or ESC to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to read frame.")
            break

        cv2.imshow("Camera - Press SPACE to Capture", frame)
        key = cv2.waitKey(1) & 0xFF

        # 종료
        if key in (ord('q'), 27):
            print("[INFO] Exit requested.")
            break

        # 사진 촬영
        if key == 32:  # Space
            save_photo(frame)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
