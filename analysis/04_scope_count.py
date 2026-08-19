import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT.parent / 'data' / 'dashboard.json'
OUT = ROOT / 'out' / '04_scope_count.txt'

d = json.load(open(DATA, encoding='utf-8'))
S = d['series']

def ser(k):
    o = S[k]
    idx = pd.to_datetime(np.array(o['t']), unit='s').normalize()
    return pd.Series(o['v'], index=idx, name=k).groupby(level=0).last().sort_index()

# 유효성 판정: 정렬 후 표본수로 20일 롤링 퍼센타일이 가능한가
def verdict(a, b):
    try:
        j = pd.concat([ser(a), ser(b)], axis=1, join='inner').pct_change().dropna()
    except Exception:
        return 'ERR', 0, np.nan, np.nan
    n = len(j)
    if n < 200:
        return '표본부족', n, np.nan, np.nan
    c20 = j[a].rolling(20).corr(j[b]).dropna()
    c60 = j[a].rolling(60).corr(j[b]).dropna()
    if len(c60) < 60:
        return '표본부족', n, np.nan, np.nan
    flip = (np.sign(c60) != np.sign(c60.median())).mean() * 100
    full = j[a].corr(j[b])
    if flip >= 35:
        return '불안정', n, c20.iloc[-1], flip
    return '유효', n, c20.iloc[-1], flip

out = []
out.append("=== 1. 기존 12개 카드를 rightOptions까지 전개한 실제 조합 수 ===")
combos = []
for p in d['pairs']:
    left = p['left']
    opts = p.get('rightOptions')
    rights = [o[0] for o in opts] if opts else [p['right']]
    for r in rights:
        combos.append((p['id'], left, r))
    out.append(f"  {p['id']:16s} left={left:8s} 우측 선택지 {len(rights)}개 -> 조합 {len(rights)}")
out.append(f"\n  카드 12개 -> 실제 상관 조합 총 {len(combos)}개")

out.append("\n=== 2. 조합별 유효성 판정 ===")
out.append(f"{'card':16s} {'조합':22s} {'n':>5s} {'c20':>6s} {'flip%':>6s} {'판정':>8s}")
tally = {}
for pid, a, b in combos:
    v, n, c20, flip = verdict(a, b)
    tally[v] = tally.get(v, 0) + 1
    c20s = f"{c20:+.2f}" if not (isinstance(c20, float) and np.isnan(c20)) else "  -"
    flips = f"{flip:.0f}" if not (isinstance(flip, float) and np.isnan(flip)) else " -"
    out.append(f"{pid:16s} {a+'->'+b:22s} {n:5d} {c20s:>6s} {flips:>6s} {v:>8s}")
out.append("\n  집계: " + ', '.join(f"{k} {v}개" for k, v in sorted(tally.items())))

out.append("\n=== 3. lead-lag(전일 미국 -> 당일 한국) 후보 매트릭스 ===")
us = ['sox', 'soxx', 'smh', 'mu', 'tsm', 'ewy', 'gspc', 'ixic', 'dxy', 'tnx']
kr = ['samsung', 'hynix', 'hanmi', 'joosung', 'leeno', 'krsemi', 'ks11']
us = [u for u in us if u in S]; kr = [k for k in kr if k in S]
out.append(f"  미국 {len(us)}종 x 한국 {len(kr)}종 = {len(us)*len(kr)}개 검증 대상")
res = []
for u in us:
    su = ser(u).pct_change().shift(1)
    for k in kr:
        j = pd.concat([su, ser(k).pct_change()], axis=1, join='inner').dropna()
        j.columns = ['x', 'y']
        res.append((abs(j.x.corr(j.y)), u, k, j.x.corr(j.y)))
res.sort(reverse=True)
strong = [x for x in res if x[0] >= 0.30]
out.append(f"  이 중 |r|>=0.30 (실전 의미 있는 수준) = {len(strong)}개")
out.append(f"  이 중 |r|>=0.40 = {len([x for x in res if x[0] >= 0.40])}개")

out.append("\n=== 4. 최종 스코프 집계 ===")
valid_combos = [c for c in combos if verdict(c[1], c[2])[0] == '유효']
out.append(f"  A. 기존 카드 유효 조합        : {len(valid_combos)}개")
out.append(f"  B. lead-lag 유효(|r|>=0.40)   : {len([x for x in res if x[0] >= 0.40])}개")
out.append(f"  C. 섹터 모멘텀(상관 아님)     : {len(d['sectors'])}개")
out.append(f"  D. 밸류체인(상관 아님)        : {len(d['valuechain'])}개")
out.append(f"\n  => 상관계수를 실제 계산해야 하는 것: A {len(valid_combos)} + B {len([x for x in res if x[0]>=0.40])} = {len(valid_combos)+len([x for x in res if x[0]>=0.40])}개")
out.append(f"  => 창 3개(20/60/120) 적용 시 시계열: {(len(valid_combos)+len([x for x in res if x[0]>=0.40]))*3}개")

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('done')
