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
# --- Qlik: contatos e produtos ---
qp = os.path.join(base, 'dados', 'qlik.json')
nprod = 0
if os.path.exists(qp):
    q = json.load(open(qp, encoding='utf-8'))
    ct = {r[0]: r[1:] for r in q['contatos']}
    for reg, e in est.items():
        c = ct.get(reg) or ['', '', '']
        e += [(c[0] or '').strip(), (c[1] or '').strip(), (c[2] or '').strip()]
    pseenp = os.path.join(base, 'dados', 'primeira_vez_produto.json')
    pseen = json.load(open(pseenp)) if os.path.exists(pseenp) else None
    pfirst = pseen is None; pseen = pseen or {}
    dic = {k: {} for k in ('est', 'nome', 'cl', 'tipo', 'sit', 'nat', 'car', 'modo', 'g', 'u')}
    rows = []
    for r in q['produtos']:
        num, er, nome, clp, tipo, sit, dt, nat, gar, car, modo = (x or '' for x in r)
        if num not in pseen: pseen[num] = 'base' if pfirst else today
        seq = num.split(' ')[-1]
        gf = []
        for g in gar.split('\u00a6'):
            if not g: continue
            a = (g.split('|') + ['', '', ''])[:3]
            try: v = float(a[1].replace(',', '.'))
            except ValueError: v = a[1]
            gf += [idx(dic['g'], a[0]), v, idx(dic['u'], a[2])]
        novo = 0 if pseen[num] == 'base' else int(pseen[num].replace('-', ''))
        rows.append([idx(dic['est'], er), seq, idx(dic['nome'], nome), idx(dic['cl'], clp), idx(dic['tipo'], tipo), idx(dic['sit'], sit),
                     dt, idx(dic['nat'], nat), idx(dic['car'], car), idx(dic['modo'], modo), gf, novo])
    json.dump(pseen, open(pseenp, 'w'))
    pd = {k: inv(v) for k, v in dic.items()}; pd['p'] = rows; pd['hoje'] = today
    open(os.path.join(base, 'produtos.json'), 'w', encoding='utf-8').write(json.dumps(pd, ensure_ascii=False, separators=(',', ':')))
    nprod = len(rows)
mtime = datetime.date.fromtimestamp(os.path.getmtime(src)).strftime('%d/%m/%Y')
data = {'mun': inv(mun), 'at': inv(at), 'cl': inv(cl), 'e': list(est.values()), 'atualizado': mtime, 'hoje': today}
s = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
t = open(os.path.join(base, 'tools', 'template.html'), encoding='utf-8').read()
open(os.path.join(base, 'sipeagro-fertilizantes.html'), 'w', encoding='utf-8').write(t.replace('__DATA__', s))
novos = sum(1 for e in est.values() if e[8] not in ('base',) and e[8] >= (datetime.date.today()-datetime.timedelta(days=60)).isoformat())
print(f'{nprod} produtos | {len(est)} empresas | novas (60 dias): {novos} | base de {mtime}')
