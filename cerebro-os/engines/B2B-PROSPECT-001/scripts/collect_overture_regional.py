#!/usr/bin/env python3
"""One-pass zero-cost Overture Places extraction for Andalusia (sharded by bbox).
Strictly public data, municipality polygons, business-only leads and no-send.
License: Overture Maps Places (CDLA-Permissive-2.0 / Apache-2.0); no hidden APIs, no writes.
"""
import os,re,csv,json,sys,time,urllib.request,unicodedata
from pathlib import Path
from collections import Counter,defaultdict
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
import shapely.wkb
from overturemaps import record_batch_reader

ROOT=Path(__file__).resolve().parents[1]
M=list(csv.DictReader((ROOT/"data/municipalities_ine_2026_andalucia.csv").open(encoding="utf-8")))
BBOXES={
 "west":(-7.65,35.75,-5.65,38.9),
 "central":(-5.65,35.75,-4.40,38.9),
 "middle":(-4.40,35.75,-3.10,38.9),
 "east":(-3.10,35.75,-1.50,38.9),
}
SHARD=os.environ.get("OSM_BBOX_SHARD","west")
BBOX=BBOXES.get(SHARD)
def norm(s):
 s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().lower()
 return re.sub(r"[^a-z0-9]+"," ",s).strip()
INDEX=defaultdict(list)
for m in M:INDEX[norm(m["municipality"])].append(m)
ALIASES={"el ejido":"ejido el","jerez":"jerez de la frontera","matalascanas":"almonte",
"aguadulce":"roquetas de mar","la herradura":"almunecar","sotogrande":"san roque",
"la linea de la concepcion":"linea de la concepcion la","el puerto de santa maria":"puerto de santa maria el",
"los palacios y villafranca":"palacios y villafranca los","las gabias":"gabias las","la zubia":"zubia la",
"el viso del alcor":"viso del alcor el","guadalcacin":"jerez de la frontera"}
ZIPS={"04":"Almería","11":"Cádiz","14":"Córdoba","18":"Granada","21":"Huelva","23":"Jaén","29":"Málaga","41":"Sevilla"}
def urlread(u):
 rq=urllib.request.Request(u,headers={"User-Agent":"FenixCapital-OpenGeo-LAB/0.2 (no-send)"})
 with urllib.request.urlopen(rq,timeout=90) as r:return r.read(80000000)
def polys():
 try:
  o=json.loads(urlread("https://www.geoboundaries.org/api/current/gbOpen/ESP/ADM3/"))
  g=json.loads(urlread(o.get("simplifiedGeometryGeoJSON") or o["gjDownloadURL"]))
  ps=[];ns=[]
  for f in g["features"]:
   try:p=shape(f["geometry"])
   except Exception:continue
   if p.is_empty or not p.is_valid:continue
   ps.append(p);ns.append(f["properties"].get("shapeName",""))
  print("OVT_POLYGONS "+json.dumps({"n":len(ps),"shard":SHARD}),flush=True)
  return ps,ns,STRtree(ps)
 except Exception as e:
  print("OVT_POLYGON_ERROR "+type(e).__name__+" "+str(e)[:220],flush=True);return None
def locate(name,province):
 key=ALIASES.get(norm(name),norm(name))
 candidates=INDEX.get(key,[])
 if province:candidates=[c for c in candidates if c["province"]==province]
 return candidates[0] if len(candidates)==1 else None
def first(x):
 if isinstance(x,(list,tuple)) and x:return x[0]
 return None
def parse_category(tax,basic,old):
 vals=[]
 if isinstance(tax,dict):
  vals += [str(tax.get("primary") or ""),str(tax.get("hierarchy") or "")]
 if isinstance(old,dict):vals.append(str(old.get("primary") or ""))
 vals.append(str(basic or ""))
 c=" ".join(vals).lower()
 if re.search(r"real_estate|realty|realtor|estate_agent|real_property_broker",c):
  if re.search(r"property_management|real_estate_law|real_estate_appraisal|real_estate_investment",c):return False,c
  return True,c[:170]
 return False,c[:170]
def col(batch,name):
 i=batch.schema.get_field_index(name)
 return batch.column(i).to_pylist() if i>=0 else [None]*batch.num_rows
def main():
 if not BBOX:sys.exit("Unknown shard")
 print("OVT_START "+json.dumps({"bbox":BBOX,"shard":SHARD}),flush=True)
 try:r=record_batch_reader("place",bbox=BBOX)
 except Exception as e:
  print("OVT_READER_ERROR "+type(e).__name__+" "+str(e)[:350],flush=True);return
 if not r:
  print("OVT_EMPTY_READER "+SHARD,flush=True);return
 print("OVT_SCHEMA "+str(r.schema)[:2600].replace("\n"," "),flush=True)
 geo=polys()
 if not geo:
  print("OVT_ABORT_NO_BOUNDARIES",flush=True);return
 geom,names,tree=geo
 c=Counter();found={};scanned=0;started=time.monotonic()
 for batch in r:
  scanned+=batch.num_rows
  tax=col(batch,"taxonomy");basic=col(batch,"basic_category");old=col(batch,"categories")
  selected=[]
  for i in range(batch.num_rows):
   v,category=parse_category(tax[i],basic[i],old[i])
   if v:selected.append((i,category))
  c["category_match"]+=len(selected)
  if not selected:continue
  columns={x:col(batch,x) for x in ("id","names","emails","phones","websites","addresses","geometry","confidence","operating_status")}
  for i,cat in selected:
   if columns["operating_status"][i]=="permanently_closed":c["closed"]+=1;continue
   conf=columns["confidence"][i]
   if conf is not None and float(conf)<0.55:c["low_confidence"]+=1;continue
   a=columns["names"][i] or {};name=(a.get("primary") if isinstance(a,dict) else "") or ""
   if not name or len(name)<3:c["no_name"]+=1;continue
   emails=columns["emails"][i] or [];phones=columns["phones"][i] or [];webs=columns["websites"][i] or []
   if not emails and not phones:c["no_email_phone"]+=1;continue
   addr=first(columns["addresses"][i]) or {}
   if not isinstance(addr,dict):addr={}
   if addr.get("country") not in (None,"ES"):c["outside_spain"]+=1;continue
   province=ZIPS.get(str(addr.get("postcode") or "")[:2])
   loc=locate(addr.get("locality"),province)
   point=None
   if loc is None:
    wkb=columns["geometry"][i]
    try:
     point=shapely.wkb.loads(wkb)
     if point.is_empty or point.geom_type!="Point":continue
     ids=tree.query(point)
     for z in ids:
      if geom[int(z)].covers(point):
       v=locate(names[int(z)],province)
       if v:loc=v;break
    except Exception:
     c["geometry_error"]+=1;continue
   if loc is None:c["no_municipal_match"]+=1;continue
   if point is None:
    try:point=shapely.wkb.loads(columns["geometry"][i])
    except Exception:point=None
   tel=re.sub(r"\D","",str(first(phones) or ""))
   if tel.startswith("34") and len(tel)==11:tel=tel[2:]
   phone="+34"+tel if len(tel)==9 and tel[0] in "6789" else None
   email=str(first(emails) or "").strip().lower()
   if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}",email):email=None
   if not email and not phone:c["bad_contacts"]+=1;continue
   eid=columns["id"][i]
   record={"name":name,"province":loc["province"],"town":loc["municipality"],"ine_code":loc["ine_code"],
       "phone":phone,"email":email,"website":first(webs),"source":"https://explore.overturemaps.org/",
       "overture_id":eid,"category":cat,"confidence":conf,
       "lat":point.y if point is not None else None,"lon":point.x if point is not None else None,
       "license":"Overture Places CDLA-Permissive-2.0/Apache-2.0"}
   key=(norm(record["province"]),norm(record["town"]),norm(name),phone or email or "")
   if key not in found:found[key]=record
  if scanned%40000<batch.num_rows:
   print("OVT_PROGRESS "+json.dumps({"shard":SHARD,"scanned":scanned,"agency_candidates":len(found),"elapsed_s":round(time.monotonic()-started,1)}),flush=True)
 for item in found.values():print("OVT_RECORD "+json.dumps(item,ensure_ascii=False,separators=(",",":")),flush=True)
 print("OVT_SUMMARY "+json.dumps({"shard":SHARD,"total_places_scanned":scanned,"new_candidates":len(found),"towns":len({x["ine_code"] for x in found.values()}),"provinces":dict(Counter(x["province"] for x in found.values())),"diagnostics":dict(c),"elapsed":round(time.monotonic()-started,1)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
