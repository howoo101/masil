"""남양주 마실 · AI 보호자 페르소나 설문 시뮬레이션 (규칙 기반, 실제 응답 아님)

- 페르소나 40명: 아래 DIST의 인원수를 그대로 나눠 만든다(무작위 섞기만 seed로 고정).
- 11문항: 각 문항은 페르소나 속성에 따른 '규칙'으로 응답 확률을 정하고, seed를 고정한 난수로 하나를 고른다.
- 같은 seed면 언제 돌려도 같은 결과가 나온다:  python3 simulate.py
결과는 '이런 사람들이라면 이렇게 답할 가능성이 높다'는 팀의 가정을 숫자로 옮긴 것이며, 실제 조사로 확인해야 한다.
"""
import json, random
SEED = 20261121
rng = random.Random(SEED)

# ── 대상자 분포 (40명) ──
DIST = {
    '나이대': {'30대': 10, '40대': 18, '50대': 12},
    '자녀 거주지': {'남양주 신도시(다산·별내)': 16, '서울': 14, '그 밖의 경기': 10},
    '부모님 거주지': {'읍·면(수동·조안·화도 등)': 26, '남양주 동 지역': 14},
    '부모님 가구': {'혼자 사심': 24, '부부 함께': 16},
    '안부 연락': {'매일': 8, '주 2~3회': 17, '주 1회 이하': 15},
    '부모님 복약': {'매일 약 드심': 28, '아님': 12},
}
def build():
    cols = {}
    for k, d in DIST.items():
        v = [a for a, n in d.items() for _ in range(n)]; assert len(v) == 40, k
        rng.shuffle(v); cols[k] = v
    return [{k: cols[k][i] for k in DIST} | {'id': i + 1} for i in range(40)]

def pick(weights):
    items = list(weights.items()); r = rng.random() * sum(w for _, w in items)
    for a, w in items:
        r -= w
        if r <= 0: return a
    return items[-1][0]

# ── 11문항과 응답 규칙 ──
def answer(p):
    far = p['자녀 거주지'] != '남양주 신도시(다산·별내)'
    rare = p['안부 연락'] == '주 1회 이하'
    alone = p['부모님 가구'] == '혼자 사심'
    rural = p['부모님 거주지'].startswith('읍·면')
    a = {}
    a['Q1 부모님 변화를 늦게 안 적이 있다'] = pick({'예': 0.55 + 0.2 * rare + 0.1 * far + 0.05 * alone, '아니오': 0.3})
    a['Q2 더 원하는 정보'] = pick({'평소와 달라진 점': 0.85 + 0.05 * rare, '실시간 위치': 0.1 + 0.1 * (p['나이대'] == '30대')})
    a['Q3 가장 알고 싶은 것'] = pick({'식사': 0.35, '복약': 0.15 + 0.25 * (p['부모님 복약'] == '매일 약 드심'), '외출·걸음': 0.25 + 0.1 * rural, '기분·대화': 0.15})
    a['Q4 부모님이 직접 체크하실 수 있다'] = pick({'예': 0.45 - 0.1 * (p['나이대'] == '50대'), '처음엔 도움 필요': 0.4, '어렵다': 0.15})
    a['Q5 가장 큰 걱정'] = pick({'부모님 동의·감시 느낌': 0.38 + 0.1 * alone, '개인정보': 0.25, '부모님이 귀찮아함': 0.22, '비용': 0.12})
    a['Q6 알림을 받으면 먼저'] = pick({'바로 전화': 0.5 + 0.1 * far, '주말에 방문': 0.25 + 0.15 * (not far), '며칠 지켜봄': 0.15})
    a['Q7 원하는 리포트 주기'] = pick({'매일 한 줄': 0.35, '주 1회 정리': 0.35, '달라질 때만': 0.3})
    a['Q8 보건소 등 기관 연결을 원한다'] = pick({'예': 0.55 + 0.15 * rural + 0.1 * alone, '아니오': 0.35})
    a['Q9 월 이용료'] = pick({'무료만': 0.2, '5천 원 미만': 0.25, '5천~9,900원': 0.3 + 0.1 * (p['나이대'] != '30대'), '9,900원 이상': 0.15 + 0.1 * far})
    a['Q10 형제와 함께 보고 싶다'] = pick({'예': 0.6, '아니오': 0.4})
    a['Q11 부모님 사진·편지를 받고 싶다'] = pick({'예': 0.65 + 0.1 * rare, '아니오': 0.3})
    return a

def main():
    people = build(); rows = []
    for p in people: rows.append(p | answer(p))
    qs = [k for k in rows[0] if k.startswith('Q')]
    summary = {q: {} for q in qs}
    for r in rows:
        for q in qs: summary[q][r[q]] = summary[q].get(r[q], 0) + 1
    out = {'seed': SEED, 'n': 40, 'distribution': DIST,
           'results': {q: {a: {'n': n, 'pct': round(n / 40 * 100)} for a, n in sorted(c.items(), key=lambda x: -x[1])} for q, c in summary.items()},
           'personas': rows}
    json.dump(out, open(__file__.replace('simulate.py', 'results.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for q, c in out['results'].items(): print(q, ' / '.join(f'{a} {v["pct"]}%' for a, v in c.items()))
if __name__ == '__main__': main()
