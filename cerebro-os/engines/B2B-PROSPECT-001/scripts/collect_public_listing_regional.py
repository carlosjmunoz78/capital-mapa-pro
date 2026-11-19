#!/usr/bin/env python3
"""Small, rate-limited, robots-aware public directory regional research batch.
No automated mail, no CRM access, no payments. Only facts from visible published pages.
Source: inmobiliarias.info public province and agency pages. Never assume publishing = approval.
"""
import sys,re,csv,time,json,urllib.request,urllib.robotparser
from pathlib import Path
from urllib.parse import urljoin,urlparse
from collections import Counter
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
BASE="https://inmobiliarias.info"
SOURCE=BASE+"/robots.txt"
AGENT="FenixCapitalPublicDirectoryResearch/0.1 (+research, no-send)"
rp=urllib.robotparser.RobotFileParser()
rp.set_url(SOURCE)
try:
 rp.read();allowed=rp.can_fetch(AGENT,BASE+"/province/malaga/")
 print("DIR_ROBOTS "+str(allowed),flush=True)
except Exception as e:
 print("DIR_ROBOTS_UNAVAILABLE "+str(e)[:150],flush=True)
 sys.exit(0)
if not allowed:sys.exit(0)
delay=max(1.2,rp.crawl_delay(AGENT) or rp.crawl_delay("*") or 1.2)
P=["almeria","cadiz","cordoba","granada","huelva","jaen","malaga","sevilla"]
DISPLAY={"almeria":"Almería","cadiz":"Cádiz","cordoba":"Córdoba","granada":"Granada","huelva":"Huelva","jaen":"Jaén","malaga":"Málaga","sevilla":"Sevilla"}
cities=list(csv.DictReader((ROOT/"data/municipalities_ine_2026_andalucia.csv").open(encoding="utf-8")))
def N(s):
 import unicodedata
 return re.sub(r"[^a-z0-9]+"," ",unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()).strip()
def fetch(url):
 if not url.startswith(BASE+"/") or not rp.can_fetch(AGENT,url):return ""
 time.sleep(delay)
 try:
  rq=urllib.request.Request(url,headers={"User-Agent":AGENT,"Accept-Language":"es-ES,es;q=0.8"})
  with urllib.request.urlopen(rq,timeout=18) as r:
   if r.status!=200:return ""
   b=r.read(1200000)
  return b.decode("utf-8","replace")
 except Exception as e:
  print("DIR_REQUEST_FAILED "+url+" "+type(e).__name__+" "+str(e)[:110],flush=True)
  return ""
def locate(text,province):
 s=N(text)
 candidates=[]
 for c in cities:
  if c["province"]!=province:continue
  town=c["municipality"];name=N(town)
  possibles=[name]
  if "," in town:
   parts=[N(x) for x in town.split(",")]
   if len(parts)==2:possibles.append(parts[1]+" "+parts[0])
  for p in possibles:
   if re.search(r"(?:^| )"+re.escape(p)+r"(?: |$)",s) and p:
    candidates.append((len(p),town))
 candidates.sort(reverse=True)
 return candidates[0][1] if candidates else None
def detail(url,province,fallback_town):
 html=fetch(url)
 if not html:return None
 soup=BeautifulSoup(html,"html.parser")
 main=soup.find("main") or soup
 h=main.find("h1")
 name=h.get_text(" ",strip=True) if h else ""
 name=re.sub(r"^inmobiliaria\s+", "",name,flags=re.I)
 if not 3<=len(name)<=150:return None
 text=main.get_text(" ",strip=True)
 emails=list(dict.fromkeys(a.get("href","")[7:].split("?")[0] for a in main.find_all("a",href=True) if a.get("href","").lower().startswith("mailto:")))
 phones=list(dict.fromkeys(a.get("href","")[4:].split("?")[0] for a in main.find_all("a",href=True) if a.get("href","").lower().startswith("tel:")))
 # Avoid copying generic footer contact emails, only explicit mailto links in company main
 email=emails[0].strip() if emails else None
 phone=phones[0].strip() if phones else None
 if not phone:
  v=re.search(r"(?:Tel[eé]fono|Llamar)[^\d]{0,15}((?:\+34[\s.-]?)?[6789][\d .-]{8,15})",text,re.I)
  if v:phone=v.group(1)
 web=None
 for a in main.find_all("a",href=True):
  href=a["href"]
  if href.startswith("http") and urlparse(href).netloc not in ("inmobiliarias.info","www.inmobiliarias.info") and "instagram.com" not in href and "facebook.com" not in href and "google.com" not in href:
   web=href;break
 town=fallback_town or locate(text,province)
 if not town:return None
 if not (phone or email):return None
 return {"name":name,"province":province,"town":town,"phone":phone,"email":email,"website":web,
  "source":url,"disclaimer":"Public directory, validity not independently verified"}
def main():
 seen=set();records=[];stats=Counter()
 for slug in P:
  prov=DISPLAY[slug];found=[]
  # Bound this one-off scan to 8 pages per province (max 96 entries/province).
  for page in range(1,9):
   url=f"{BASE}/province/{slug}/" if page==1 else f"{BASE}/province/{slug}/page/{page}/"
   html=fetch(url)
   if not html:
    if page==1:print("DIR_SOURCE_SKIPPED "+url,flush=True)
    break
   soup=BeautifulSoup(html,"html.parser");links=[]
   for a in soup.find_all("a",href=True):
    title=a.get_text(" ",strip=True)
    if "Conocer inmobiliaria" not in title:continue
    href=urljoin(url,a["href"]).split("#")[0].rstrip("/")+"/"
    if urlparse(href).netloc not in ("inmobiliarias.info","www.inmobiliarias.info"):continue
    if href in seen:continue
    seen.add(href)
    card=a.find_parent("article") or a.find_parent(class_=re.compile("card|listing|agency",re.I)) or a.parent.parent
    cont=card.get_text(" ",strip=True) if card else ""
    town=locate(cont[:240],prov)
    links.append((href,town))
   if not links:
    if page==1:print("DIR_LISTING_HTML_SAMPLE "+prov+" "+soup.get_text(" ",strip=True)[:400],flush=True)
    break
   found+=links
   if len(links)<12:break
  stats[prov+"_listed"]=len(found)
  # Limit detail fetches to 18 first for fast, minimally invasive sample.
  for url,town in found[:18]:
   x=detail(url,prov,town)
   stats[prov+"_details"]+=1
   if x:records.append(x);print("DIR_RECORD "+json.dumps(x,ensure_ascii=False,separators=(",",":")),flush=True)
  print("DIR_PROGRESS "+json.dumps({"province":prov,"listed":len(found),"details_checked":min(len(found),18),"with_contacts":sum(1 for x in records if x["province"]==prov)},ensure_ascii=False),flush=True)
 print("DIR_SUMMARY "+json.dumps({"extracted":len(records),"checks":dict(stats),"delay_seconds":delay},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
