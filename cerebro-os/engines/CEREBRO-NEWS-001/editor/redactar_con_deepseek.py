#!/usr/bin/env python3
"""CEREBRO-NEWS-001 DeepSeek authoring adapter, isolated LAB: drafts only, never sends.

Uses only standard library; no PII, no provider contacts. --live is explicitly opt-in.
Reads local versioned source evidence; no internet/news search performed by the model.
"""
from __future__ import annotations
import argparse
import copy
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
MODEL = 'deepseek-flash'  # DeepSeek V4.1 Flash, official name as of 2026-11-17
URL = 'https://api.deepseek.com/chat/completions'
# Peak pricing in USD/1M tokens (DeepSeek official). Cost floor not claimed.
PEAK_INPUT = 0.30
PEAK_OUTPUT = 1.20
MAX_OUTPUT_TOKENS = 3000
MAX_PRECALL_USD = 0.025
MAX_MONTHLY_USD = 1.00
# Whitelist fields. Architecture, URLs, links, blocks and approval flags are locked.
EDITABLE = {
    'subject','preheader','hero_title','hero_intro','letter',
    'main_title','main_intro','main_quote',
    'mortgage_title','mortgage_body','article_title','article_body',
    'tool_title','tool_body','key_title','key_body',
    'trust_title','trust_body','question_title','question','question_body',
    'cta_title','cta_body','closing','case_title','case_body',
}
BANNED = re.compile(r'\b(c[oó]rdoba|andaluc[ií]a|ja[eé]n|sevilla|granada|m[aá]laga|huelva|c[aá]diz|almer[ií]a|espa[nñ]a|madrid|barcelona|valencia|provincia|regi[oó]n|v[ií]deo semanal|v[ií]deo de la semana|newsletter n[úu]mero|edici[oó]n n[.º°])\b', re.I)
HYPE = re.compile(r'\b(garantizad[oa]s?|aprobaci[oó]n segura|100\s*%\s*de aprobaci[oó]n|sin riesgos?|siempre aceptan)\b', re.I)

def load_json(path: Path) -> dict:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError('JSON must be an object')
    return value

def verified_news(registry: dict, audience: str, *, today: date | None=None) -> list[dict]:
    today=today or date.today()
    chosen=[]
    for item in registry.get('items', []):
        if audience not in item.get('audiences',[]):continue
        for k in ('id','title','source_url','published_at','verified_at','facts'):
            if not item.get(k): raise ValueError('News source missing '+k)
        target=urllib.parse.urlparse(item['source_url'])
        if target.scheme!='https' or not target.netloc or target.username or target.password:raise ValueError('Unsafe news URL')
        date_pub=date.fromisoformat(item['published_at'][:10])
        date_verified=date.fromisoformat(item['verified_at'][:10])
        if not (0 <= (today-date_pub).days <= 21 and 0 <= (today-date_verified).days <= 7):continue
        if not isinstance(item['facts'],list) or not all(isinstance(f,str) and 8<len(f)<=400 for f in item['facts']):raise ValueError('Malformed evidence')
        chosen.append({k:item[k] for k in ('id','title','source_url','published_at','verified_at','facts')})
    return chosen[:3]

def price_ceiling(prompt_len:int, max_output:int=MAX_OUTPUT_TOKENS) -> float:
    # Very conservative: at most one billable input token per UTF-8 byte.
    return round((prompt_len*4/1_000_000)*PEAK_INPUT+(max_output/1_000_000)*PEAK_OUTPUT,6)

def make_payload(original: dict, kind: str, news: list[dict]) -> dict:
    target=original['audiences'][kind]
    locked={k:target[k] for k in ('name','urls','audience')}
    system='''Actúas como redactor senior de Fénix Capital. Español natural, sin voz robótica. Prepara exclusivamente las claves de la whitelist solicitada. Todo dato reciente procede EXCLUSIVAMENTE de los hechos y fuentes recibidos, nunca del conocimiento del modelo. No inventes testimonios, personas, datos, porcentajes de financiación, contratos ni casos reales. No menciones ciudades, regiones ni países, no incluyas vídeos, ni numeración de edición, ni enlaces externos en el cuerpo. Al inicio incluye una noticia relevante de las fuentes, si procede, y explicaciones prácticas para convertir visitas en solicitudes útiles. No cambies los enlaces/URLs, segmento, marca ni el consentimiento. Devuelve SOLO un objeto JSON con claves audience, source_ids, copy. Fuente de cualquier noticia en source_ids, títulos y hechos exactos. No afirmar que se ha comprobado algo si no está en los hechos. Tono editorial humano, cercano, elegante, curioso, sin promesas bancarias. Respeta tres puntos clave de los contenidos existentes, 10 bloques de la newsletter y CTA existente.'''
    user={'audience':kind,'current_edition':{k:v for k,v in target.items() if k in EDITABLE},'locked':locked,'source_news':news,'editable_keys':sorted(EDITABLE),'rule':'one article-worthy current news story if supported by facts, no external links in customer email; preserve other sections'}
    return {'model':MODEL,'thinking':{'type':'disabled'},'response_format':{'type':'json_object'},'max_tokens':MAX_OUTPUT_TOKENS,'temperature':0.65,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(user,ensure_ascii=False,sort_keys=True)}]}

def validate_draft(response: dict,original: dict,kind: str,news: list[dict]) -> dict:
    if set(response)!={'audience','source_ids','copy'}:raise ValueError('Unexpected response keys')
    if response['audience']!=kind:raise ValueError('Wrong audience')
    if not isinstance(response['copy'],dict) or not response['copy']:raise ValueError('Missing copy')
    if set(response['copy'])-EDITABLE:raise ValueError('Forbidden data fields in response')
    if not isinstance(response['source_ids'],list) or set(response['source_ids'])-set(x['id'] for x in news):raise ValueError('Unknown evidence source IDs')
    if news and not response['source_ids']:raise ValueError('No news cited')
    for k,v in response['copy'].items():
        if not isinstance(v,str) or not (4<=len(v)<=1600):raise ValueError('Invalid copy: '+k)
        if BANNED.search(v):raise ValueError('Geography/video prohibited: '+k)
        if HYPE.search(v):raise ValueError('Unsupported guarantee: '+k)
        if re.search(r'https?://|<script|\{\{',v,re.I):raise ValueError('Unsafe content: '+k)
    # Only whitelisted text, not identity or routing, can be applied at editorial review.
    clone=copy.deepcopy(original['audiences'][kind])
    clone.update(response['copy'])
    if clone['urls']!=original['audiences'][kind]['urls']:raise ValueError('URL changed')
    return clone

def request_deepseek(payload:dict,key:str,timeout:int=40) -> dict:
    body=json.dumps(payload,ensure_ascii=False).encode('utf-8')
    request=urllib.request.Request(URL,data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=timeout) as f:
            raw=f.read(2_000_000)
    except urllib.error.HTTPError as e:
        # Do not log request, headers, tokens, provider response body or secrets.
        raise RuntimeError('DeepSeek failed HTTP '+str(e.code)) from None
    except urllib.error.URLError:
        raise RuntimeError('DeepSeek network unavailable') from None
    result=json.loads(raw)
    return {'copy':json.loads(result['choices'][0]['message']['content']), 'usage':result.get('usage',{})}

def main(args=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--audience',choices=['b2c','b2b'],required=True)
    ap.add_argument('--news',default=str(ROOT/'news_observer_verified.json'))
    ap.add_argument('--live',action='store_true',help='explicitly authorizes a paid draft call, never an email send')
    ap.add_argument('--output',default=None)
    ns=ap.parse_args(args)
    original=load_json(ROOT/'motor_contenidos.json')
    if original.get('send_enabled') or original.get('publish_enabled'):raise ValueError('Invalid safety gate in base config')
    registry=load_json(Path(ns.news))
    news=verified_news(registry,ns.audience)
    if not news:raise ValueError('NO_VERIFIED_CURRENT_NEWS: provide a dated observer record before generating')
    payload=make_payload(original,ns.audience,news)
    prompt_bytes=len(json.dumps(payload,ensure_ascii=False).encode('utf-8'))
    maximum=price_ceiling(prompt_bytes)
    if maximum>MAX_PRECALL_USD:raise ValueError('Cost cap exceeded before request')
    p=Path(ns.output) if ns.output else ROOT/f'deepseek_draft_{ns.audience}.json'
    if not p.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Output must stay inside the LAB folder')
    if not ns.live:
        print(json.dumps({'mode':'DRY_RUN','audience':ns.audience,'model':MODEL,'verified_news_ids':[x['id'] for x in news],'max_pre_call_usd':maximum,'max_monthly_usd':MAX_MONTHLY_USD,'send_enabled':False,'publish_enabled':False},ensure_ascii=False,indent=2));return
    key=os.environ.get('DEEPSEEK_API_KEY','').strip()
    if not key:raise RuntimeError('DEEPSEEK_API_KEY not configured in the runtime; never paste key in chat')
    # Monthly ledger is only an app-level guard; concurrency/billing must be rate limited by supervisor.
    ledger=ROOT/'.deepseek_monthly_ledger.json'
    state=load_json(ledger) if ledger.exists() else {}
    month=date.today().isoformat()[:7]
    spend=float(state.get(month,0))
    if spend+maximum>MAX_MONTHLY_USD:raise RuntimeError('Monthly DeepSeek budget gate failed')
    response=request_deepseek(payload,key)
    candidate=validate_draft(response['copy'],original,ns.audience,news)
    usage=response['usage'];inp=usage.get('prompt_tokens');out=usage.get('completion_tokens')
    estimated=round((float(inp or prompt_bytes)*PEAK_INPUT+float(out or MAX_OUTPUT_TOKENS)*PEAK_OUTPUT)/1_000_000,6)
    state[month]=round(spend+estimated,6)
    ledger.write_text(json.dumps(state,sort_keys=True,indent=2),encoding='utf-8')
    result={'engine_id':'CEREBRO-NEWS-001','status':'DRAFT_HOLD','audience':ns.audience,'model':MODEL,'news_evidence':news,'copy':response['copy']['copy'],'source_ids':response['copy']['source_ids'],'candidate_content':candidate,'provider_usage':usage,'conservative_cost_estimate_usd':estimated,'created_at':datetime.now().isoformat(),'approved':False,'brevo_send_enabled':False}
    # Atomic on one worker: do not allow output to represent live state.
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
    print(json.dumps({'status':'DRAFT_HOLD','output_file':p.name,'evidence_count':len(news),'conservative_cost_estimate_usd':estimated,'approved':False},ensure_ascii=False))

if __name__=='__main__':main()