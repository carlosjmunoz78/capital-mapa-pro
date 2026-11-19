#!/usr/bin/env python3
"""B2B-PROSPECT-001: One-shot read-only public OSM regional extract, with optional geoBoundaries.
DO NOT mutate CRM, send mail, access Brevo, use paid APIs, or fabricate no-agency statements.
Provenance © OpenStreetMap contributors ODbL. geoBoundaries boundaries used for geographic matching.
"""
import os,io,csv,re,json,time,sys,urllib.request,urllib.parse,unicodedata
from pathlib import Path
from collections import defaultdict,Counter
import osmium
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1]
PBF=Path(os.environ.get("OSM_PBF_PATH","/tmp/andalucia-b2b-lab.osm.pbf"))
CSV=ROOT/"data/municipalities_ine_2026_andalucia.csv"
BASE="https://download.geofabrik.de/europe/spain/andalucia-latest.osm.pbf"
GEO="https://www.geoboundaries.org/api/current/gbOpen/ESP/ADM3/"
def norm(s):
 s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",s).strip()
aliases={
 "jerez":"jerez de la frontera","el puerto de santa maria":"puerto de santa maria el",
 "sotogrande":"san roque","matalascanas":"almonte","la herradura":"almunecar",
 "los guajares":"guajares los","las gabias":"gabias las","la zubia":"zubia la",
 "el viso del alcor":"viso del alcor el","san jose de la rinconada":"rinconada la",
 "aguadulce":"roquetas de mar","el ejido":"ejido el","guadalcacin":"jerez de la frontera",
 "la linea de la concepcion":"linea de la concepcion la","zahara de los atunes":"barbate",
 "los palacios y villafranca":"palacios y villafranca los","cortijos nuevos":"segura de la sierra",
}
official=list(csv.DictReader(CSV.open(encoding="utf-8")))
bytown=defaultdict(list)
provinces={"04":"Almería","11":"Cádiz","14":"Córdoba","18":"Granada","21":"Huelva","23":"Jaén","29":"Málaga","41":"Sevilla"}
for x in official:bytown[norm(x["municipality"])].append(x)
def resolve_town(name,prov=None):
 n=aliases.get(norm(name),norm(name))
 hits=bytown.get(n,[])
 if prov:hits=[x for x in hits if x["province"]==prov]
 return hits[0] if len(hits)==1 else None
def fetch(url,maxbytes=250000000,timeout=90):
 req=urllib.request.Request(url,headers={"User-Agent":"FenixCapital-B2B-LAB/0.2 (public research, no-send)","Accept":"application/json,*/*"})
 with urllib.request.urlopen(req,timeout=timeout) as r:return r.read(maxbytes)
class Agency(osmium.SimpleHandler):
 def __init__(self):
  super().__init__();self.items=[];self.seen=set();self.c=Counter()
 def collect(self,o,t,pos):
  office=t.get("office","");shop=t.get("shop","")
  if not (office in ("estate_agent","real_estate_agent") or shop=="estate_agent" or t.get("real_estate") in ("agency","agent")):return
  self.c["found"]+=1
  name=t.get("name") or t.get("brand") or t.get("operator") or ""
  if len(name.strip())<3:self.c["no_name"]+=1;return
  email=t.get("contact:email") or t.get("email") or t.get("contact:mail") or None
  phone=t.get("contact:phone") or t.get("phone") or t.get("telephone") or t.get("mobile") or None
  web=t.get("contact:website") or t.get("website") or t.get("url") or None
  if not (email or phone or web):self.c["no_contact_or_web"]+=1;return
  etype="node" if o.is_node() else "way" if o.is_way() else "relation"
  url=f"https://www.openstreetmap.org/{etype}/{o.id}"
  if url in self.seen:return
  self.seen.add(url)
  city=t.get("addr:city") or t.get("addr:municipality") or t.get("addr:town") or t.get("addr:place") or ""
  zipc=t.get("addr:postcode") or ""
  if email:email=email.split(";")[0].strip().lower()
  if phone:phone=phone.split(";")[0].strip()
  if web:web=web.split(";")[0].strip()
  self.items.append({"name":str(name).strip(),"email":email,"phone":phone,"website":web,"city_tag":city,"postcode":zipc,
    "lat":pos[0],"lon":pos[1],"source":url,"osm_timestamp":str(o.timestamp)[:10] if o.timestamp else None,
    "tags_business": {"office":office,"shop":shop}})
 def node(self,o):
  try:
   if o.location.valid():self.collect(o,o.tags,(o.location.lat,o.location.lon))
  except Exception:self.c["node_loc_error"]+=1
 def way(self,o):
  try:
   a=[x for x in o.nodes if x.location.valid()]
   if a:
    lat=sum(x.location.lat for x in a)/len(a);lon=sum(x.location.lon for x in a)/len(a)
    self.collect(o,o.tags,(lat,lon))
  except Exception:self.c["way_loc_error"]+=1
 def relation(self,o):pass
def polygon_index():
 try:
  meta=json.loads(fetch(GEO,timeout=35))
  print("B2B_BOUNDARY_META "+json.dumps({"admUnitCount":meta.get("admUnitCount"),"url":meta.get("gjDownloadURL")},ensure_ascii=False),flush=True)
  u=meta.get("simplifiedGeometryGeoJSON") or meta.get("gjDownloadURL")
  if not u:raise ValueError("Missing gjDownloadURL")
  js=json.loads(fetch(u,80000000,90))
  polygons=[];names=[]
  for item in js.get("features",[]):
   t=item.get("properties",{})
   town=t.get("shapeName") or t.get("name") or t.get("NAMEUNIT") or t.get("NAME") or ""
   try:geom=shape(item["geometry"])
   except Exception:continue
   if geom.is_empty or not geom.is_valid:continue
   polygons.append(geom);names.append(town)
  tree=STRtree(polygons)
  print("B2B_BOUNDARIES_LOADED "+json.dumps({"geometries":len(polygons),"first_properties":js["features"][0].get("properties",{}) if js.get("features") else {}},ensure_ascii=False),flush=True)
  return polygons,names,tree
 except Exception as e:
  print("B2B_BOUNDARY_FAILED "+type(e).__name__+" "+str(e)[:350],flush=True);return None
def main():
 start=time.monotonic()
 if not PBF.exists():
  print("B2B_DOWNLOAD_START "+BASE,flush=True)
  req=urllib.request.Request(BASE,headers={"User-Agent":"FenixCapital-B2B-LAB/0.2 (OpenStreetMap open research, no-send)"})
  try:
   with urllib.request.urlopen(req,timeout=180) as f, PBF.open("wb") as out:
    size=0
    while True:
     block=f.read(1024*1024)
     if not block:break
     out.write(block);size+=len(block)
     if size>500000000:raise ValueError("PBF >500 MB limit")
   print("B2B_DOWNLOAD_OK "+str(size),flush=True)
  except Exception as e:
   print("B2B_DOWNLOAD_ERROR "+type(e).__name__+" "+str(e)[:400],flush=True);return
 polygons=polygon_index()
 hand=Agency()
 print("B2B_PBF_PROCESS_START",flush=True)
 hand.apply_file(str(PBF),locations=True)
 print("B2B_PBF_PROCESS_DONE "+json.dumps({"selected":len(hand.items),"counts":dict(hand.c),"seconds":round(time.monotonic()-start,2)}),flush=True)
 results=[];errors=Counter()
 for r in hand.items:
  province=provinces.get(str(r["postcode"])[:2])
  match=resolve_town(r["city_tag"],province)
  method="ADDR_CITY" if match else None
  if not match and polygons:
   poly,names,tree=polygons
   p=Point(r["lon"],r["lat"])
   try:
    candidates=tree.query(p)
    for idx in candidates:
     if poly[int(idx)].covers(p):
      boundaryname=names[int(idx)]
      match=resolve_town(boundaryname,province)
      if match:method="GEO_BOUNDARY";break
   except Exception as e:errors["polygon_error"]+=1
  if not match:
   errors["no_verified_municipality"]+=1
   continue
  if r["email"] and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}",r["email"]):r["email"]=None
  tel=re.sub(r"\D","",r["phone"] or "")
  if tel.startswith("34") and len(tel)==11:tel=tel[2:]
  if len(tel)!=9 or tel[0] not in "6789":r["phone"]=None
  else:r["phone"]="+34"+tel
  if not (r["phone"] or r["email"]):errors["no_phone_email"]+=1;continue
  r.update({"province":match["province"],"town":match["municipality"],"ine_code":match["ine_code"],"match":method,
           "license":"© OpenStreetMap contributors, ODbL 1.0"})
  results.append(r)
 # avoid importing same brand office twice within municipality if phone/email matches
 unique={}
 for r in results:
  k=(norm(r["province"]),norm(r["town"]),norm(r["name"]),r["phone"] or r["email"] or "")
  if k not in unique:unique[k]=r
 for r in unique.values():print("B2B_GEOFABRIK_RECORD "+json.dumps(r,ensure_ascii=False,separators=(",",":")),flush=True)
 print("B2B_GEOFABRIK_SUMMARY "+json.dumps({"totalPbfElements":hand.c["found"],"selectedWithContactOrWeb":len(hand.items),
  "validBeforeDedupe":len(results),"uniqueBusinesses":len(unique),"municipalitiesRepresented":len({x["ine_code"] for x in unique.values()}),
  "byProvince":dict(Counter(x["province"] for x in unique.values())),"errors":dict(errors),"seconds":round(time.monotonic()-start,2)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
