#!/usr/bin/env python3
"""Supplemental one-page UNEXIA member list extractor, postal-code and INE assisted.
One public page, zero paid calls, no email sending, no mutation, historical leads pending validation.
"""
from collections import Counter,defaultdict
from pathlib import Path
import csv,json,re
import collect_public_directories as base
def norm(x):return base.norm(x)
ROOT=Path(__file__).resolve().parents[1]
CSV=ROOT/"data/municipalities_ine_2026_andalucia.csv"
MS=list(csv.DictReader(CSV.open(encoding="utf-8")))
ZIP_TO_PROV={"04":"Almería","11":"Cádiz","14":"Córdoba","18":"Granada","21":"Huelva","23":"Jaén","29":"Málaga","41":"Sevilla"}
CAP_ZIPS={"040":"Almería","110":"Cádiz","140":"Córdoba","180":"Granada","210":"Huelva","230":"Jaén","290":"Málaga","410":"Sevilla"}
ALIASES={"sotogrande":"san roque","aguadulce":"roquetas de mar","la herradura":"almunecar","los palacios y villafranca":"palacios y villafranca los","el ejido":"ejido el","san jose de la rinconada":"rinconada la","matalascanas":"almonte","jerez":"jerez de la frontera","guadalcacin":"jerez de la frontera"}
TOWNS=defaultdict(list)
for m in MS:
 TOWNS[m["province"]].append((norm(m["municipality"]),m["municipality"]))
def locate(blob):
 normtext=norm(blob)
 cp=re.search(r"(?<!\d)(?:c\.?p\.?\s*:?\s*)?([0-4]\d{4})(?!\d)",blob,re.I)
 province=ZIP_TO_PROV.get(cp.group(1)[:2]) if cp else None
 if not province:
  par=re.findall(r"\(\s*(Almer[ií]a|C[aá]diz|C[oó]rdoba|Granada|Huelva|Ja[eé]n|M[aá]laga|Sevilla)\s*\)",blob,re.I)
  if par:
   province=next((v for v in ZIP_TO_PROV.values() if norm(v)==norm(par[-1])),None)
 if not province:
  match=re.search(r"\b(Almer[ií]a|C[aá]diz|C[oó]rdoba|Granada|Huelva|Ja[eé]n|M[aá]laga|Sevilla)\s+Espa[ñn]a",blob,re.I)
  if match:province=next((v for v in ZIP_TO_PROV.values() if norm(v)==norm(match.group(1))),None)
 if not province:return None,None,"NO_PROVINCE"
 # For postal-code addresses, prefer the text after the postal-code marker; else whole address.
 look=norm(blob[cp.end():cp.end()+95]) if cp else normtext
 candidates=[]
 for t,official in TOWNS[province]:
  alt=[t]
  if "," in official:
   parts=[norm(x) for x in official.split(",")]
   if len(parts)==2:alt.append(parts[1]+" "+parts[0])
  for spelling in alt:
   if len(spelling)<4:continue
   hit=re.search(r"(?:^| )"+re.escape(spelling)+r"(?: |$)",look)
   if hit:candidates.append((hit.start(),-len(spelling),official))
 for alias,canon in ALIASES.items():
  hit=re.search(r"(?:^| )"+re.escape(alias)+r"(?: |$)",look)
  if hit:
   off=next((m["municipality"] for m in MS if m["province"]==province and norm(m["municipality"])==canon),None)
   if off:candidates.append((hit.start(),-len(alias),off))
 if candidates:
  candidates.sort()
  return province,candidates[0][2],"MATCH_TEXT"
 if cp and cp.group(1)[:3] in CAP_ZIPS:return province,CAP_ZIPS[cp.group(1)[:3]],"CAPITAL_POSTCODE"
 return province,None,"NO_TOWN"
def main():
 url="https://unexiaandalucia.com/asociados/"
 html=base.download(url)
 if not html:return
 f=base.Flatten();f.feed(html);items=f.items
 ds=[i for i,s in enumerate(items) if re.fullmatch(r"(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[012])/20\d\d",s)]
 output=[];why=Counter()
 for j,i in enumerate(ds):
  name=items[i-1] if i else ""
  seg=items[i+1:ds[j+1]-1 if j+1<len(ds) else len(items)]
  blob=" ".join(seg[:30])
  emails=base.EMAIL.findall(blob)
  phones=base.PHONE.findall(blob)
  if not name or not (emails or phones):why["no_data"]+=1;continue
  prov,town,how=locate(blob)
  if not town:why[how]+=1;continue
  if not prov:why["no_province"]+=1;continue
  if norm(name).startswith(("test ","demo ")):continue
  p=re.sub(r"\D","",phones[0]) if phones else None
  if p and len(p)==9:p="+34"+p
  output.append({"name":name,"province":prov,"town":town,"phone":p,"email":emails[0].lower() if emails else None,
    "website":None,"source":url,"registry":"UNEXIA histórico asociado "+items[i],"location_match":how})
 for z in output:print("UNEXIA_EXTRA "+json.dumps(z,ensure_ascii=False,separators=(",",":")),flush=True)
 print("UNEXIA_EXTRA_TOTAL "+json.dumps({"detected_dates":len(ds),"valid":len(output),"province_counts":dict(Counter(x["province"] for x in output)),"skip":dict(why)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
