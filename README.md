# Level2-nlp-datacentric-project

## 0. Workflow
![image_work_flow](https://github.com/user-attachments/assets/0f130239-cf61-4fce-8ffc-959f7c2ce12c)

## 1. 파일구성
```
level2-nlp-datacentric-nlp-01/
├── src/
│   ├── config.py                # 경로 및 설정 상수
│   ├── dataset.py               # 데이터셋 클래스 정의
│   ├── model.py                 # 모델 로드 및 초기화
│   ├── train.py                 # 훈련 스크립트
│   ├── evaluate.py              # 테스트 데이터 예측 스크립트
│   └── utils.py                 # 보조 함수 및 메트릭 계산 함수
├── data/
│   ├── train.csv                # 학습 데이터 (직접 넣을 것)
│   └── test.csv                 # 테스트 데이터 (직접 넣을 것)
└── main.py                      # 메인 실행 파일

```

## 2. 실행방법

CLI 창에서
`python main.py`
라고 치면 훈련 및 평가(output.csv 저장)까지 자동으로 진행됩니다.
