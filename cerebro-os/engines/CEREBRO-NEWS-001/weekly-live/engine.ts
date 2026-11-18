// CEREBRO NEWS001 standalone editorial: no ChatGPT, no paid AI, zero stale rates.
export const LISTS={hogar:17,pro:18};
export const LOGO="https://fenixcapital.es/wp-content/uploads/2026/10/Logo-Fenix-Capital-oficial-color-completo-scaled-1.png";
const IMG={hogar:"https://fenixcapital.es/wp-content/uploads/2026/10/Fenix-C2B7-Pareja-haciendo-numeros-para-comprar-vivienda.jpg",pro:"https://fenixcapital.es/wp-content/uploads/2026/11/fenix-seo001-52663-cabecera-premium-apoyo-hipotecario-agencias-cordoba.webp"};
const ESC=s=>String(s).replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
const XML=s=>String(s).replace(/^<!\[CDATA\[/,"").replace(/\]\]>$/,"").replace(/<[^>]*>/g,"").replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/\s+/g," ").trim();
const FIELD=(name,item)=>XML((item.match(new RegExp("<"+name+"(?:\\s[^>]*)?>([\\s\\S]*?)<\\/"+name+">","i"))||[])[1]||"");
export function weekOf(d){const x=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()));x.setUTCDate(x.getUTCDate()+4-(x.getUTCDay()||7));const y=x.getUTCFullYear();return y+"-W"+String(Math.ceil((((x-new Date(Date.UTC(y,0,1)))/86400000)+1)/7)).padStart(2,"0");}
export function parseFeed(xml,now){
 if(typeof xml!=="string"||xml.length>1200000)return [];
 const out=[];
 for(const m of xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)){
  const x=m[1],title=FIELD("title",x),url=FIELD("link",x),date=new Date(FIELD("pubDate",x)),age=(now-date)/86400000;
  let u;try{u=new URL(url)}catch{continue}
  if(u.protocol!=="https:"||u.hostname!=="www.bde.es"||u.username||u.password||u.port||!Number.isFinite(age)||age<0||age>21)continue;
  if(!/eur[ií]bor|hipotec|vivienda|pr[eé]stam|cr[eé]dito|financiaci[oó]n|tipos? de inter[eé]s|pol[ií]tica monetaria/i.test(title)||title.length<22||title.length>200)continue;
  if(/cookie|preferencias|privacy|newsletter|AI valuations/i.test(title))continue;
  out.push({title,url,published:date.toISOString().slice(0,10),source:"Banco de España"});
 }
 return out.sort((a,b)=>b.published.localeCompare(a.published)).slice(0,1);
}
export async function headline(fetcher=fetch,now=new Date()){
 const ctrl=new AbortController(),tm=setTimeout(()=>ctrl.abort(),7000);
 try{
  const r=await fetcher("https://www.bde.es/wbe/es/inicio/rss/rss-noticias/",{redirect:"error",signal:ctrl.signal,headers:{"accept":"application/rss+xml, text/xml"}});
  if(!r.ok)return null;
  const u=new URL(r.url||"https://www.bde.es/");if(u.hostname!=="www.bde.es"||u.protocol!=="https:")return null;
  return parseFeed(await r.text(),now)[0]||null;
 }catch{return null}finally{clearTimeout(tm)}
}
const TOPICS=[
 ["Arras","Comprueba tu financiación antes de entregar arras","Financiación y arras: tres controles para tu agencia",
  ["Separa el dinero reservado de los gastos que aún debes pagar.","Distingue una simulación bancaria de un expediente estudiado.","Revisa plazos y consecuencias con asesoramiento adecuado."],
  ["Comprueba qué parte de la financiación está realmente revisada.","Aclara las fechas críticas con comprador y vendedor.","Evita presentar una estimación como una aprobación hipotecaria."]],
 ["Ahorro","El ahorro de una compra no es solo la entrada","El comprador necesita más que una cifra de ahorro",
  ["Distingue precio, impuestos, gastos y reserva personal.","Consulta el coste total antes de comprometer una señal.","No calcules la viabilidad solo con una cuota mensual."],
  ["Comprueba si el comprador incluye gastos e impuestos.","Asegúrate de que entiende los importes pendientes.","Coordina información financiera y calendario comercial."]],
 ["Documentación","Prepara los documentos antes de pedir hipoteca","Documentación que ayuda a evitar retrasos en compraventas",
  ["Organiza tus ingresos y obligaciones financieras.","Comprueba que la documentación está actualizada.","Pregunta qué requiere cada entidad para estudiar tu caso."],
  ["Identifica qué documentos tiene preparados el comprador.","Separa declaraciones verbales de documentos contrastados.","Anota pendientes antes de fijar fechas de firma."]],
 ["Tipos","Tipo fijo o variable: compara con criterios claros","Cómo explicar los tipos hipotecarios sin prometer resultados",
  ["Compara coste total, no solo el interés anunciado.","Pregúntate qué cuota tolerarías si cambian tus circunstancias.","Revisa comisiones y condiciones completas."],
  ["Explica que la noticia económica no es una oferta individual.","Recomienda comparar condiciones escritas y completas.","No confirmes financiación sin estudio de la entidad."]],
 ["Preanálisis","Estudia tu financiación antes de reservar una vivienda","Preanálisis hipotecario: protege la operación a tiempo",
  ["Revisa endeudamiento y capacidad de ahorro.","Calcula los gastos y deja margen para imprevistos.","Distingue preanálisis, oferta y aprobación."],
  ["Plantea una revisión financiera temprana autorizada.","Identifica riesgos antes de las arras.","Protege la confidencialidad de la información del comprador."]],
 ["Compra","Preguntas útiles antes de comprar una vivienda","Una operación sólida empieza con expectativas claras",
  ["¿Qué gastos debo prever además del precio?","¿Qué documentación me pedirá la entidad?","¿Qué cuestiones debo confirmar antes de firmar?"],
  ["¿Comprende el comprador el coste total de la operación?","¿Se ha verificado su capacidad de financiación?","¿Están claros los plazos y los documentos pendientes?"]]
];
const cell=(id,c)=>'<tr data-block="'+id+'"><td style="padding:22px 36px;font:16px/1.6 Arial,sans-serif;color:#222;background:#FFF">'+c+'</td></tr>';
const heading=(s)=>'<h2 style="margin:0 0 12px;font:bold 22px/1.3 Arial,sans-serif;color:#222">'+ESC(s)+'</h2>';
export function render(a,now=new Date(),news=null){
 if(!(a in LISTS))throw Error("AUDIENCE_DENIED");
 const week=weekOf(now),t=TOPICS[(Number(week.slice(-2))-1)%TOPICS.length],pro=a==="pro";
 const brand=pro?"FÉNIX PRO":"FÉNIX HOGAR",title=pro?t[2]:t[1],tips=pro?t[4]:t[3];
 const intro=pro?"Una agencia cuida cada operación cuando la financiación, la documentación y los plazos se revisan a tiempo.":"Comprar vivienda merece una decisión informada. Conviene revisar ahorro, condiciones, documentación y plazos antes de comprometer dinero.";
 const purpose=pro?"El interés del comprador no equivale a financiación aprobada. Una buena coordinación entre agencia, comprador y entidad puede evitar errores.":"Una noticia financiera describe el mercado, pero no garantiza las condiciones de tu hipoteca. La oferta dependerá de tu situación y de cada entidad.";
 const source=news&&news.url?.startsWith("https://www.bde.es/")?news:null;
 const current=source?'<p style="margin:0 0 12px">El Banco de España publicó el '+ESC(source.published)+': <strong>'+ESC(source.title)+'</strong>.</p><p style="margin:0">Consulta la <a style="color:#D94F00" href="'+ESC(source.url)+'">fuente oficial</a>; su titular no determina las condiciones de una operación individual.</p>':
 '<p style="margin:0">Esta edición incluye una <strong>guía práctica</strong> sobre '+ESC(t[0].toLowerCase())+'. No presentamos cifras económicas como actuales cuando no tenemos una noticia oficial pertinente y reciente.</p>';
 const primary=pro?"Hablar de operaciones con Fénix":"Conocer Fénix Capital",url=pro?"https://fenixcapital.es/inmobiliarias/":"https://fenixcapital.es/";
 const question=pro?"¿Sabes qué financiación está realmente estudiada antes de fijar las arras?":"¿Qué te preocupa más: el ahorro, la cuota o entregar arras demasiado pronto?";
 const html='<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+ESC(brand+" | "+title)+'</title></head><body style="margin:0;background:#F4F1ED;-webkit-text-size-adjust:100%"><div style="display:none!important;max-height:0;overflow:hidden;opacity:0">'+ESC(title)+'</div><table role="presentation" cellspacing="0" cellpadding="0" width="100%" style="background:#F4F1ED"><tr><td align="center" style="padding:20px 10px"><table role="presentation" cellspacing="0" cellpadding="0" width="640" style="max-width:640px;width:100%;background:#FFFFFF;border-collapse:collapse">'+[
 cell("marca",'<table role="presentation" width="100%"><tr><td><img src="'+LOGO+'" alt="Fénix Capital" width="156" style="display:block;width:156px;max-width:100%;height:auto;border:0"></td><td align="right" style="font:bold 13px Arial;color:#D94F00">'+brand+'</td></tr></table>'),
 cell("portada",'<p style="font:bold 13px Arial;color:#D94F00;margin:0 0 12px">EDICIÓN SEMANAL · '+week+'</p><h1 style="font:bold 30px/1.25 Arial,sans-serif;color:#222;margin:0 0 15px">'+ESC(title)+'</h1><p style="margin:0">'+intro+'</p>'),
 cell("imagen",'<img src="'+IMG[a]+'" alt="'+(pro?"Asesoramiento hipotecario para agencias":"Compra de vivienda")+'" width="562" style="display:block;width:100%;max-width:562px;height:auto;border:0;border-radius:5px">'),
 cell("actualidad",heading(source?"Actualidad verificada":"El tema de esta semana")+current),
 cell("interpretacion",heading("Qué significa para ti")+'<p style="margin:0">'+purpose+'</p>'),
 cell("checklist",heading("Tres comprobaciones prácticas")+'<ul style="margin:0;padding-left:23px">'+tips.map(x=>'<li style="padding:0 0 9px">'+ESC(x)+'</li>').join("")+'</ul>'),
 cell("aviso",heading("Cuidado con esta confusión")+'<p style="margin:0;color:#C54B00;font-weight:bold">Una simulación o un preanálisis no equivalen a una concesión hipotecaria.</p>'),
 cell("recurso",heading("Qué puedes preparar hoy")+'<p style="margin:0">Ordena tus documentos, gastos, plazos y preguntas pendientes. Anota lo confirmado por escrito y lo que todavía necesita revisión antes de asumir compromisos.</p>'),
 cell("accion",heading("¿Hablamos?")+'<p style="margin:0 0 16px">'+(pro?"Fénix Capital puede apoyar a tu inmobiliaria con orientación hipotecaria, con autorización del comprador y sin prometer aprobaciones.":"Fénix Capital puede ayudarte a ordenar tu situación y las preguntas clave antes de una solicitud hipotecaria, sin prometer aprobaciones.")+'</p><a href="'+url+'" style="display:inline-block;padding:16px 21px;background:#FF5F00;color:#FFFFFF;text-decoration:none;font:bold 15px Arial;border-radius:4px">'+primary+'</a><p style="margin:14px 0 0"><strong>'+question+'</strong></p>'),
 cell("pie",'<div style="font:12px/1.65 Arial,sans-serif;color:#666;border-top:1px solid #ddd;padding-top:14px"><p style="margin:0 0 7px">Fénix Capital · Córdoba · Información general; no oferta vinculante.</p><p style="margin:0 0 7px">Recibes esta newsletter por tu suscripción a las comunicaciones de Fénix Capital.</p><a href="{{ unsubscribe }}" style="color:#D94F00">Darse de baja</a> · <a href="https://fenixcapital.es/declaracion-de-privacidad/" style="color:#666">Privacidad</a> · <a href="mailto:hipotecas@fenixcapital.es" style="color:#666">Contacto</a></div>')
 ].join("")+'</table></td></tr></table></body></html>';
 const blocks=(html.match(/\bdata-block=/g)||[]).length,images=(html.match(/<img /g)||[]).length;
 if(blocks!==10||images!==2||html.length<6500||!html.includes("{{ unsubscribe }}")||!html.includes(LOGO))throw Error("HTML_QA_FAIL_blocks_"+blocks+"_images_"+images+"_chars_"+html.length);
 return {audience:a,listId:LISTS[a],week,name:"NEWS001 CEREBRO AUTO "+a.toUpperCase()+" "+week,subject:"🟠 "+brand+" | "+title,previewText:pro?"Una idea práctica para proteger las operaciones de tu agencia.":"Ideas prácticas para preparar mejor tu compra de vivienda.",htmlContent:html,blocks,images,source:source?{url:source.url,title:source.title,date:source.published}:null};
}
