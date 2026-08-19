import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT.parent / 'data' / 'dashboard.json'
OUT = ROOT / 'out' / '03_correlation_magnitude.txt'

d = json.load(open(DATA, encoding='utf-8'))
S = d['series']

def ser(k):
    o = S[k]
    idx = pd.to_datetime(np.array(o['t']), unit='s').normalize()
    return pd.Series(o['v'], index=idx, name=k).groupby(level=0).last().sort_index()

out = []
out.append("=== 1. 이론 적중률: P(같은 방향) = 1/2 + arcsin(r)/pi ===")
out.append(f"{'r':>6s} {'R2(설명력)':>10s} {'이론 방향적중률':>14s}")
for r in [0.05, 0.1, 0.2, 0.25, 0.3, 0.33, 0.4, 0.46, 0.5, 0.6, 0.7, 0.82, 0.9]:
    p = 0.5 + np.arcsin(r) / np.pi
    out.append(f"{r:>6.2f} {r*r*100:>9.1f}% {p*100:>13.1f}%")

out.append("\n=== 2. 실제 데이터로 검증 (이론 vs 실측 적중률) ===")
tests = [
    ('soxx(전일) -> hynix', 'soxx', 'hynix', 1),
    ('soxx(전일) -> samsung', 'soxx', 'samsung', 1),
    ('ewy(전일) -> samsung', 'ewy', 'samsung', 1),
    ('gold <-> btc (동일일)', 'gold', 'btc', 0),
    ('wti <-> dgs10 (동일일)', 'wti', 'dgs10', 0),
    ('tnx <-> gspc (동일일)', 'tnx', 'gspc', 0),
]
out.append(f"{'관계':26s} {'r':>7s} {'R2':>6s} {'이론적중':>8s} {'실측적중':>8s} {'n':>6s}")
for label, a, b, lag in tests:
    j = pd.concat([ser(a).pct_change().shift(lag), ser(b).pct_change()], axis=1, join='inner').dropna()
    j.columns = ['x', 'y']
    j = j[(j.x != 0) & (j.y != 0)]
    r = j.x.corr(j.y)
    theo = (0.5 + np.arcsin(r) / np.pi) * 100
    emp = (np.sign(j.x) == np.sign(j.y)).mean() * 100
    out.append(f"{label:26s} {r:>+7.3f} {r*r*100:>5.1f}% {theo:>7.1f}% {emp:>7.1f}% {len(j):>6d}")

out.append("\n=== 3. r=0.46이면 실제로 얼마나 움직이나 (soxx 전일 -> hynix 당일) ===")
x = ser('soxx').pct_change().shift(1)
y = ser('hynix').pct_change()
j = pd.concat([x, y], axis=1, join='inner').dropna()
j.columns = ['x', 'y']
r = j.x.corr(j.y)
sx, sy = j.x.std() * 100, j.y.std() * 100
out.append(f"soxx 일변동 표준편차 = {sx:.2f}% / hynix = {sy:.2f}% / r = {r:.3f}")
out.append(f"회귀 기울기 beta = r * (sy/sx) = {r * sy / sx:.3f}  (soxx 1% 움직이면 hynix 평균 {r*sy/sx:.2f}% 예상)")
out.append("")
out.append("soxx 전일 등락률 구간별 -> 당일 hynix 실제 결과:")
bins = [(-99, -3), (-3, -1.5), (-1.5, -0.5), (-0.5, 0.5), (0.5, 1.5), (1.5, 3), (3, 99)]
out.append(f"{'soxx 전일':>14s} {'n':>5s} {'hynix 평균':>10s} {'상승비율':>9s} {'hynix 표준편차':>13s}")
for lo, hi in bins:
    m = j[(j.x * 100 >= lo) & (j.x * 100 < hi)]
    if len(m) < 5: continue
    lbl = f"{lo:+.1f}~{hi:+.1f}%" if abs(lo) < 90 and abs(hi) < 90 else (f"{hi:+.0f}% 미만" if abs(lo) > 90 else f"{lo:+.0f}% 초과")
    out.append(f"{lbl:>14s} {len(m):>5d} {m.y.mean()*100:>+9.2f}% {(m.y>0).mean()*100:>8.0f}% {m.y.std()*100:>12.2f}%")

out.append("\n=== 4. 참고: 같은 자산군끼리는 상관이 얼마나 높나 (비교 기준) ===")
for a, b in [('gspc', 'ixic'), ('gspc', 'dji'), ('sox', 'soxx'), ('samsung', 'hynix'), ('gold', 'copper')]:
    j = pd.concat([ser(a).pct_change(), ser(b).pct_change()], axis=1, join='inner').dropna()
    j.columns = ['x', 'y']
    out.append(f"  {a:8s} <-> {b:8s} r = {j.x.corr(j.y):+.3f}")

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('done')
