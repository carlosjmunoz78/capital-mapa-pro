#!/usr/bin/env python3
"""CEREBRO-NEWS-001 / semanal LAB con hechos verificables: dos ediciones SIN llamadas a IA, SIN envío.

This is the explicit deterministic fallback, not an OpenAI or DeepSeek provider call.
It always fails closed for stale/unverified news and keeps all 10 blocks in both audiences.
"""
import argparse
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse, urlencode

from bs4 import BeautifulSoup
import crear_newsletters as motor
from redactar_con_deepseek import verified_news, validate_draft, BANNED, HYPE

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'out'
AUDIENCES=('b2c','b2b')


def require_news(registry,kind,today):
    records=verified_news(registry,kind,today=today)
    if not records:raise RuntimeError('HOLD_NO_VERIFIED_RECENT_NEWS')
    if not all(record['source_url'].startswith('https://www.bde.es/') or record['source_url'].startswith('https://www.ecb.europa.eu/') for record in records):
        raise RuntimeError('HOLD_UNAPPROVED_PRIMARY_SOURCE')
    return records


def extract_official_signal(records):
    euribor = next((x for x in records if 'EURIBOR' in x['id']), None)
    ecb = next((x for x in records if 'BCE' in x['id']),None)
    if not euribor or not ecb: return extract_generic_official_signal(records)
    raw=' '.join(euribor['facts'])
    pair=re.search(r'octubre de 2026 fue del (\d,\d+)\s*%,?\s*frente al (\d,\d+)\s*%',raw,re.I)
    if not pair:raise RuntimeError('HOLD_NEWS_NUMBERS_UNRECOGNIZED')
    if 'mantuv' not in ' '.join(ecb['facts']).lower() and 'mantuvo' not in ' '.join(ecb['facts']).lower():
        raise RuntimeError('HOLD_ECB_DECISION_UNSUPPORTED')
    return {'euribor':pair.group(1),'previous':pair.group(2),'euribor_date':euribor['published_at'], 'ecb_date':ecb['published_at']}



def extract_generic_official_signal(records):
    if not records: raise RuntimeError('HOLD_NO_CURRENT_PRIMARY_SOURCE')
    entry=records[0]
    title=entry['title']
    terms={'euríbor':'Euríbor','hipotec':'Hipotecas','tipos de interés':'Tipos de interés','crédito':'Crédito','vivienda':'Vivienda','monetari':'Política monetaria'}
    topic=next((v for k,v in terms.items() if k in title.casefold()),'Actualidad financiera')
    irrelevant=re.compile(r'podr[aá]s elegir las [aá]reas|recibir nuestras comunicaciones|pol[ií]tica de cookies|preferencias de privacidad|newsletter',re.I)
    evidence=[x.strip() for x in entry['facts'] if not BANNED.search(x) and not HYPE.search(x) and not irrelevant.search(x) and 'http' not in x.lower() and 145<=len(x.strip())<=390 and re.search(r'[.!?]\s+',x)]
    if not evidence: raise RuntimeError('HOLD_UNSAFE_OR_EMPTY_PRIMARY_FACT')
    return {'type':'generic_official','topic':topic,'fact':evidence[-1],
            'source_date':entry['published_at'], 'source_id':entry['id']}


def generic_copy(kind, signal):
    topic=signal['topic'];fact=signal['fact'];published=signal['source_date']
    when=f'{published[8:10]}/{published[5:7]}/{published[:4]}'
    introductory=(f'Una publicación oficial del {when} contiene esta información: «{fact}». '
                  'Es un dato general y no determina el resultado de una solicitud de financiación concreta.')
    if kind=='b2c':
        return {
          'subject':f'🟠 FÉNIX HOGAR | {topic}: una clave antes de comprar',
          'preheader':f'{topic}, claves prácticas y herramientas para preparar mejor tu vivienda.',
          'hero_title':'Decidir mejor empieza por entender qué ha cambiado.',
          'hero_intro':f'La actualidad sobre {topic.lower()} puede afectar a las preguntas que te hagas antes de comprar. Lo importante es distinguir un dato general de las condiciones que te ofrezcan a ti.',
          'letter':'Reunimos información contrastada y te ayudamos a convertirla en preguntas útiles antes de reservar una vivienda.',
          'main_title':f'{topic}: qué aporta la última publicación contrastada',
          'main_intro':introductory,
          'main_quote':'Ninguna noticia general sustituye el estudio de tu economía y de la vivienda.',
          'mortgage_body':'Antes de pedir financiación, revisa ahorro, deudas, documentación y gastos. Las condiciones dependerán de la entidad y de tu situación; una simulación no es una aprobación.',
          'question':'¿Necesitas entender los gastos de compra, la cuota o el riesgo de entregar arras antes de tiempo?',
          'cta_title':'Pon números a la decisión de comprar',
          'cta_body':'Podemos ordenar tus documentos, gastos y plazos para que estudies tu operación con mayor claridad. La decisión sobre la financiación corresponde a la entidad.',
        }
    return {
       'subject':f'🟠 FÉNIX PRO | {topic}: puntos clave para tu agencia',
       'preheader':f'Actualidad de {topic.lower()}, señales de riesgo y recurso práctico para inmobiliarias.',
       'hero_title':'La operación gana seguridad cuando la financiación se revisa a tiempo.',
       'hero_intro':f'Una publicación reciente sobre {topic.lower()} puede abrir preguntas entre compradores. Te ayudamos a explicar los datos sin prometer resultados.',
       'letter':'Separar una noticia económica de la capacidad real de un comprador evita malos entendidos y protege el trabajo de tu agencia.',
       'main_title':f'{topic}: información verificada que conviene explicar',
       'main_intro':introductory,
       'main_quote':'Una cifra de mercado no reemplaza un preanálisis hipotecario.',
       'case_body':'Un cliente pregunta si una noticia reciente garantiza una mejor hipoteca. Es un ejemplo hipotético: conviene explicar que la oferta depende de su expediente, documentación y criterios de la entidad.',
       'question':'¿Qué duda se repite más entre tus compradores al hablar de financiación y plazos?',
       'cta_title':'Revisa la financiación antes de comprometer la operación',
       'cta_body':'Tu agencia conserva el control comercial. Fénix puede orientar el análisis hipotecario con la autorización y documentos correspondientes, sin prometer aprobaciones.',
    }


def edition_copy(kind,signal):
    if signal.get('type')=='generic_official':return generic_copy(kind,signal)
    x,y=signal['euribor'],signal['previous']
    if kind=='b2c':
        return {
            'subject':f'Euríbor al {x} %: qué significa antes de comprar vivienda',
            'preheader':f'Nueva cifra oficial ({x} %), claves para evitar sorpresas y una herramienta de Fénix para ordenar tu compra.',
            'hero_title':'La actualidad cambia. Tus decisiones merecen claridad.',
            'hero_intro':f'La última cifra oficial del euríbor ya está aquí: {x} %. La noticia importa, pero tu compra no se decide con un solo porcentaje. Vamos a traducirlo a preguntas concretas y a pasos que sí puedes controlar.',
            'letter':'Queremos que esta carta te sirva para algo más que estar al día. Un dato financiero puede parecer lejano hasta que empiezas a mirar viviendas, a contar tus ahorros o a plantearte una reserva. Te explicamos qué sabemos y qué deberías revisar en tu caso.',
            'main_title':f'El dato de actualidad: euríbor del {x} %',
            'main_intro':f'Según la publicación oficial del {signal["euribor_date"][-2:]}/{signal["euribor_date"][5:7]}/{signal["euribor_date"][:4]}, el euríbor a un año pasó del {y} % de septiembre al {x} % de octubre. La diferencia es pequeña: no significa que cada banco vaya a ofrecerte automáticamente una mejor hipoteca. En su decisión del {signal["ecb_date"][-2:]}/{signal["ecb_date"][5:7]}, el BCE mantuvo sus tipos oficiales sin cambios. Por eso, antes de reservar, siguen importando estas tres comprobaciones:',
            'main_quote':'Un titular puede explicar el mercado. La documentación y tus números explican tu compra.',
            'mortgage_body':'¿Podrías financiar el 90 % del precio? Depende de tu situación, del inmueble y de los criterios de cada entidad. Aunque una oferta cubriera esa proporción, tendrías que estudiar impuestos, gastos y reservas de ahorro. No confundas porcentaje de financiación con aprobación bancaria.',
            'question':'¿Lo que más te preocupa de comprar es el ahorro inicial, la cuota mensual o entregar una reserva demasiado pronto?',
            'cta_title':'¿Te gustaría poner orden a los números antes de decidir?',
            'cta_body':'Cuéntanos qué estás valorando y qué te preocupa. Revisaremos contigo los puntos que necesitan estudiarse antes de comprometer tus ahorros. Sin prometer la aprobación de ninguna entidad.',
        }
    return {
        'subject':f'Euríbor al {x} %: el dato que conviene explicar bien al comprador',
        'preheader':'Actualidad hipotecaria comprobada, semáforo de riesgos y recurso práctico para agencias.',
        'hero_title':'Una buena venta se protege antes de cerrar las arras.',
        'hero_intro':f'El último euríbor oficial se ha situado en el {x} %. Pero una cifra de mercado no convierte un comprador interesado en un expediente viable. Ahí es donde una conversación profesional, hecha a tiempo, puede salvar semanas de trabajo.',
        'letter':'La actualidad económica genera preguntas en las visitas y en las llamadas. Nuestra propuesta es sencilla: interpretarla sin alarmismos, no prometer financiación y saber cuándo derivar el análisis a quien corresponda.',
        'main_title':f'La noticia relevante: euríbor {x} % y tipos oficiales estables',
        'main_intro':f'La cifra oficial de octubre bajó ligeramente frente a septiembre ({y} %). Además, el BCE dejó sus tipos principales sin cambios el {signal["ecb_date"][-2:]}/{signal["ecb_date"][5:7]}. No extrapoles estos datos a las condiciones concretas de un comprador. Antes de fijar plazos o arras, prepara esta conversación: ¿qué financiación tiene realmente revisada, con qué documentación y qué riesgos siguen abiertos?',
        'main_quote':'La noticia sirve para conversar; el preanálisis sirve para no dar una operación por segura demasiado pronto.',
        'case_body':'Un comprador comenta: «He visto que el euríbor ha bajado; el banco seguro que me dará una buena hipoteca». Es una conversación ficticia para ilustrar la duda. Conviene preguntarle qué parte de su economía se ha revisado y dejar claro que las cifras oficiales no son una oferta individual.',
        'question':'Cuando alguien dice «el banco ya me ha dicho que sí», ¿sabéis si habla de una simulación o de un expediente realmente estudiado?',
        'cta_title':'Antes de fijar una fecha, revisemos la financiación del comprador',
        'cta_body':'Tu equipo mantiene la gestión comercial. Con el consentimiento correspondiente, Fénix puede ayudarte a ordenar el análisis hipotecario sin prometer una concesión bancaria.',
    }


def current_campaign_suffix(today):
    y,w,_=today.isocalendar()
    return f'{y}w{w:02d}'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--date',default=date.today().isoformat())
    ap.add_argument('--registry',default=str(ROOT/'news_observer_verified.json'))
    args=ap.parse_args()
    today=date.fromisoformat(args.date)
    registry=json.loads(Path(args.registry).read_text(encoding='utf-8'))
    base=json.loads((ROOT/'motor_contenidos.json').read_text(encoding='utf-8'))
    if (base.get('environment'),base.get('send_enabled'),base.get('publish_enabled'),base.get('approved'))!=('LAB',False,False,False):
        raise RuntimeError('HOLD_SAFETY_FLAGS')
    # Critical: never rewrite base manifest, only use a temporary in-memory copy.
    motor.D=copy.deepcopy(base['audiences'])
    original_url_builder=motor.U
    def trace(path,edition,block):
        from urllib.parse import urlparse
        # Preserve the original site's URL validation.
        if path.startswith('https://'):
            assert urlparse(path).netloc=='fenixcapital.es'
            url=path
        else:
            assert path.startswith('/') and not path.startswith('//')
            url='https://fenixcapital.es'+path
        return url + ('&' if '?' in url else '?') + urlencode({'utm_source':'brevo','utm_medium':'email','utm_campaign':f'fenix_news_{edition}_{current_campaign_suffix(today)}','utm_content':block})
    motor.U=trace
    out={}
    for kind in AUDIENCES:
        facts=require_news(registry,kind,today)
        signal=extract_official_signal(facts)
        copy_fields=edition_copy(kind,signal)
        data=validate_draft({'audience':kind,'source_ids':[f['id'] for f in facts],'copy':copy_fields},base,kind,facts)
        motor.D[kind]=data
        out[kind]={'source_ids':[f['id'] for f in facts],'copy_sha256':hashlib.sha256(json.dumps(copy_fields,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
    OUT.mkdir(exist_ok=True)
    for kind in AUDIENCES:
        c=motor.D[kind]
        h=(OUT/f'NEWS_FENIX_{kind}_PREVISUALIZACION.html')
        b=(OUT/f'NEWS_FENIX_{kind}_BREVO_BORRADOR.html')
        h.write_text(motor.make(kind,True),encoding='utf-8')
        b.write_text(motor.make(kind,False),encoding='utf-8')
        out[kind].update({'preview':motor.validate(h,kind),'brevo':motor.validate(b,kind),'subject':c['subject'],'preheader':c['preheader']})
        soup=BeautifulSoup(h.read_text(encoding='utf-8'),'html.parser')
        blocks=[t['data-block'] for t in soup.select('[data-block]')]
        if len(blocks)!=10 or len(set(blocks))!=10:raise RuntimeError('HOLD_MISSING_BLOCKS')
        if not any(c['main_title']==t for t in soup.stripped_strings):raise RuntimeError('HOLD_MISSING_CURRENT_NEWS_SECTION')
    report={'engine_id':'CEREBRO-NEWS-001','environment':'LAB','date':today.isoformat(),'weekly_campaign_suffix':current_campaign_suffix(today),'send_enabled':False,'publish_enabled':False,'approved':False,'brevo_campaign_created':False,'api_called':False,'content_origin':'CEREBRO_DETERMINISTIC_VERIFIED_NEWS_FALLBACK_NOT_DEEPSEEK','source_registry_sha256':hashlib.sha256(Path(args.registry).read_bytes()).hexdigest(),'audiences':out}
    (OUT/'RESULTADO_PRUEBA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CEREBRO_WEEKLY_FALLBACK_PASS', today.isoformat(), {k:(v['preview']['word_count'],len(v['preview']['blocks'])) for k,v in out.items()})

if __name__=='__main__':main()