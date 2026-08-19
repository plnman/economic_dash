import json, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT.parent / 'data' / 'dashboard.json'
OUT = ROOT / 'out' / '01_pair_validity.txt'

d = json.load(open(DATA, encoding='utf-8'))
S = d['series']

def ser(k):
    o = S[k]
    idx = pd.to_datetime(np.array(o['t']), unit='s').normalize()
    return pd.Series(o['v'], index=idx, name=k).groupby(level=0).last().sort_index()

def freq_of(s):
    gaps = np.diff(s.index.values).astype('timedelta64[D]').astype(int)
    med = int(np.median(gaps)) if len(gaps) else 0
    return {1: 'daily', 2: 'daily', 3: 'daily', 7: 'weekly'}.get(med, 'monthly' if 25 <= med <= 35 else f'{med}d')

PAIRS = [p['id'] for p in d['pairs']]
PMAP = {p['id']: (p['left'], p['right'], p['label']) for p in d['pairs']}

out = []
out.append("=== 1. 시리즈 기간/빈도 (12개 페어 구성 시리즈) ===")
used = sorted({x for p in d['pairs'] for x in (p['left'], p['right'])})
for k in used:
    s = ser(k)
    out.append(f"{k:9s} n={len(s):5d} {s.index[0].date()}~{s.index[-1].date()} freq={freq_of(s):8s} unit={S[k]['unit']}")

out.append("\n=== 2. 페어별 정렬 후 표본수 + 롤링상관 실측 ===")
out.append(f"{'pair':16s} {'freq':8s} {'n_align':>7s} {'20':>7s} {'60':>7s} {'120':>7s} {'sd60':>6s} {'flip%':>6s}")
rows = {}
for pid in PAIRS:
    a, b, label = PMAP[pid]
    sa, sb = ser(a), ser(b)
    fa, fb = freq_of(sa), freq_of(sb)
    # 저빈도 쪽에 맞춰 정렬: 공통 인덱스 inner join (저빈도 날짜에 고빈도 값을 asof 매칭)
    lo, hi = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    j = pd.merge_asof(lo.to_frame('lo').reset_index().rename(columns={'index': 'dt'}),
                      hi.to_frame('hi').reset_index().rename(columns={'index': 'dt'}),
                      on='dt', direction='nearest', tolerance=pd.Timedelta('3D')).dropna().set_index('dt')
    r = j.pct_change().dropna()
    n = len(r)
    res = {}
    for w in (20, 60, 120):
        if n >= w + 10:
            c = r['lo'].rolling(w).corr(r['hi']).dropna()
            res[w] = c
        else:
            res[w] = pd.Series(dtype=float)
    c60 = res[60]
    sd60 = c60.std() if len(c60) else np.nan
    flip = (np.sign(c60) != np.sign(c60.median())).mean() * 100 if len(c60) else np.nan
    fmt = lambda c: f"{c.iloc[-1]:+.2f}" if len(c) else "  n/a"
    freq = f"{fa[0]}/{fb[0]}"
    out.append(f"{pid:16s} {freq:8s} {n:7d} {fmt(res[20]):>7s} {fmt(res[60]):>7s} {fmt(res[120]):>7s} "
               f"{sd60:6.2f}" if not np.isnan(sd60) else
               f"{pid:16s} {freq:8s} {n:7d} {fmt(res[20]):>7s} {fmt(res[60]):>7s} {fmt(res[120]):>7s}   n/a")
    if not np.isnan(sd60):
        out[-1] += f" {flip:5.0f}%"
    rows[pid] = (n, res, sd60, flip)

out.append("\n※ sd60 = 60일 롤링상관의 표준편차(클수록 불안정) / flip% = 부호가 중앙값과 반대인 기간 비율")

out.append("\n=== 3. 유효표본 문제 (퍼센타일 판정의 근거 강도) ===")
out.append(f"{'pair':16s} {'w':>4s} {'롤링값수':>7s} {'독립표본≈':>8s} {'판정':>10s}")
for pid in PAIRS:
    n, res, _, _ = rows[pid]
    for w in (20, 60, 120):
        c = res[w]
        if len(c) == 0:
            out.append(f"{pid:16s} {w:4d} {'-':>7s} {'-':>8s} {'계산불가':>10s}")
            continue
        eff = len(c) / w
        verdict = '충분' if eff >= 20 else ('빈약' if eff >= 8 else '근거없음')
        out.append(f"{pid:16s} {w:4d} {len(c):7d} {eff:8.1f} {verdict:>10s}")

out.append("\n=== 4. 시차(lead-lag) 검증: 정말 선행하는가 ===")
for pid, la, lb in [('ewy-krsemi', 'ewy', 'samsung'), ('dollar-kospi', 'dxy', 'ks11'), ('rate-index', 'tnx', 'gspc')]:
    sa, sb = ser(la), ser(lb)
    j = pd.concat([sa, sb], axis=1, join='inner').pct_change().dropna()
    line = f"{pid:14s} ({la}->{lb}) "
    for lag in (-2, -1, 0, 1, 2):
        c = j[la].shift(lag).corr(j[lb])
        line += f"lag{lag:+d}={c:+.3f}  "
    out.append(line)
out.append("※ lag+1 = 왼쪽 시리즈가 하루 선행(어제 EWY -> 오늘 삼성전자)")

open(OUT, 'w', encoding='utf-8').write('\n'.join(out))
print('done', len(out), 'lines')
