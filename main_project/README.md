# GNP 문서 자동화(가제)
-   프로젝트 플로우를 정리
##  1. 학습 데이터 수집
-   구성 환경
    -   웹캡 또는 USB 카메라 사용
    -   720P HD이미지
    -   30fps를 목표로 수집하였지만 수집 환경의 문제로 7.5fps로 수집됨
    -   OpenCV기반 이미지 촬영 진행
-   촬영 스크립트 기능
    -   SPACE: 녹화 시작 및 종료
    -   A/S/D: 이벤트 플래그 기록
    -   Q/ESC: 종료
-   녹화 파일 구조
```
data
└── video/
    ├── normal/
    │   ├── video_normal_001/
    │   │   ├── frame_000000.jpg
    │   │   ├── frame_000001.jpg
    │   │   ├── frame_000002.jpg
    │   │   └── ...
    │   ├── video_normal_001_events.csv
    │   ├── video_normal_002/
    │   │   ├── frame_000000.jpg
    │   │   ├── frame_000001.jpg
    │   │   └── ...
    │   ├── video_normal_002_events.csv
    │   └── ...
    │
    ├── missing1/
    │   ├── video_missing1_A_001/
    │   │   ├── frame_000000.jpg
    │   │   ├── frame_000001.jpg
    │   │   └── ...
    │   ├── video_missing1_A_001_events.csv
    │   ├── video_missing1_B_001/
    │   │   ├── frame_000000.jpg
    │   │   └── ...
    │   ├── video_missing1_B_001_events.csv
    │   └── ...
    │
    ├── missing2/
    │   ├── video_missing2_A_001/
    │   │   ├── frame_000000.jpg
    │   │   ├── frame_000001.jpg
    │   │   └── ...
    │   ├── video_missing2_A_001_events.csv
    │   ├── video_missing2_C_001/
    │   │   ├── frame_000000.jpg
    │   │   └── ...
    │   ├── video_missing2_C_001_events.csv
    │   └── ...
    │
    └── idle/
        ├── video_idle_001/
        │   ├── frame_000000.jpg
        │   ├── frame_000001.jpg
        │   └── ...
        ├── video_idle_001_events.csv
        └── ...
```
##  2. 데이터 전처리
-   데이터 가공 process
    0.  영상 -> 프레임 변환
    1.  이벤트 플래그 -> 프레임 라벨로 변환
        -   이벤트 플래그를 학습 가능한 프레임별 라벨링으로 변환함
        -   이벤트 플래그로 학습시 데이터 불균형으로 인한 학습의 어려움이 발생.
    2.  랜드마크 추출(MediaPipe 사용)
        -   google의 MediaPipe를 이용하여 손의 각 관절부의 랜드마크를 추출하여 저장함.
    3.  Dataset 구성
        -   촬영시 10회를 묶음으로 촬영을 진행하여 학습시에 세트 단위를 유지하며 분할 할 수 있도록 함.

##  3. 모델 학습
1.  행동 탐지
    -   사용한 모델
        -   MLP + Temporal Average Pooling 
            -   프레임 단위 특징(랜드마크)을 평균을 구하여 하나의 고정 길이 벡터로 만든 뒤
            -   MLP(다층 퍼셉트론)으로 분류하는 단순 구조
            -   시간 정보가 사라지기 때문에 시계열 데이터 학습이 적절한지 비교용 모델
        -   1D CNN(Temporal Convolution)
            -   시간축을 따라 슬라이딩 커널(CN)로 패턴을 학습하는 모델
            -   short-term 패턴(0.1~0.5초) 탐지에 강함
            -   멀리 떨어진 프레임간 의존성을 잘 잡지 못함 
        -   BiLSTM
            -   LSTM을 앞 -> 뒤, 뒤-> 앞  두 방향으로 학습
            -   시간 순서 기반의 long-term dependency를 학습
            -   프레임 간 의미적 흐름을 파악함
            -   앞뒤 문맥을 모두 보며 학습을 함.
        -   TCN(Temporal Convolutional Network)
            -   Dilated Conv(팽장 합성곱)을 사용하여 긴 시간 의존성을 CNN 방식으로 학습
            -   BiLSTM과 달리 병렬화가 가능하여 성능이 좋음
    -   최종적으로 TCN 모델을 선택하여 학습을 진행함.

2.  객체 탐지
    -   Yolov8을 통한 객체탐지
        -   기능
            -   박스 개수 감지
            -   열린/닫힌 박스 수 감지
            -   물건 있음/없음 감지
            -   프레임 단위 로그 생성

##  4. 예측 및 후처리
-   각각의 단일 모델로 예측을 할 경우 정확한 값을 얻을 수 없음
    -   TCN 행동 탐지 모델: 전반적으로 행동 위치는 맞으나, 
                            각 행동 구간별 끊기는 지점 + 오탐으로 인한 노이즈 등 파편화 된 데이터가 형성되어 있음
    -   Yolo 객체 탐지 모델: 객체가 정상적으로 보인다는 가정 하에 압도적인 정확도를 보이나,
                            손, 장해물 등 객체 탐지가 안되는 상황 + 다른 객체 오탐 등으로 인해 안정적인 구간 예측이 힘듬

-   위의 두 모델의 단점을 서로 보완하여 예측 알고리즘을 구성
-   예측 알고리즘 간략 설명
    1.  TCN 결과와 YOLO 결과를 프레임 단위로 합친 후
    2.  TCN 에서 나온 이벤트 구간을 노이즈 보정 후 파악
    3.  각 구간 안에서 시작 지점과 끝 지점을 yolo 객체탐지 데이터를 통하여 구함
    4.  이벤트 플레그 작성 완료

##  5. 평가
-   Yolo: 각 validation 별 mAP 계산
### Open/Close 모델

| Metric | Value |
|-------|-------|
| **mAP50-95** | **0.8130** |
| **mAP50** | **0.9950** |
| **mAP75** | **0.9243** |
| **Per-class mAP50** | [0.81285, 0.81316] |



### Full/Empty 모델

| Metric | Value |
|-------|-------|
| **mAP50-95** | **0.8187** |
| **mAP50** | **0.9950** |
| **mAP75** | **0.9410** |
| **Per-class mAP50** | [0.85850, 0.77881] |



-   TCN: K-fold 결과를 통하여 모델 선택 후 test 데이터를 통하여 검증 밎 평가
### 📌 TCN 행동 분류 모델 성능

| Metric | Value |
|--------|--------|
| **전체 F1 (all f1)** | **0.765** |
| **전체 Accuracy (all acc)** | **0.755** |
| **A-class F1** | **0.627** |
| **S-class F1** | **0.879** |
| **D-class F1** | **0.744** |