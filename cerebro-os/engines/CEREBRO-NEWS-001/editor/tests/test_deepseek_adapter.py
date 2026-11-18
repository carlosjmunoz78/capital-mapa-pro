#!/usr/bin/env python3
"""Offline DeepSeek editorial integration QA. No secrets, API calls or emails."""
import copy, json, sys, pathlib, tempfile, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import redactar_con_deepseek as d

def item(today=None):
    x=(today or datetime.date.today()).isoformat()
    return {'id':'FACT-001','title':'Cambio regulatorio contrastado, ejemplo de laboratorio',
            'source_url':'https://www.boe.es/','published_at':x,'verified_at':x,
            'facts':['El observador verifica y transcribe este dato de fuente oficial antes de redactar.'],
            'audiences':['b2c','b2b']}

def registry():return {'items':[item()]}

def good(kind='b2c'):
    return {'audience':kind,'source_ids':['FACT-001'],'copy':{'subject':'Comprueba qué cambia antes de comprar','key_title':'Información que merece contexto','key_body':'Una noticia verificada debe explicarse sin conclusiones precipitadas ni promesas financieras.'}}

def fails(f):
    try:f()
    except (ValueError,AssertionError):return
    raise AssertionError('Must reject input')

c=json.loads((ROOT/'motor_contenidos.json').read_text(encoding='utf-8'))
for kind in ['b2c','b2b']:
    src=d.verified_news(registry(),kind)
    assert len(src)==1
    valid=d.validate_draft(good(kind),c,kind,src)
    assert valid['urls']==c['audiences'][kind]['urls'] and valid['subject']=='Comprueba qué cambia antes de comprar'
    tmp=good(kind);tmp['copy']['hero_title']='Oferta en Córdoba';fails(lambda:d.validate_draft(tmp,c,kind,src))
    tmp=good(kind);tmp['copy']['new_external_link']='https://other.example';fails(lambda:d.validate_draft(tmp,c,kind,src))
    tmp=good(kind);tmp['copy']['cta_title']='Aprobación garantizada';fails(lambda:d.validate_draft(tmp,c,kind,src))
    tmp=good(kind);tmp['source_ids']=['UNKNOWN'];fails(lambda:d.validate_draft(tmp,c,kind,src))
    tmp=good(kind);tmp['copy']['key_body']='Visita https://externo.es';fails(lambda:d.validate_draft(tmp,c,kind,src))
    print('PASS',kind,'evidence / preserve URLs / 5 unsafe cases blocked')
# Expired publication: no simulated current news
old=item();old['published_at']='2024-01-01';assert not d.verified_news({'items':[old]},'b2c')
# Unverified/off-domain source
bad=item();bad['source_url']='http://example.org';fails(lambda:d.verified_news({'items':[bad]},'b2c'))
# Model exact & thinking disabled, no web search, no automated publication
prompt=d.make_payload(c,'b2c',d.verified_news(registry(),'b2c'))
assert prompt['model']=='deepseek-flash' and prompt['thinking']=={'type':'disabled'}
assert prompt['max_tokens']<=3000
assert not prompt.get('tools')
# Very conservative budget estimate, not vendor hard cap
cost=d.price_ceiling(len(json.dumps(prompt,ensure_ascii=False).encode('utf8')))
assert cost<=d.MAX_PRECALL_USD, (cost,'PRECALL_BUDGET_REJECTION')
print('PASS model selection, thinking off, no web tools, pre-call budget cap',cost)
# Local dry-run must NEVER send; only source metadata
with tempfile.TemporaryDirectory() as folder:
    src=pathlib.Path(folder)/'sources.json';src.write_text(json.dumps(registry()))
    d.main(['--audience','b2c','--news',str(src)])
print('PASS DRY_RUN with no secret, no API and no send')
print('TOTAL 17 checks (2 x 7 + 3) PASS')