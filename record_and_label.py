import cv2
import time
import numpy as np
import json


def main():
    # === 설정 ===
    cam_index = 0          # 카메라 번호 (노트북 기본 웹캠이면 보통 0)
    fps = 60               # 라벨 계산용으로만 쓸 예정
    duration = 30.0        # 녹화 시간(초)
    width, height = 1280, 720  # 720p

    # === 카메라 열기 ===
    # Windows면 CAP_DSHOW를 쓰는 게 초기 딜레이 줄이는 데 도움이 될 수 있음
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        return

    # 해상도 / FPS 설정 (카메라에 따라 완벽히 적용 안 될 수도 있음)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # cap.set(cv2.CAP_PROP_FPS, fps)  # 필요하면 사용, 일단은 기본 값 사용

    # === 노출(셔터 속도) 설정 ===
    # print("[INFO] 초기 노출값:", cap.get(cv2.CAP_PROP_EXPOSURE))

    # 1) 자동 노출 끄기 (카메라/드라이버마다 다르게 동작할 수 있음)
    #    안 먹는 카메라도 많으니, 일단 시도해보고 값이 안 바뀌면
    #    제조사 유틸(로지텍 G HUB 등)에서 수동 노출 설정해야 할 수도 있음
    # try:
    #     cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # 일부 백엔드에서 "수동" 모드 의미
    # except Exception:
    #     pass

    # 2) 수동 노출값 설정 (값의 스케일은 장치별로 다름)
    # cap.set(cv2.CAP_PROP_EXPOSURE, -9)
    # print("[INFO] 설정 후 노출값:", cap.get(cv2.CAP_PROP_EXPOSURE))

    # === 비디오 저장 설정 ===
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 안 되면 'XVID' + .avi 로 변경
    out = cv2.VideoWriter(
        'sample_720p_15fps.mp4',
        fourcc,
        fps,              # 파일에 기록할 nominal fps (라벨이랑만 맞으면 됨)
        (width, height)
    )

    # === 라벨링 관련 변수 ===
    intervals = []         # [(start_s, end_s), ...]
    labeling = False       # A키로 ON/OFF 할 상태
    label_start_t = None

    # === 시간 / 프레임 카운트 ===
    start_time = time.time()
    frame_idx = 0

    print("[INFO] 녹화를 시작합니다. A: 라벨 ON/OFF, Q 또는 ESC: 종료")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("카메라에서 프레임을 읽지 못했습니다. 종료합니다.")
            break

        elapsed = time.time() - start_time

        # 30초 지나면 종료
        if elapsed >= duration:
            break

        # 비디오 파일로 저장
        out.write(frame)

        # 화면에 현재 상태 표시
        status_text = f"t={elapsed:5.2f}s  Label={'ON' if labeling else 'OFF'}"
        color = (0, 0, 255) if labeling else (0, 255, 0)
        cv2.putText(frame, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.imshow("Recording (A: label, Q: quit)", frame)

        key = cv2.waitKey(1) & 0xFF

        if key in (ord('a'), ord('A')):
            if not labeling:
                labeling = True
                label_start_t = elapsed
                print(f"[LABEL] ON at {label_start_t:.2f}s")
            else:
                labeling = False
                label_end_t = elapsed
                intervals.append((label_start_t, label_end_t))
                print(f"[LABEL] OFF at {label_end_t:.2f}s  → ({label_start_t:.2f}, {label_end_t:.2f})")
                label_start_t = None

        elif key in (ord('q'), 27):
            print("[INFO] 사용자에 의해 조기 종료.")
            break

        frame_idx += 1

    final_elapsed = time.time() - start_time
    if labeling and label_start_t is not None:
        label_end_t = min(final_elapsed, duration)
        intervals.append((label_start_t, label_end_t))
        print(f"[LABEL] 자동 OFF at {label_end_t:.2f}s  → ({label_start_t:.2f}, {label_end_t:.2f})")

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print("[INFO] 녹화 종료.")
    print("[INFO] 라벨링 구간(초 단위):")
    for st, en in intervals:
        print(f"  ({st:.2f}, {en:.2f})")

    n_frames = frame_idx
    labels = np.zeros(n_frames, dtype=np.int32)

    for (st, en) in intervals:
        st_idx = int(st * fps)
        en_idx = int(en * fps)
        st_idx = max(0, min(st_idx, n_frames))
        en_idx = max(0, min(en_idx, n_frames))
        labels[st_idx:en_idx] = 1

    np.save("labels.npy", labels)
    with open("intervals.json", "w", encoding="utf-8") as f:
        json.dump(intervals, f, ensure_ascii=False, indent=2)

    print(f"[INFO] 총 프레임 수: {n_frames}")
    print("[INFO] intervals.json, labels.npy, sample_720p_15fps.mp4 저장 완료.")


if __name__ == "__main__":
    main()
