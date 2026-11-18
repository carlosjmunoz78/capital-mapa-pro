#!/usr/bin/env python3
"""CEREBRO-NEWS-001 · Editor determinista de newsletters Fénix (LAB; no envíos)."""
from __future__ import annotations
import json, html, re, pathlib, hashlib, urllib.parse
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parent
BASE='https://fenixcapital.es'
PRIVACY=f'{BASE}/declaracion-de-privacidad/'
LEGAL=f'{BASE}/aviso-legal/'
SOCIAL={
 'Instagram':'https://www.instagram.com/fenixcapitalhipotecas/',
 'Facebook':'https://www.facebook.com/fenixhipotecas',
 'LinkedIn':'https://www.linkedin.com/company/fenixcapitalhipotecas/'
}
PUBLIC_IMAGE={
 'logo':'https://fenixcapital.es/wp-content/uploads/2026/10/Logo-Fenix-Capital-oficial-color-completo-scaled-1.png',
 'b2c':'https://fenixcapital.es/wp-content/uploads/2026/10/Fenix-C2B7-Pareja-haciendo-numeros-para-comprar-vivienda.jpg',
 'b2b':'https://fenixcapital.es/wp-content/uploads/2026/11/fenix-seo001-52663-cabecera-premium-apoyo-hipotecario-agencias-cordoba.webp',
}

def U(path, edition, block):
    """Trace click provenance without inserting PII or unverified conversion IDs."""
    if path.startswith('https://'):
        assert urllib.parse.urlparse(path).netloc == 'fenixcapital.es', 'URL fuera del dominio canónico'
        url=path
    else:
        assert path.startswith('/') and not path.startswith('//'), 'Ruta inválida'
        url=BASE+path
    k={'utm_source':'brevo','utm_medium':'email','utm_campaign':f'fenix_news_{edition}_202611','utm_content':block}
    return url+('?' if '?' not in url else '&')+urllib.parse.urlencode(k)

D={
 'b2c':{
  'audience':'Particulares','name':'Hipotecas sin vueltas',
  'subject':'La casa te gusta. Ahora hablemos de los números.',
  'preheader':'Arras, ahorro, financiación al 90 % y una calculadora: ideas útiles antes de dar el paso.',
  'hero_title':'Una casa ilusiona. Que los números no te quiten el sueño.',
  'hero_intro':'A veces todo empieza por una visita, una sensación y la frase «esta podría ser». Esa ilusión importa. Pero merece la pena acompañarla de números claros antes de entregar una señal.',
  'letter':'En Fénix nos gustan las preguntas que llegan a tiempo. Por eso, hoy no vamos a venderte una hipoteca milagrosa: vamos a ayudarte a ver qué deberías comprobar antes de comprometer tus ahorros.',
  'main_title':'Antes de reservar, hay tres conversaciones que conviene tener',
  'main_intro':'Aunque el piso te encante, todavía quedan piezas por encajar. Pregúntate lo siguiente:',
  'checkpoints':[
    ('El dinero completo','No basta con mirar la entrada. Hay que contar impuestos, gastos de compra y el colchón que quieres conservar después.'),
    ('La cuota de verdad','Suma las deudas que ya tienes. La cuota que parece cómoda en una calculadora puede dejar de serlo en el presupuesto cotidiano.'),
    ('El calendario','Pregunta qué ocurrirá si faltan documentos, la tasación llega por debajo del precio previsto o el banco necesita más tiempo.')],
  'main_quote':'La prisa por no perder una vivienda no debería hacerte perder claridad.',
  'mortgage_title':'¿Una hipoteca al 90 % significa que solo necesitas ahorrar un 10 %?',
  'mortgage_body':'No necesariamente. Ese porcentaje describe la parte financiada bajo los criterios que aplique la entidad; no sustituye los impuestos, gastos ni el análisis de tu caso. Y una simulación nunca es una aprobación. El porcentaje útil es el que encaja con tu economía completa.',
  'mortgage_link':'Entender la financiación al 90 %',
  'article_title':'Qué revisar antes de firmar arras',
  'article_body':'Si ya has encontrado vivienda, esta guía te ayuda a ordenar ahorro, precio, tasación, documentación y plazos. Mejor una conversación incómoda ahora que una sorpresa cuando ya has entregado dinero.',
  'article_link':'Leer la guía completa',
  'tool_title':'Ponle cifras a la compra, no solo a la hipoteca',
  'tool_body':'Una vivienda tiene precio de compra y también costes alrededor. Usa nuestra calculadora de gastos para estimarlos de forma orientativa antes de hacer promesas o fijar un presupuesto final.',
  'tool_link':'Calcular los gastos de compra',
  'key_title':'«Mi banco me ha dicho que sí». ¿Eso es suficiente?',
  'key_body':'Depende de qué haya revisado exactamente. Una conversación, una oferta orientativa o una simulación no equivalen a una decisión definitiva sobre tu expediente y esa vivienda. Pide claridad sobre lo que está confirmado y lo que falta por comprobar.',
  'trust_title':'Lo que puedes esperar de Fénix',
  'trust_body':'Primero escuchamos tu situación. Después contrastamos ingresos, ahorro, deudas, vivienda y documentación. Y te explicamos qué merece la pena estudiar y qué sigue pendiente. Sin venderte como segura una operación que todavía debe analizar la entidad.',
  'question_title':'Te hacemos una pregunta',
  'question':'Si hoy fueras a comprar, ¿qué te quitaría más el sueño: no tener ahorro suficiente, no saber qué cuota asumir o que se alarguen los plazos?',
  'question_body':'Respóndenos. Nos interesa conocer las dudas reales, también las que parecen demasiado sencillas.',
  'question_link':'Contar mi duda',
  'cta_title':'¿Y si revisamos tu compra antes de que tengas que decidir?',
  'cta_body':'Cuéntanos qué vivienda valoras, qué ahorro tienes y qué punto te preocupa. Te ayudaremos a ordenar el siguiente paso. La revisión inicial no es una aprobación bancaria.',
  'cta_button':'Quiero revisar mi situación',
  'closing':'Gracias por leernos. Nos vemos en tu próxima gran decisión, con menos ruido y más claridad.',
  'urls':{
   'mortgage':('/hipotecas/hipoteca-90/','hipoteca_90'),
   'article':('/antes-de-reservar/','articulo_arras'),
   'tool':('/gastos-compra/','calculadora_gastos'),
   'main':('/pre-ok-hipotecario/','cta_principal'),
   'question':('mailto:hipotecas@fenixcapital.es?subject=Mi%20pregunta%20a%20Hipotecas%20sin%20vueltas','pregunta')
  },
  'image_alt':'Pareja revisando juntos números y documentación de una compra de vivienda en un ambiente cercano.',
 },
 'b2b':{
  'audience':'Inmobiliarias','name':'Operaciones con más claridad',
  'subject':'La operación parecía cerrada. ¿Y la financiación?',
  'preheader':'Tres señales de riesgo, una herramienta para agencias y un Pre-OK para anticiparse.',
  'hero_title':'Hay ventas que se complican cuando todo parecía hecho.',
  'hero_intro':'Lo sabes bien: detrás de una operación hay visitas, llamadas, negociación, expectativas y muchas horas de trabajo. Por eso fastidia tanto descubrir tarde un problema que quizá podía haberse detectado antes.',
  'letter':'Hoy queremos hablarte de algo muy práctico: cómo abordar la financiación del comprador sin convertir a tu agencia en un banco y sin prometer certezas que nadie tiene todavía.',
  'main_title':'El comprador está ilusionado. Pero ¿qué sabemos de su capacidad real?',
  'main_intro':'La pregunta no es cuánto le gustaría pagar, sino qué datos hacen defendible la operación. Antes de fijar una reserva, conviene distinguir interés comercial de financiación contrastada.',
  'semaphore':[
   ('VERDE · Base documental','Hay información inicial sobre ingresos, otras cuotas, ahorro y vivienda; puede iniciarse una revisión, sin dar por aprobada la hipoteca.'),
   ('ÁMBAR · Capacidad','La cuota deseada se calcula sin tener en cuenta otros préstamos, tarjetas o ingresos variables.'),
   ('ROJO · Calendario','Se quiere firmar arras con fechas ajustadas sin tener documentación y revisión de financiación encauzadas.')],
  'main_quote':'Una agencia no tiene que aprobar hipotecas. Tiene que detectar cuándo es el momento de pedir un análisis profesional.',
  'article_title':'Evitar operaciones caídas empieza bastante antes de la firma',
  'article_body':'Hemos reunido señales que suelen desordenar el proceso: ahorro insuficiente, tasación que no encaja, documentos que faltan y plazos que dejan poco margen. La idea es ayudarte a anticiparlas en la conversación comercial.',
  'article_link':'Leer el protocolo práctico',
  'tool_title':'Una calculadora para orientar, no para prometer',
  'tool_body':'Nuestra calculadora de preanálisis ayuda a ordenar precio, ahorro, deuda y cuota estimada. No sustituye al Pre-OK ni autoriza a comunicar al comprador que su hipoteca está aprobada.',
  'tool_link':'Abrir calculadora para agencias',
  'case_title':'La frase que pide una segunda pregunta',
  'case_body':'«El banco ya le ha dicho que sí». Puede significar muchas cosas: una simulación, una consulta previa o un análisis avanzado. Antes de convertir esa frase en fecha de arras, pregunta qué documentos se han revisado y qué condiciones siguen abiertas. No hace falta conocer datos financieros que no correspondan a la agencia.',
  'key_title':'La clave Fénix: derivar pronto también es vender mejor',
  'key_body':'Un preanálisis oportuno no quita protagonismo a tu equipo. Puede proteger la relación comercial, ayudar a ordenar expectativas y permitir que cada profesional trabaje con la información y las competencias que le corresponden.',
  'trust_title':'Así trabajamos junto a una agencia',
  'trust_body':'La agencia mantiene su relación con el comprador. Fénix revisa la parte hipotecaria con autorización y documentación adecuada, explica incidencias sin prometer resultados y comunica los hitos que corresponda compartir. Un método más útil que una respuesta vaga.',
  'question_title':'Nos interesa vuestra experiencia',
  'question':'¿Qué os hace perder más tiempo últimamente: clientes sin ahorro suficiente, documentación incompleta o plazos de arras demasiado ajustados?',
  'question_body':'Cuéntanoslo. Una buena herramienta empieza por un problema de verdad, no por una presentación bonita.',
  'question_link':'Contar el principal problema',
  'cta_title':'¿Tienes un comprador al que conviene revisar antes de seguir?',
  'cta_body':'Cuéntanos lo imprescindible para orientar el siguiente paso. Si hace falta un Pre-OK, coordinaremos la revisión profesional sin interferir en la relación entre tu agencia y el comprador.',
  'cta_button':'Pedir un Pre-OK para mi comprador',
  'closing':'Nos gustan los acuerdos claros y las operaciones bien preparadas. Si tienes un caso sobre la mesa, hablemos.',
  'urls':{
   'article':('/inmobiliarias/evitar-operaciones-caidas/','articulo_operaciones'),
   'tool':('/inmobiliarias/calculadora-preanalisis-hipotecario/','calculadora_b2b'),
   'main':('/inmobiliarias/preok-hipotecario/','cta_preok'),
   'secondary':('/inmobiliarias/formacion-inmobiliarias/','formacion_agencias'),
   'question':('mailto:hipotecas@fenixcapital.es?subject=Pregunta%20de%20inmobiliarias%20a%20Fenix','pregunta')
  },
  'image_alt':'Mesa de trabajo y documentación de una operación inmobiliaria preparada para revisión profesional.',
 }
}

INK='#202321';ORANGE='#FF5F00';LIGHT='#FFF3E8';BEIGE='#F8F3EC';BORDER='#E8E4DE';DIM='#60635E'

def text(s):return html.escape(str(s),quote=True)
def link(kind,k,urlkey):
    raw,tag=D[kind]['urls'][urlkey]
    if raw.startswith('mailto:'):
        assert raw.lower().startswith(('mailto:hipotecas@fenixcapital.es', 'mailto:info@fenixcapital.es')), 'Destinatario de correo no autorizado'
        return raw
    return U(raw,kind,tag)

def p(txt):return f'<p style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.62;color:{INK};margin:0 0 14px;">{text(txt)}</p>'
def small(s):return f'<p style="font-family:Arial,sans-serif;font-size:11px;letter-spacing:1.7px;font-weight:700;color:{ORANGE};margin:0 0 12px;text-transform:uppercase;">{text(s)}</p>'
def h(s):return f'<h2 style="font-family:Georgia,serif;line-height:1.18;font-weight:700;letter-spacing:-.5px;color:{INK};font-size:27px;margin:0 0 18px;">{text(s)}</h2>'
def btn(label,url,light=False):
    bg='#242424' if light else ORANGE
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:24px 0 9px;"><tr><td bgcolor="{bg}" style="background:{bg};border-radius:7px;">'
            f'<a href="{html.escape(url,quote=True)}" style="font-size:14px;font-weight:700;font-family:Arial,Helvetica,sans-serif;line-height:1.3;display:inline-block;color:#FFFFFF;text-decoration:none;padding:16px 25px;">{text(label)} &nbsp;→</a>'
            '</td></tr></table>')
def ll(label,url):return f'<a href="{html.escape(url,quote=True)}" style="color:{ORANGE};text-decoration:underline;font-size:14px;font-weight:700;">{text(label)} →</a>'
def module(code,inner,bg='#FFFFFF',padding=34):
    return f'<tr data-block="{code}"><td bgcolor="{bg}" style="background:{bg};padding:{padding}px 36px;border-bottom:1px solid {BORDER};" class="pad">{inner}</td></tr>'
def banner(txt):return f'<div style="border-left:4px solid {ORANGE};padding:10px 0 10px 17px;margin:19px 0 4px;color:{INK};font-family:Georgia,serif;font-size:19px;line-height:1.38;font-style:italic;">{text(txt)}</div>'
def sectioncard(label,body):return f'<tr><td style="vertical-align:top;padding:7px 0 13px;"><span style="font-family:Arial,sans-serif;color:{ORANGE};font-weight:bold;font-size:17px;">✓</span>&nbsp; <strong style="font-family:Arial,sans-serif;color:{INK};font-size:15px;">{text(label)}</strong><div style="padding:5px 0 0 27px;font-family:Arial,sans-serif;font-size:14px;line-height:1.55;color:{DIM};">{text(body)}</div></td></tr>'

def make(kind='b2c',preview=True):
 c=D[kind];name=c['name'];remainder=[]
 local=lambda fname: '../assets/'+fname
 logo=local('logo-fenix-original.png') if preview else PUBLIC_IMAGE['logo']
 hero=local('hero-'+('particulares' if kind=='b2c' else 'inmobiliarias')+'.jpg') if preview else PUBLIC_IMAGE[kind]
 blocks=[]
 intro=(small(name)+
        f'<h1 style="font-family:Georgia,serif;font-size:40px;line-height:1.11;color:{INK};margin:0 0 17px;letter-spacing:-1.1px;">{text(c["hero_title"])}</h1>'+
        f'<p style="font-size:17px;line-height:1.55;font-family:Arial,sans-serif;color:#4A4A46;margin:0 0 20px;">{text(c["hero_intro"])}</p>'+
        f'<img src="{text(hero)}" width="600" alt="{text(c["image_alt"])}" style="display:block;width:100%;max-width:600px;height:auto;border:0;border-radius:5px;margin:10px 0 22px;"/>'+
        p(c['letter']))
 blocks.append(module('apertura',intro,padding=40))
 if kind=='b2c':
    second=small('El asunto que importa')+h(c['main_title'])+p(c['main_intro'])
    second+='<table role="presentation" style="border-collapse:collapse;width:100%;" cellpadding="0" cellspacing="0">'
    second+=''.join(sectioncard(*pair) for pair in c['checkpoints'])+'</table>'+banner(c['main_quote'])
    blocks.append(module('tema_principal',second,BEIGE))
    third=small('Hipoteca de la semana')+h(c['mortgage_title'])+p(c['mortgage_body'])+ll(c['mortgage_link'],link(kind,kind,'mortgage'))
    blocks.append(module('hipoteca_de_la_semana',third))
    fourth=small('Post de la semana')+h(c['article_title'])+p(c['article_body'])+ll(c['article_link'],link(kind,kind,'article'))
    blocks.append(module('post_de_la_semana',fourth,BEIGE))
    fifth=small('Herramienta que sí ayuda')+h(c['tool_title'])+p(c['tool_body'])+btn(c['tool_link'],link(kind,kind,'tool'))
    blocks.append(module('herramienta',fifth))
    sixth=small('La clave Fénix')+h(c['key_title'])+p(c['key_body'])
    blocks.append(module('la_clave',sixth,BEIGE))
    seventh=small('Una razón para confiar')+h(c['trust_title'])+p(c['trust_body'])
    blocks.append(module('confianza',seventh))
 else:
    second=small('El tema de hoy')+h(c['main_title'])+p(c['main_intro'])+banner(c['main_quote'])
    blocks.append(module('tema_principal',second,BEIGE))
    third=small('Semáforo hipotecario')+h('Señales que conviene revisar antes de comprometer la operación')
    # color describes a caution status; no guarantee of solvency.
    for (label,body) in c['semaphore']:
      dot='#31865A' if 'VERDE' in label else ('#DFA334' if 'ÁMBAR' in label else '#B33226')
      third+=f'<div style="padding:14px 15px;margin:10px 0;border:1px solid {BORDER};border-radius:8px;"><strong style="font-family:Arial,sans-serif;color:{INK};font-size:15px;"><span style="color:{dot};">●</span> &nbsp;{text(label)}</strong><div style="margin-top:7px;font-family:Arial,sans-serif;font-size:14px;line-height:1.58;color:{DIM};">{text(body)}</div></div>'
    blocks.append(module('semaforo_hipotecario',third))
    fourth=small('Post de la semana')+h(c['article_title'])+p(c['article_body'])+ll(c['article_link'],link(kind,kind,'article'))
    blocks.append(module('post_de_la_semana',fourth,BEIGE))
    fifth=small('Recurso para tu equipo')+h(c['tool_title'])+p(c['tool_body'])+btn(c['tool_link'],link(kind,kind,'tool'))
    blocks.append(module('herramienta',fifth))
    sixth=small('Una escena que reconocerás')+h(c['case_title'])+p(c['case_body'])
    blocks.append(module('caso_practico',sixth,BEIGE))
    seventh=small('La clave Fénix')+h(c['key_title'])+p(c['key_body'])
    seventh+='<div style="height:13px;"></div>'+small('Así colaboramos')+p(c['trust_body'])+ll('Ver cómo preparamos a los equipos',link(kind,kind,'secondary'))
    blocks.append(module('confianza',seventh))
 eighth=small('La pregunta de la semana')+h(c['question_title'])+p(c['question'])+p(c['question_body'])+ll(c['question_link'],link(kind,kind,'question'))
 blocks.append(module('pregunta',eighth,BEIGE))
 ninth=(small('Cuando necesites dar el siguiente paso')+h(c['cta_title'])+p(c['cta_body'])+btn(c['cta_button'],link(kind,kind,'main')))
 blocks.append(module('captacion',ninth,'#FCEADD'))
 socials='&nbsp;&nbsp; · &nbsp;&nbsp;'.join(f'<a href="{html.escape(url,quote=True)}" style="font-size:12px;color:#F0F0EE;text-decoration:underline;">{text(platform)}</a>' for platform,url in SOCIAL.items())
 footer=(f'<p style="font:700 17px Arial,sans-serif;color:#FFFFFF;margin:0 0 12px;">FÉNIX CAPITAL</p>'+
  f'<p style="font:14px/1.55 Arial,sans-serif;color:#EDEAE4;margin:0 0 15px;">{text(c["closing"])}</p>'+
  f'<p style="font:13px/1.6 Arial,sans-serif;color:#F0F0EE;margin:0 0 17px;">{socials}</p>'+
  f'<p style="font:11px/1.7 Arial,sans-serif;color:#D0CCC5;margin:0 0 6px;">Recibes este correo porque te has suscrito a las comunicaciones de Fénix Capital.</p>'+
  f'<p style="font:11px/1.7 Arial,sans-serif;color:#D0CCC5;margin:0;">'+
  f'<a href="{{{{ unsubscribe }}}}" style="color:#FFFFFF;text-decoration:underline;">Darse de baja</a> &nbsp;·&nbsp; '+
  f'<a href="{PRIVACY}" style="color:#FFFFFF;text-decoration:underline;">Privacidad</a> &nbsp;·&nbsp; '+
  f'<a href="{LEGAL}" style="color:#FFFFFF;text-decoration:underline;">Aviso legal</a> &nbsp;·&nbsp; '+
  f'<a href="mailto:info@fenixcapital.es" style="color:#FFFFFF;text-decoration:underline;">Contacto</a></p>')
 blocks.append(module('cierre_legal',footer,'#222222'))
 top=(f'<tr><td bgcolor="#FFFFFF" style="padding:23px 36px 24px;text-align:left;border-top:6px solid {ORANGE};" class="pad">'
      f'<table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr><td width="170" valign="middle">'
      f'<a href="{BASE}" aria-label="Fénix Capital"><img src="{text(logo)}" width="150" alt="Fénix Capital" style="width:150px;max-width:150px;height:auto;border:0;display:block;"></a>'
      f'</td><td valign="middle" align="right" style="font:12px/1.35 Arial,sans-serif;color:{DIM};">'+
      ('Una carta para comprar con más claridad.' if kind=='b2c' else 'Ideas prácticas para cuidar cada operación.')+'</td></tr></table></td></tr>')
 doc=(f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
     f'<meta name="viewport" content="width=device-width,initial-scale=1">'
     f'<title>{text(c["subject"])}</title>'
     f'<style>@media screen and (max-width:660px){{.wrap{{width:100%!important;max-width:100%!important}} .pad{{padding:25px 22px!important}} h1{{font-size:32px!important}} h2{{font-size:24px!important}} .small-screen{{font-size:13px!important}}}} @media print{{body{{background:#FFFFFF!important}}.wrap{{border:0!important;box-shadow:none!important}} a{{text-decoration:none!important}}}} </style></head>'
     f'<body style="margin:0;padding:0;background:#F3F1ED;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">'
     f'<span style="display:none!important;visibility:hidden;font-size:1px;color:#F3F1ED;line-height:1px;max-height:0;opacity:0;overflow:hidden;">{text(c["preheader"])}</span>'
     '<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#F3F1ED;"><tr><td align="center" style="padding:20px 10px 34px;">'
     '<table role="presentation" cellpadding="0" cellspacing="0" border="0" class="wrap" width="640" style="width:640px;max-width:640px;background:#FFFFFF;border-collapse:collapse;box-shadow:0 6px 30px rgba(0,0,0,.07);">'
     +top+''.join(blocks)+'</table></td></tr></table></body></html>')
 return doc

def all_visible_text(content):
 soup=BeautifulSoup(content,'html.parser');[z.decompose() for z in soup.select('style')]
 return soup.get_text(' ',strip=True)

def validate(path,kind):
 htm=path.read_text(encoding='utf-8');soup=BeautifulSoup(htm,'html.parser')
 block_names=[t.get('data-block') for t in soup.select('[data-block]')]
 assert len(block_names)==10 and len(set(block_names))==10,(kind,block_names)
 if kind=='b2c':assert 'hipoteca_de_la_semana' in block_names
 if kind=='b2b':assert 'semaforo_hipotecario' in block_names
 visible=all_visible_text(htm)
 banned=r'\b(córdoba|cordoba|andalucía|andalucia|jaén|jaen|sevilla|granada|málaga|malaga|almería|almeria|huelva|cádiz|cadiz|provincia|región|region|edición n[ºo]|n[úu]mero de edición|v[ií]deo de la semana|v[ií]deo semanal)\b'
 assert not re.search(banned,visible,re.I),re.findall(banned,visible,re.I)
 assert '{{ unsubscribe }}' in htm
 assert 'utm_source=brevo' in htm and 'utm_medium=email' in htm
 assert all((img.get('alt') or '') for img in soup.select('img'))
 assert not soup.select('script,iframe,form')
 assert all(a.get('href') and(a['href'].startswith(('https://','mailto:','{{'))) for a in soup.select('a'))
 assert 'testimonio' not in visible.lower() and 'caso real' not in visible.lower()
 # user specifically prohibits visible pink/purple composition
 assert not re.search(r'(#870064|#ec008c|\bfucsia\b|\brosa\b|\bmorado\b|\bmagenta\b)',htm,re.I)
 print(path.name,'OK',len(htm),'bytes',len(visible.split()),'words',len(block_names),'blocks',len(soup.select('a')),'links')
 return {'file':path.name,'html_sha256':hashlib.sha256(htm.encode('utf-8')).hexdigest(),'bytes':len(htm),'word_count':len(visible.split()),'blocks':block_names,'links':len(soup.select('a')),'status':'LAB_PASS'}

def main():
 content_file=ROOT/'motor_contenidos.json'
 if content_file.exists():
  stored=json.loads(content_file.read_text(encoding='utf8'))
  assert stored['engine_id']=='CEREBRO-NEWS-001' and stored['environment']=='LAB'
  assert stored['send_enabled'] is False and stored['publish_enabled'] is False, 'Gate envío debe permanecer cerrado'
  D.update(stored['audiences'])
 results={}
 for kind in ('b2c','b2b'):
  folder=ROOT/kind;folder.mkdir(exist_ok=True)
  a=folder/('newsletter_'+kind+'_previsualizacion.html')
  b=folder/('newsletter_'+kind+'_brevo.html')
  a.write_text(make(kind,True),encoding='utf-8')
  b.write_text(make(kind,False),encoding='utf-8')
  results[kind]={'preview':validate(a,kind),'brevo':validate(b,kind),'subject':D[kind]['subject'],'preheader':D[kind]['preheader']}
 (ROOT/'qa_resultados.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'motor_contenidos.json').write_text(json.dumps({'engine_id':'CEREBRO-NEWS-001','company_id':'fenix-capital','environment':'LAB','version':'0.1.0','publish_enabled':False,'send_enabled':False,'approved':False,'locale':'es-ES','schema':'newsletter_editorial_blocks_v1','assets':PUBLIC_IMAGE,'audiences':D},ensure_ascii=False,indent=2),encoding='utf8')
 print('Generated',results.keys())

if __name__=='__main__':main()