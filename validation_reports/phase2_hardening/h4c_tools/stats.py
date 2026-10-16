import json,glob,collections,re
led=json.load(open('ledger.json'))
st=collections.Counter(); role=collections.Counter()
for d,e in led.items():
    st[(e.get('role'),e.get('status'))]+=1
print('ledger (role,status):',dict(st))
logl=open('dispatch.log').read().splitlines()
print('dispatch lines:',sum(1 for l in logl if re.search(r'\bstem-batch44\d-S44\d-\d{3}-(first|confirming)',l) and 'SETASIDE' not in l and 'CORRECTION' not in l and 'NOTE' not in l))
print('SETASIDE lines:',sum('SETASIDE' in l for l in logl))
hv8=[l for l in logl if 'effort=medium' in l]; print('effort=medium dispatches:',len(hv8))
ov=collections.Counter(); npc=0; npl=[]
for g in ['S441','S442','S443','S444','S445','S446','S447']:
    for i,v in sorted(json.load(open(f'keys/{g}.key.json')).items()):
        n=v['node_id']; fs=glob.glob(f'../../../validation_reports/stem_review/{n}/stem-batch44*-confirming*.json')
        r=json.loads(json.load(open(max(fs,key=lambda f:json.load(open(f))['filed_at'])))['raw_reply'])
        ov[r['overall']]+=1
        nps=[c for c,x in r['clauses'].items() if x.get('verdict')=='NOT_PRODUCIBLE']
        if nps: npc+=len(nps); npl.append((i,nps))
print('standing overall:',dict(ov),'| NOT_PRODUCIBLE clauses:',npc,npl)
r49=[l for l in open('r49.log') if ' | ' in l and not l.startswith('#')]
print('r49 lines:',len(r49),'| all-disproved ->ruling21:',sum('ruling-21 judge' in l for l in r49))
models=collections.Counter(tuple(e.get('models') or []) for e in led.values() if 'models' in e); print('models:',dict(models))
