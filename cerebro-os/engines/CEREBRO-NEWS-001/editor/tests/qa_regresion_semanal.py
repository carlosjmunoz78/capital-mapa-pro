from datetime import date
from pathlib import Path
import json,re,sys
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ejecutar_prueba_semanal import require_news,extract_official_signal,edition_copy
from redactar_con_deepseek import BANNED,HYPE,validate_draft
r=Path(__file__).resolve().parents[1]
reg=json.loads((r/'news_observer_verified.json').read_text())
base=json.loads((r/'motor_contenidos.json').read_text())
passed=[]
for kind in ('b2c','b2b'):
 news=require_news(reg,kind,date(2026,11,17))
 sig=extract_official_signal(news)
 fields=edition_copy(kind,sig)
 assert not any(BANNED.search(v) or HYPE.search(v) for v in fields.values())
 validate_draft({'audience':kind,'source_ids':[x['id'] for x in news],'copy':fields},base,kind,news)
 h=(r/'out'/f'NEWS_FENIX_{kind}_BREVO_BORRADOR.html').read_text()
 soup=BeautifulSoup(h,'html.parser');b=[x.get('data-block') for x in soup.select('[data-block]')]
 assert len(b)==10 and len(set(b))==10
 assert '3,239' in soup.get_text(' ',strip=True)
 assert '{{ unsubscribe }}' in h
 assert 'utm_campaign=fenix_news_'+kind+'_2026w47' in h
 assert not soup.select('script,iframe,form')
 urls=[a.get('href') or '' for a in soup.select('a')]
 assert any(x.startswith('https://fenixcapital.es/') for x in urls)
 assert all('bde.es' not in x and 'ecb.europa.eu' not in x for x in urls)
 passed.append(f'{kind}:10 blocks, news, links, UTM, no outbound news, unsub, safe HTML')
try:
 require_news(reg,'b2c',date(2026,12,20))
 raise AssertionError('FAILED: accepted stale news')
except RuntimeError as e:
 assert str(e)=='HOLD_NO_VERIFIED_RECENT_NEWS'
 passed.append('stale news -> HOLD')
try:
 require_news({'items':[]},'b2b',date(2026,11,17))
 raise AssertionError('FAILED: accepted missing evidence')
except RuntimeError as e:
 assert str(e)=='HOLD_NO_VERIFIED_RECENT_NEWS'
 passed.append('empty sources -> HOLD')
assert base['send_enabled'] is False and base['publish_enabled'] is False and base['approved'] is False
passed.append('no send / no publish / no approval')
print('REGRESSION:',len(passed),'PASS')
print('\n'.join(passed))