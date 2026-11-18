#!/usr/bin/env python3
"""Read an already validated DeepSeek draft and render both audience HTMLs. LAB ONLY.

Never calls DeepSeek, Brevo, Supabase or a CRM. Never sends email.
"""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
import crear_newsletters as renderer
from redactar_con_deepseek import load_json, validate_draft, verified_news

ROOT = Path(__file__).resolve().parent

def render_draft(draft: dict, base: dict, registry: dict, outdir: Path) -> dict:
    if draft.get('engine_id')!='CEREBRO-NEWS-001' or draft.get('status')!='DRAFT_HOLD':
        raise ValueError('Expected a CEREBRO NEWS LAB draft')
    if draft.get('approved') is not False or draft.get('brevo_send_enabled') is not False:
        raise ValueError('Draft cannot have approval/send enabled')
    if base.get('send_enabled') or base.get('publish_enabled') or base.get('environment')!='LAB':
        raise ValueError('Base config safety policy failed')
    kind=draft.get('audience')
    if kind not in ('b2c','b2b'): raise ValueError('Invalid audience')
    evidence=verified_news(registry,kind)
    if not evidence: raise ValueError('No verified, recent source records')
    chosen=draft.get('source_ids')
    if not isinstance(chosen,list) or not chosen:
        raise ValueError('Source IDs missing: cannot attribute current news')
    response={'audience':kind,'source_ids':chosen,'copy':draft.get('copy')}
    candidate=validate_draft(response,base,kind,evidence)
    if draft.get('news_evidence')!=evidence:
        raise ValueError('Evidence changed since source verification')
    renderer.D=copy.deepcopy(base['audiences'])
    renderer.D[kind]=candidate
    outdir.mkdir(parents=True,exist_ok=True)
    result={}
    for target in ['b2c','b2b']:
        p=outdir/('newsletter_'+target+'_brevo_DRAFT_HOLD.html')
        p.write_text(renderer.make(target,False),encoding='utf-8')
        result[target]=renderer.validate(p,target)
    report={'status':'DRAFT_HOLD','audience':kind,'source_ids':chosen,
            'approved':False,'brevo_send_enabled':False,'pdf_ready':False,
            'email_send_attempted':False,'html':result}
    (outdir/'render_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--draft',required=True)
    ap.add_argument('--registry',default=str(ROOT/'news_observer_verified.json'))
    ap.add_argument('--outdir',default=str(ROOT/'_rendered_draft_hold'))
    ns=ap.parse_args()
    out=Path(ns.outdir).resolve()
    if not out.is_relative_to(ROOT): raise ValueError('Output must stay inside the LAB folder')
    report=render_draft(load_json(Path(ns.draft)),load_json(ROOT/'motor_contenidos.json'),load_json(Path(ns.registry)),out)
    print(json.dumps({k:report[k] for k in ('status','audience','source_ids','approved','brevo_send_enabled')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()