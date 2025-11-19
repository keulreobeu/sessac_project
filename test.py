import cv2
import os
import time
import csv
import glob
import re

# Camera capture with event flag recording (frame saving version)

# Controls:
#     - SPACE : toggle recording start/stop
#     - A     : event flag 1
#     - S     : event flag 2
#     - D     : event flag 3
#     - Q or ESC : exit program (if recording, save and exit)

# Output structure:
#     - video/<SCENARIO_DIR>/<session_folder>/frame_000000.jpg ...
#     - video/<SCENARIO_DIR>/video_<SCENARIO_CODE>_<index>_events.csv

# =========================
# 1. Configurable variables
# =========================

CAMERA_INDEX = 0
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720
FPS          = 30
EXPOSURE     = None

BASE_DIR      = "video"
SCENARIO_DIR  = "normal"
SCENARIO_CODE = "normal"

AUTO_RECORD_SECONDS = None
IMAGE_FORMAT = "jpg"
JPEG_QUALITY = 95
FLAG_DISPLAY_DURATION = 1.0

# =========================
# 2. Utility functions
# =========================

def init_camera():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {CAMERA_INDEX}")

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


def get_next_index(out_dir, scenario_code):
    pattern = os.path.join(out_dir, f"video_{scenario_code}_*")
    paths = glob.glob(pattern)

    indices = []
    for path in paths:
        name = os.path.basename(path)
        m = re.match(rf"video_{re.escape(scenario_code)}_(\d+)", name)
        if m:
            indices.append(int(m.group(1)))

    if not indices:
        return 1
    return max(indices) + 1


def make_session_paths():
    out_dir = get_output_dir()
    index = get_next_index(out_dir, SCENARIO_CODE)
    base_name = f"video_{SCENARIO_CODE}_{index:03d}"
    frames_dir = os.path.join(out_dir, base_name)
    event_path = os.path.join(out_dir, base_name + "_events.csv")
    return frames_dir, event_path


def save_frame(frames_dir, frame_idx, frame):
    fmt = IMAGE_FORMAT.lower()
    if fmt in ("jpg", "jpeg"):
        ext = ".jpg"
        params = [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    elif fmt == "png":
        ext = ".png"
        params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
    else:
        ext = "." + fmt
        params = []

    filename = f"frame_{frame_idx:06d}{ext}"
    path = os.path.join(frames_dir, filename)

    if params:
        cv2.imwrite(path, frame, params)
    else:
        cv2.imwrite(path, frame)


def log_event(events, frame_idx, elapsed_time_sec, key_code):
    if key_code == ord('a'):
        flag_id, flag_key = 1, 'A'
    elif key_code == ord('s'):
        flag_id, flag_key = 2, 'S'
    elif key_code == ord('d'):
        flag_id, flag_key = 3, 'D'
    else:
        return None

    events.append((frame_idx, elapsed_time_sec, flag_id, flag_key))
    return flag_id, flag_key


def save_events_csv(event_path, events):
    if not events:
        return

    with open(event_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_idx", "time_sec", "flag_id", "flag_key"])
        writer.writerows(events)


def draw_overlay(frame, recording, record_start_time,
                 last_flag_text, last_flag_time):
    overlay = frame.copy()

    h, w = overlay.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1
    color_text = (255, 255, 255)

    text1 = f"Scenario: {SCENARIO_DIR} ({SCENARIO_CODE})"
    cv2.putText(overlay, text1, (10, 20), font, scale, color_text, thickness, cv2.LINE_AA)

    text2 = f"Res: {w}x{h} (target {FRAME_WIDTH}x{FRAME_HEIGHT}) @ {FPS}fps"
    cv2.putText(overlay, text2, (10, 40), font, scale, color_text, thickness, cv2.LINE_AA)

    if recording and record_start_time is not None:
        elapsed = time.time() - record_start_time
        color_rec = (0, 0, 255)
        rec_text = f"REC {elapsed:5.1f}s"
        cv2.putText(overlay, rec_text, (10, 60), font, scale, color_rec, thickness + 1, cv2.LINE_AA)

        if AUTO_RECORD_SECONDS is not None:
            remaining = max(0.0, AUTO_RECORD_SECONDS - elapsed)
            auto_text = f"AUTO STOP IN {remaining:5.1f}s"
            cv2.putText(overlay, auto_text, (10, 80), font, scale, color_rec, thickness, cv2.LINE_AA)
    else:
        idle_text = "Press SPACE to start recording"
        cv2.putText(overlay, idle_text, (10, 60), font, scale, color_text, thickness, cv2.LINE_AA)

    now = time.time()
    if last_flag_text and (now - last_flag_time <= FLAG_DISPLAY_DURATION):
        flag_color = (0, 255, 255)
        y_pos = h - 20
        cv2.putText(overlay, f"{last_flag_text} (RECORDED)", (10, y_pos),
                    font, scale, flag_color, thickness + 1, cv2.LINE_AA)

    return overlay

# =========================
# 3. Recording control
# =========================

def start_recording():
    frames_dir, event_path = make_session_paths()
    os.makedirs(frames_dir, exist_ok=True)

    record_start_time = time.time()
    frame_idx = 0
    events = []

    print(f"[INFO] Recording started. Frames: {frames_dir}")
    print(f"[INFO] Event log: {event_path}")
    return frames_dir, event_path, record_start_time, frame_idx, events


def stop_recording(event_path, events):
    save_events_csv(event_path, events)
    print(f"[INFO] Recording stopped. Events saved: {event_path}")

# =========================
# 4. Main loop
# =========================

def main():
    cap = init_camera()

    recording = False
    frames_dir = None
    event_path = None
    record_start_time = None
    frame_idx = 0
    events = []

    last_flag_text = ""
    last_flag_time = 0.0

    print("[INFO] SPACE=start/stop, A/S/D=flags, Q/ESC=quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to read frame. Exiting.")
            break

        display_frame = draw_overlay(frame, recording, record_start_time,
                                     last_flag_text, last_flag_time)
        cv2.imshow("Capture", display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key in (ord('q'), 27):
            if recording:
                stop_recording(event_path, events)
            print("[INFO] Exit requested.")
            break

        if key == 32:
            if not recording:
                (frames_dir,
                 event_path,
                 record_start_time,
                 frame_idx,
                 events) = start_recording()
                recording = True
                last_flag_text = ""
                last_flag
