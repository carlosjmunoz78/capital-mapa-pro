#!/usr/bin/env python3
"""LAB one-off extractor for public Andalusian corporate real-estate directory pages.
Read-only network requests. Does not send email, connect to CRM, or modify production.
Source URLs and provenance are retained; never treat a published address as permission to market.
"""
import json
import re
import time
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urlsplit

P = ["Almería","Cádiz","Córdoba","Granada","Huelva","Jaén","Málaga","Sevilla"]
P_BY_CODE = {"AL":"Almería","CA":"Cádiz","CO":"Córdoba","GR":"Granada","HU":"Huelva","JA":"Jaén","MA":"Málaga","SE":"Sevilla"}
CANON = {"almeria":"Almería","cadiz":"Cádiz","cordoba":"Córdoba","granada":"Granada","huelva":"Huelva","jaen":"Jaén","malaga":"Málaga","sevilla":"Sevilla"}
EMAIL = re.compile(r"(?<![A-Za-z0-9._%+-])[\w.+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+34[\s.-]*)?([6789]\d{2}[\s.-]*\d{3}[\s.-]*\d{3})(?!\d)")
ZIP_TOWN = re.compile(r"(?:CP:\s*)?(\d{5})\s*[,;:\-]?\s*([A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'\-]{2,70}?)\s*\(\s*(Almería|Cádiz|Córdoba|Granada|Huelva|Jaén|Málaga|Sevilla)\s*\)", re.I)
def norm(s):
 import unicodedata
 return re.sub(r"[^a-z0-9]+"," ",unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()).strip()
class Flatten(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True); self.items=[]; self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ("script","style","noscript"): self.skip+=1
 def handle_endtag(self,tag):
  if tag in ("script","style","noscript"): self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if self.skip:return
  txt=" ".join(data.split())
  if txt:self.items.append(txt)
def download(url):
 host=urlsplit(url).netloc
 agent="Mozilla/5.0 (compatible; B2BProspectResearch/1.0)"
 roboturl="https://"+host+"/robots.txt"
 rp=urllib.robotparser.RobotFileParser(); rp.set_url(roboturl)
 try:
  rp.read()
  if not rp.can_fetch(agent,url):
   print("B2B_SOURCE_SKIPPED_ROBOTS "+url,flush=True)
   return ""
 except Exception as e:
  print("B2B_ROBOTS_CHECK_ERROR "+type(e).__name__,flush=True)
 try:
  req=urllib.request.Request(url,headers={"User-Agent":agent,"Accept-Language":"es-ES,es;q=0.9"})
  with urllib.request.urlopen(req,timeout=35) as resp:
   page=resp.read(16000000)
   charset=resp.headers.get_content_charset() or "utf-8"
   text=page.decode(charset,errors="replace")
   print("B2B_FETCH_OK "+host+" "+str(len(page)),flush=True)
   return text
 except Exception as e:
  print("B2B_FETCH_FAILED "+host+" "+type(e).__name__+" "+str(e)[:160],flush=True)
  return ""
def rows_api(html,url):
 f=Flatten(); f.feed(html);items=f.items
 idx=[i for i,s in enumerate(items) if re.search(r"N[uú]m\.?\s*Colegiado",s,re.I)]
 rows=[]
 for step,i in enumerate(idx):
  name=items[i-1] if i else ""
  if not name or norm(name).startswith("num colegiado") or len(name)>120: continue
  start=i+1; end=(idx[step+1]-1 if step+1<len(idx) else len(items))
  block=items[start:min(end,start+32)]
  blob=" | ".join(block)
  emails=EMAIL.findall(blob); phones=PHONE.findall(blob)
  zipmatch=ZIP_TOWN.search(blob)
  prov=None;town=None
  if zipmatch: town=zipmatch.group(2).strip(" -.,");prov=next((p for p in P if norm(p)==norm(zipmatch.group(3))),None)
  if not prov:
   v=re.search(r"([A-Z]{2})\s*\d+",items[i])
   if v:prov=P_BY_CODE.get(v.group(1).upper())
  if not prov: continue
  if not town:
   addr=re.search(r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ -]{2,50})\s*\(\s*"+re.escape(prov)+r"\s*\)",blob,re.I)
   if addr:town=addr.group(1).split(",")[-1].strip()
  if not town:town=prov
  if norm(town) in {"madrid","valencia","barcelona"}:continue
  ph=(re.sub(r"\D","",phones[0]) if phones else None)
  if ph and len(ph)==9:ph="+34"+ph
  websites=re.findall(r"\b(?:https?://)?www\.[a-z0-9][\w.-]*\.[a-z]{2,}(?:/[^\s|]*)?",blob,re.I)
  website=websites[0] if websites else None
  if website and not website.startswith("http"):website="https://"+website
  rows.append({"name":name,"province":prov,"town":town,"phone":ph,"email":emails[0].lower() if emails else None,"website":website,"source":url,"registry":items[i]})
 return rows,len(idx),items[:35]
def rows_unexia(html,url):
 f=Flatten();f.feed(html);items=f.items
 inds=[i for i,s in enumerate(items) if re.fullmatch(r"(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[012])/20\d\d",s)]
 rows=[]
 for j,i in enumerate(inds):
  name=items[i-1] if i else ""
  block=items[i+1:(inds[j+1]-1 if j+1<len(inds) else len(items))]
  blob=" ".join(block[:25])
  if not name or len(name)>130:continue
  emails=EMAIL.findall(blob)
  phones=PHONE.findall(blob)
  prov=None;town=None
  m=re.search(r"\b(\d{5})\s+([\wÁÉÍÓÚÜÑáéíóúüñ .\-]+?)\s+(ALMER[IÍ]A|C[AÁ]DIZ|C[OÓ]RDOBA|GRANADA|HUELVA|JA[EÉ]N|M[AÁ]LAGA|SEVILLA)\s+Espa[ñn]a",blob,re.I)
  if m:town=m.group(2).strip(" .,");prov=CANON.get(norm(m.group(3)))
  if not prov:
   for p in P:
    if re.search(r"\b"+re.escape(p)+r"\s+Espa[ñn]a\b",blob,re.I):prov=p;town=p;break
  if not prov:continue
  ph=re.sub(r"\D","",phones[0]) if phones else None
  if ph and len(ph)==9:ph="+34"+ph
  if not emails and not ph:continue
  rows.append({"name":name,"province":prov,"town":town or prov,"phone":ph,"email":emails[0].lower() if emails else None,"website":None,"source":url,"registry":"UNEXIA asociado (fuente pública)"})
 return rows,len(inds),items[:24]
def main():
 sources=[
  ("api","https://www.andaluciaviviendas.es/localiza-tu-api-portal-inmobiliario-api-andalucia.html"),
  ("unexia","https://unexiaandalucia.com/asociados/")]
 allrows=[]
 for kind,url in sources:
  h=download(url)
  if not h:continue
  results,detected,preview=(rows_api(h,url) if kind=="api" else rows_unexia(h,url))
  print("B2B_PARSED_SOURCE "+json.dumps({"kind":kind,"detected":detected,"rows":len(results),"sample":results[:2],"text_head":preview[:8]},ensure_ascii=False),flush=True)
  allrows+=results
  time.sleep(1)
 unique={}
 for r in allrows:
  if "salinas" in norm(r["name"]):continue
  k=(norm(r["province"]),norm(r["town"]),norm(r["name"]))
  if not k[0] or not k[2]:continue
  if k not in unique: unique[k]=r
  else:
   z=unique[k]
   for prop in ("phone","email","website"):
    if not z[prop] and r[prop]:z[prop]=r[prop]
 for r in unique.values():print("B2B_RECORD "+json.dumps(r,ensure_ascii=False,separators=(",",":")),flush=True)
 print("B2B_TOTAL "+json.dumps({"raw":len(allrows),"deduped":len(unique),"by_province":{p:sum(1 for r in unique.values() if r["province"]==p) for p in P}},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
