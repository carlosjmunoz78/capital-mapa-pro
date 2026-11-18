#!/usr/bin/env python3
"""NEWS001 · invariant checks for the actual CEREBRO generator, not the rejected mockups."""
import hashlib, json, pathlib, sys, copy
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import crear_newsletters as engine
out=ROOT/"out"
report=json.loads((out/"RESULTADO_PRUEBA.json").read_text(encoding="utf-8"))
assert report["engine_id"]=="CEREBRO-NEWS-001" and report["send_enabled"] is False
assert report["api_called"] is False and report["brevo_campaign_created"] is False
assets={"logo-fenix-original.png":"1b1f234f8f0fb90c50a86749020ea58ffee9fe3a47eff1b70db30a16e9f51e9e","hero-inmobiliarias.jpg":"a99245613258646b28087666351a101467baa7a4bed83ee0c87c2917b5ba3e20","hero-particulares.jpg":"d22d113c3c696ca4ff01cb62136266e7a37a71c666234a1be01afa754d9cc0de"}
for path,digest in assets.items():
 f=ROOT/"assets"/path
 assert f.exists(),f"MISSING_REAL_IMAGE:{path}"
 assert hashlib.sha256(f.read_bytes()).hexdigest()==digest,f"IMAGE_CHANGED:{path}"
for kind in ("b2b","b2c"):
 data=json.loads((ROOT/"motor_contenidos.json").read_text(encoding="utf-8"))
 engine.D=copy.deepcopy(data["audiences"])
 original=engine.make(kind,False)
 soup=BeautifulSoup(original,"html.parser")
 assert len(soup.select("[data-block]"))==10
 assert len(soup.select("img"))==2
 assert len(soup.select("a"))==13
 assert soup.select_one("img[alt='Fénix Capital']")
 assert soup.select_one("img[alt*='vivienda'],img[alt*='inmobiliaria']")
 assert "#FF5F00" in original and "#870064" not in original
 old=engine.D[kind]["hero_title"];engine.D[kind]["hero_title"]="OTRA EDICIÓN DE CEREBRO"
 changed=engine.make(kind,False)
 assert changed!=original and "OTRA EDICIÓN DE CEREBRO" in changed
 assert len(BeautifulSoup(changed,"html.parser").select("[data-block]"))==10
 engine.D[kind]["hero_title"]=old
 html=(out/f"NEWS_FENIX_{kind}_BREVO_BORRADOR.html").read_text(encoding="utf-8")
 assert len(BeautifulSoup(html,"html.parser").select("a"))==13
 assert "{{ unsubscribe }}" in html
 assert report["audiences"][kind]["brevo"]["status"]=="LAB_PASS"
 assert report["audiences"][kind]["brevo"]["html_sha256"]==hashlib.sha256(html.encode()).hexdigest()
 print("CEREBRO_AUTONOMOUS_REPRODUCTION_PASS",kind,"10 blocks 13 links original logo and hero, 2 independent editions")
print("NO_CUSTOMER_SEND_NO_PROD_MUTATIONS")
