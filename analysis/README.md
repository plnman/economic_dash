# 검증 스크립트

`dashboard-redesign-spec.md` 섹션 0.5의 실측값을 생성한 코드. 결과는 `out/`에 텍스트로 커밋되어 있어 실행 없이도 읽을 수 있다.

## 실행

데이터는 용량 때문에 커밋하지 않는다(`.gitignore`). 먼저 받아야 한다.

```bash
mkdir -p data
curl -o data/dashboard.json https://brevislab.com/assets/data/dashboard.json
python analysis/01_pair_validity.py
```

필요 패키지: `pandas`, `numpy`

## 스크립트

| 파일 | 내용 |
|---|---|
| `01_pair_validity.py` | 12개 페어 롤링 상관 전수 계산, 유효표본 진단, 시차 검증 |
| `02_overnight_leadlag.py` | 전일 미국 → 당일 한국 예측력 70조합, 오늘자 레짐 판정, 수출 YoY, 섹터 모멘텀 |
| `03_correlation_magnitude.py` | 상관계수 크기 해석 (R², 방향 적중률 이론 vs 실측, 구간별 반응) |
| `04_scope_count.py` | `rightOptions` 전개 후 31조합 분류, 최종 스코프 집계 |

## 주의

상관계수는 **레벨이 아닌 일별 등락률**로 계산한다. 레벨로 내면 양쪽 다 우상향 추세라 가짜 상관이 잡힌다.
