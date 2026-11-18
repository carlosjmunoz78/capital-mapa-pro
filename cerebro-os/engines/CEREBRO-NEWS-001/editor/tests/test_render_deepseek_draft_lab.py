from pathlib import Path
import copy, json, tempfile, sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from redactar_con_deepseek import load_json, verified_news
from render_deepseek_draft_lab import render_draft
base=load_json(ROOT/'motor_contenidos.json'); registry=load_json(ROOT/'news_observer_verified.json');today=None
news=verified_news(registry,'b2c'); assert len(news)==2
fixture={'engine_id':'CEREBRO-NEWS-001','status':'DRAFT_HOLD','audience':'b2c',
 'approved':False,'brevo_send_enabled':False,'source_ids':[news[0]['id']],
 'news_evidence':news,
 'copy':{'main_intro':'Según los últimos datos oficiales publicados, el euríbor de octubre se situó en el 3,239 % frente al 3,247 % del mes anterior. El dato no equivale a una oferta ni determina por sí solo el coste de tu préstamo.'}}
pass_count=0
with tempfile.TemporaryDirectory() as tmp:
    p=render_draft(fixture,base,registry,Path(tmp));assert p['status']=='DRAFT_HOLD';pass_count+=1
    html=(Path(tmp)/'newsletter_b2c_brevo_DRAFT_HOLD.html').read_text();assert '3,239' in html and '{{ unsubscribe }}' in html;pass_count+=1
    html2=(Path(tmp)/'newsletter_b2b_brevo_DRAFT_HOLD.html').read_text();assert '3,239' not in html2;pass_count+=1
    for update in [dict(source_ids=['UNKNOWN']),dict(copy={'urls':{}}),dict(approved=True),dict(brevo_send_enabled=True),dict(status='APPROVED'),dict(news_evidence=[]),dict(copy={'main_intro':'Oferta de hipoteca garantizada de por vida'})]:
        bad=copy.deepcopy(fixture);bad.update(update)
        try:render_draft(bad,base,registry,Path(tmp)/'bad')
        except (ValueError,TypeError):pass_count+=1
        else:raise AssertionError('Unsafe draft passed '+str(update))
print('RENDER_ADAPTER_PASS',pass_count,'/ 10; no external API/email calls')