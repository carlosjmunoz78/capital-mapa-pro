#!/usr/bin/env python3
"""One-off, read-only public OSM Overpass estate agency registry extraction.
Attribution required: © OpenStreetMap contributors, ODbL 1.0.
No authenticated APIs, emails sent, paid sources, or CRM writes.
"""
import csv,io,json,re,time,urllib.request,urllib.parse,urllib.error
from collections import Counter,defaultdict
from pathlib import Path
from unicodedata import normalize
def N(v):
 return re.sub(r"[^a-z0-9]+"," ",normalize("NFKD",str(v or "")).encode("ascii","ignore").decode().lower()).strip()
ROOT=Path(__file__).resolve().parents[1]
MUNICIPIOS=ROOT/"data/municipalities_ine_2026_andalucia.csv"
ROWS=list(csv.DictReader(MUNICIPIOS.open(encoding="utf-8")))
P_BY_ZIP={"04":"Almería","11":"Cádiz","14":"Córdoba","18":"Granada","21":"Huelva","23":"Jaén","29":"Málaga","41":"Sevilla"}
INDEX=defaultdict(list)
for m in ROWS:
 INDEX[N(m["municipality"])].append(m)
ALIASES={"jerez":"jerez de la frontera","el puerto de santa maria":"puerto de santa maria el","sotogrande":"san roque","matalascanas":"almonte",
"los guajares":"guajares los","las gabias":"gabias las","la zubia":"zubia la","otura":"villa de otura",
"el viso del alcor":"viso del alcor el","san jose de la rinconada":"rinconada la","guadalcacin":"jerez de la frontera",
"la linea de la concepcion":"linea de la concepcion la","los palacios y villafranca":"palacios y villafranca los",
"zahara de los atunes":"barbate"}
QL='[out:json][timeout:150];area["ISO3166-2"="ES-AN"]["admin_level"="4"]->.and; (nwr["office"="estate_agent"](area.and); nwr["shop"="estate_agent"](area.and); nwr["office"="real_estate_agent"](area.and););out center tags;'
def req(endpoint):
 data=urllib.parse.urlencode({"data":QL}).encode()
 rq=urllib.request.Request(endpoint,data=data,headers={"User-Agent":"FenixCapital-OSM-Research/0.1 (public source; read only)","Accept":"application/json"})
 with urllib.request.urlopen(rq,timeout=175) as resp:
  blob=resp.read(25000000)
 return json.loads(blob)
def main():
 data=None
 for endpoint in ["https://overpass.kumi.systems/api/interpreter","https://overpass-api.de/api/interpreter"]:
  try:
   data=req(endpoint);print("OSM_PROVIDER_OK "+endpoint+" "+str(len(data.get("elements",[]))),flush=True);break
  except Exception as ex:print("OSM_PROVIDER_ERROR "+endpoint+" "+type(ex).__name__+" "+str(ex)[:120],flush=True)
 if not data: print("OSM_TOTAL 0");return
 raw=data["elements"];existing=0;reasons=Counter();unique={}
 for el in raw:
  tags=el.get("tags",{});name=tags.get("name") or tags.get("operator") or ""
  if len(name)<3 or N(name) in {"oficina","estate agent","agencia inmobiliaria"}:reasons["no_name"]+=1;continue
  phone=tags.get("contact:phone") or tags.get("phone") or tags.get("telephone")
  email=tags.get("contact:email") or tags.get("email")
  website=tags.get("contact:website") or tags.get("website")
  if not phone and not email:reasons["no_contact"]+=1;continue
  phone=phone.split(";")[0].strip() if phone else None
  email=email.split(";")[0].strip() if email else None
  website=website.split(";")[0].strip() if website else None
  city=(tags.get("addr:city") or tags.get("addr:municipality") or tags.get("addr:town") or tags.get("addr:place") or "").strip()
  zipc=tags.get("addr:postcode") or ""
  province=P_BY_ZIP.get(str(zipc)[:2])
  if not city:reasons["no_city"]+=1;continue
  key=N(city);key=ALIASES.get(key,key)
  options=INDEX.get(key,[])
  if not options:reasons["city_not_in_catalog"]+=1;continue
  if province:options=[x for x in options if x["province"]==province]
  if len(options)!=1:reasons["ambiguous_province"]+=1;continue
  town=options[0]["municipality"];province=options[0]["province"]
  if not province or province not in P_BY_ZIP.values():continue
  ref=f"https://www.openstreetmap.org/{el['type']}/{el['id']}"
  xy=el.get("center") or el
  r={"name":name,"town":town,"province":province,"phone":phone,"email":email,"website":website,"source":ref,
      "source_license":"© OpenStreetMap contributors, ODbL 1.0","lat":xy.get("lat"),"lon":xy.get("lon")}
  key=(N(name),N(town),N(province))
  if key in unique:
   for prop in ["phone","email","website"]:
    if not unique[key].get(prop) and r.get(prop):unique[key][prop]=r[prop]
  else:unique[key]=r
 for r in unique.values():print("OSM_RECORD "+json.dumps(r,ensure_ascii=False,separators=(",",":")),flush=True)
 print("OSM_TOTAL "+json.dumps({"elements":len(raw),"with_contact_municipalities":len(unique),
  "by_province":dict(Counter(r["province"] for r in unique.values())),
  "municipalities_with_records":len(set((r["town"],r["province"]) for r in unique.values())),
  "excluded_reasons":dict(reasons)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
