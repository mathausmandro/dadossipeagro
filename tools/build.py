# Gera dados.json e o app HTML a partir do CSV do SIPEAGRO (fertilizantes).
# Uso: python3 -I build.py <pasta_base>
import csv, json, sys, os, datetime
base = sys.argv[1]
src = os.path.join(base, 'dados', 'sipeagrofertilizante.csv')
seenp = os.path.join(base, 'dados', 'primeira_vez_visto.json')
today = datetime.date.today().isoformat()
rows = list(csv.reader(open(src, encoding='utf-8-sig', newline=''), delimiter=';'))[1:]
seen = json.load(open(seenp)) if os.path.exists(seenp) else None
first_run = seen is None
seen = seen or {}
mun, at, cl, est = {}, {}, {}, {}
def idx(d, k):
    if k not in d: d[k] = len(d)
    return d[k]
for r in rows:
    if len(r) != 10 or r[8] not in ('COMERCIANTE','PRODUTOR','IMPORTADOR','EXPORTADOR'): continue
    uf, m, reg, st, cnpj, rz, nf, area, a, c = [x.strip() for x in r]
    e = est.get(reg)
    if not e:
        if reg not in seen: seen[reg] = 'base' if first_run else today
        e = est[reg] = [uf, idx(mun, m), reg, st[:1], cnpj, rz.upper(), nf.upper(), [], seen[reg]]
    p = [idx(at, a), idx(cl, c)]
    if p not in e[7]: e[7].append(p)
json.dump(seen, open(seenp, 'w'))
inv = lambda d: [k for k, _ in sorted(d.items(), key=lambda x: x[1])]
mtime = datetime.date.fromtimestamp(os.path.getmtime(src)).strftime('%d/%m/%Y')
data = {'mun': inv(mun), 'at': inv(at), 'cl': inv(cl), 'e': list(est.values()), 'atualizado': mtime, 'hoje': today}
s = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
t = open(os.path.join(base, 'tools', 'template.html'), encoding='utf-8').read()
open(os.path.join(base, 'sipeagro-fertilizantes.html'), 'w', encoding='utf-8').write(t.replace('__DATA__', s))
novos = sum(1 for e in est.values() if e[8] not in ('base',) and e[8] >= (datetime.date.today()-datetime.timedelta(days=60)).isoformat())
print(f'{len(est)} empresas | novas (60 dias): {novos} | base de {mtime}')
