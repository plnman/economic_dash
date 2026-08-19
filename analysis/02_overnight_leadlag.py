import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT.parent / 'data' / 'dashboard.json'
OUT = ROOT / 'out' / '02_overnight_leadlag.txt'

d = json.load(open(DATA, encoding='utf-8'))
S = d['series']

def ser(k):
    o = S[k]
    idx = pd.to_datetime(np.array(o['t']), unit='s').normalize()
    return pd.Series(o['v'], index=idx, name=k).groupby(level=0).last().sort_index()

out = []

# --- A. 오버나이트 예측력 랭킹: 전일 미국물 -> 당일 한국물 ---
us = ['sox', 'soxx', 'smh', 'mu', 'tsm', 'ewy', 'gspc', 'ixic', 'dxy', 'tnx']
kr = ['samsung', 'hynix', 'hanmi', 'joosung', 'leeno', 'krsemi', 'ks11']
out.append("=== A. 전일 미국 종가 -> 당일 한국 종가 (lag+1 상관, 3년) ===")
out.append(f"{'':9s}" + ''.join(f"{k:>9s}" for k in kr))
best = []
for u in us:
    if u not in S: continue
    su = ser(u).pct_change()
    line = f"{u:9s}"
    for k in kr:
        if k not in S: line += f"{'-':>9s}"; continue
        sk = ser(k).pct_change()
        j = pd.concat([su.shift(1), sk], axis=1, join='inner').dropna()
        j.columns = ['u', 'k']
        c = j['u'].corr(j['k'])
        line += f"{c:>+9.3f}"
        best.append((abs(c), c, u, k, len(j)))
    out.append(line)
best.sort(reverse=True)
out.append("\n상위 8개 (절대값 기준):")
for a, c, u, k, n in best[:8]:
    out.append(f"  {u:8s} -> {k:9s} r={c:+.3f}  R2={c*c*100:4.1f}%  n={n}")

# --- B. 5개 유효 페어의 오늘 상태: 20일 상관 + 퍼센타일 + 20-60 스프레드 ---
VALID = [('wti-rates', 'wti', 'dgs10'), ('breadth-index', 'breadth', 'gspc'),
         ('gold-btc', 'gold', 'btc'), ('ewy-krsemi', 'ewy', 'samsung'),
         ('rate-index', 'tnx', 'gspc')]
out.append("\n=== B. 오늘자 레짐 판정 (20일 기준 + 20-60 스프레드) ===")
out.append(f"{'pair':15s} {'c20':>6s} {'%ile':>5s} {'c60':>6s} {'스프레드':>7s} {'판정':>16s}")
for pid, a, b in VALID:
    j = pd.concat([ser(a), ser(b)], axis=1, join='inner').pct_change().dropna()
    c20 = j[a].rolling(20).corr(j[b]).dropna()
    c60 = j[a].rolling(60).corr(j[b]).dropna()
    now20, now60 = c20.iloc[-1], c60.iloc[-1]
    pct = (c20 < now20).mean() * 100
    med = c20.median()
    spread = now20 - now60
    if pct >= 85: v = '평소보다 강함' if abs(now20) > abs(med) else '평소보다 약함'
    elif pct <= 15: v = '평소보다 약함' if abs(now20) < abs(med) else '평소보다 강함'
    else: v = '정상범위'
    if np.sign(now20) != np.sign(med) and abs(now20) > 0.1: v = '부호반전(디커플링)'
    out.append(f"{pid:15s} {now20:>+6.2f} {pct:>5.0f} {now60:>+6.2f} {spread:>+7.2f} {v:>16s}")

# --- C. 장기: 수출 사이클 (유일한 5년치 시리즈) ---
out.append("\n=== C. 장기용 후보: exports YoY (2021~, 68개월) ===")
ex = ser('exports')
yoy = (ex / ex.shift(12) - 1) * 100
out.append(f"최근 12개월 YoY: " + ', '.join(f"{i.date().strftime('%y-%m')}:{v:+.0f}%" for i, v in yoy.dropna().tail(12).items()))
out.append(f"YoY 범위(5년): 최저 {yoy.min():+.0f}% / 최고 {yoy.max():+.0f}% / 현재 {yoy.dropna().iloc[-1]:+.0f}% "
           f"(백분위 {(yoy.dropna() < yoy.dropna().iloc[-1]).mean()*100:.0f})")

# --- D. 섹터 로테이션 (90포인트 = 상관 불가, 모멘텀은 가능) ---
out.append("\n=== D. 중기용: 섹터 상대모멘텀 (섹터ETF 90포인트) ===")
sec = [s['id'] if isinstance(s, dict) else s for s in d['sectors']]
rows = []
for sid in sec:
    if sid not in S: continue
    s = ser(sid)
    r1 = (s.iloc[-1] / s.iloc[-21] - 1) * 100 if len(s) > 21 else np.nan
    r3 = (s.iloc[-1] / s.iloc[-63] - 1) * 100 if len(s) > 63 else np.nan
    rows.append((r1, r3, sid, S[sid]['name']))
rows.sort(reverse=True)
out.append(f"{'sector':6s} {'1M':>7s} {'3M':>7s}")
for r1, r3, sid, nm in rows:
    out.append(f"{sid:6s} {r1:>+7.1f} {r3:>+7.1f}")

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('done')
