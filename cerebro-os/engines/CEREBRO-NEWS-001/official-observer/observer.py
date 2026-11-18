#!/usr/bin/env python3
"""NEWS001 official-source RSS observer. Pure evidence, no recipient data or Brevo calls."""
from __future__ import annotations
import argparse
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = (
    "https://www.bde.es/wbe/es/inicio/rss/rss-noticias/",
    "https://www.ecb.europa.eu/rss/press.html",
)
HOSTS={"www.bde.es","www.ecb.europa.eu"}
TOPIC=re.compile(r"eur[ií]bor|hipotec|vivienda|pr[eé]stam|cr[eé]dito|financiaci[oó]n|tipos? de inter[eé]s|pol[ií]tica monetaria|mortgage|housing|interest rates?|monetary policy",re.I)
BOILERPLATE=re.compile(r"podr[aá]s elegir las [aá]reas|recibir nuestras comunicaciones|pol[ií]tica de cookies|preferencias de privacidad|suscr[ií]bete a nuestras comunicaciones|your cookie preferences|our monetary policy strategy, the tools we use|the impact they have|selecciona tus preferencias|interest to receive our communications|site navigation",re.I)
STRIP=re.compile(r"\s+")
class Text(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.out=[]
    def handle_data(self,s):self.out.append(s)
def pure(s):
    p=Text();p.feed(s or "")
    return STRIP.sub(" ",unescape(" ".join(p.out))).strip()
def official_url(raw):
    p=urllib.parse.urlparse(raw or "")
    return p.scheme=="https" and p.hostname in HOSTS and not p.username and not p.password and p.port is None

class Paragraphs(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.depth=0;self.cur=[]
    def handle_starttag(self,tag,attrs):
        if tag=="p":self.depth+=1;self.cur=[]
    def handle_data(self,data):
        if self.depth:self.cur.append(data)
    def handle_endtag(self,tag):
        if tag=="p" and self.depth:
            value=STRIP.sub(" "," ".join(self.cur)).strip()
            if len(value)>=145 and TOPIC.search(value) and re.search(r"[.!?]\s+",value) and not BOILERPLATE.search(value):self.parts.append(value)
            self.depth=0;self.cur=[]

def page_excerpt(url,getter):
    if not official_url(url) or url.lower().split("?")[0].endswith(".pdf"):return ""
    content=getter(url)
    if len(content)>2_000_000:return ""
    p=Paragraphs();p.feed(content.decode("utf-8","replace") if isinstance(content,bytes) else content)
    return p.parts[0][:390] if p.parts else ""

def extract(xml,*,today:date,feed:str,page_getter=None):
    if feed not in FEEDS:raise ValueError("UNAPPROVED_FEED")
    if len(xml)>2_000_000:raise ValueError("FEED_TOO_LARGE")
    root=ET.fromstring(xml)
    out=[]
    for entry in list(root.findall(".//item"))+list(root.findall(".//{http://www.w3.org/2005/Atom}entry")):
        def field(*tags):
            for t in tags:
                v=entry.findtext(t)
                if v:return v
            return ""
        title=pure(field("title","{http://www.w3.org/2005/Atom}title"))
        desc=pure(field("description","{http://www.w3.org/2005/Atom}summary","{http://www.w3.org/2005/Atom}content"))
        # These official RSS feeds often omit descriptions. Verify the linked article body.

        url=field("link")
        if not url:
            for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
                if link.attrib.get("rel","alternate")=="alternate":url=link.attrib.get("href","");break
        if not official_url(url) or len(title)<15 or not TOPIC.search(title) or BOILERPLATE.search(title):continue
        if len(desc)<36 and page_getter is not None:
            try:desc=page_excerpt(url,page_getter)
            except Exception:desc=""
        stamp=field("pubDate","{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated")
        try:
            dt=datetime.fromisoformat(stamp.replace("Z","+00:00")) if re.match(r"^\d{4}-\d{2}-\d{2}T",stamp) else parsedate_to_datetime(stamp)
            if dt.tzinfo is None:continue
            published=dt.astimezone(timezone.utc).date()
        except (ValueError,TypeError,OverflowError):continue
        if (today-published).days not in range(0,22) or len(desc)<145 or not TOPIC.search(desc) or not re.search(r"[.!?]\s+",desc) or BOILERPLATE.search(desc):continue
        # Literal source text only. Does not establish editorial truth or permit a send.
        out.append({"id":"NEWS001-RSS-"+hashlib.sha256(url.encode()).hexdigest()[:24],
         "title":title[:200],"source_url":url,"source_type":"official_primary",
         "published_at":published.isoformat(),"verified_at":today.isoformat(),
         "audiences":["b2b","b2c"],"facts":[title[:390],desc[:390]]})
    return out

def refresh(*,today:date,getter=None):
    if getter is None:
        def getter(url):
            req=urllib.request.Request(url,headers={"User-Agent":"Fenix-Cerebro-News001/1.0","Accept":"application/rss+xml, application/xml, text/xml"})
            with urllib.request.urlopen(req,timeout=12) as r:
                if not official_url(r.geturl()):raise ValueError("FEED_REDIRECT_NOT_OFFICIAL")
                raw=r.read(2_000_001)
                if len(raw)>2_000_000:raise ValueError("FEED_TOO_LARGE")
                return raw
    found=[]
    for url in FEEDS:
        try:found.extend(extract(getter(url),today=today,feed=url,page_getter=getter))
        except Exception:continue # A failed source does not generate guessed content.
    unique={x["source_url"]:x for x in found}
    items=sorted(unique.values(),key=lambda x:x["published_at"],reverse=True)[:3]
    if not items:raise RuntimeError("HOLD_NO_FRESH_OFFICIAL_RSS_EVIDENCE")
    return {"schema":"cerebro-news-verified-sources-v1","as_of":today.isoformat(),
      "items":items,"verification_policy":{"only_public_official_sources":True,
       "status":"SOURCE_SNIPPETS_ONLY_PENDING_EDITORIAL_QA","no_customer_personal_data":True}}
def main():
    p=argparse.ArgumentParser();p.add_argument("--date",default=date.today().isoformat());p.add_argument("--output",required=True);args=p.parse_args()
    data=refresh(today=date.fromisoformat(args.date))
    Path(args.output).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("NEWS001_OBSERVER_PASS",data["as_of"],len(data["items"]))
if __name__=="__main__":main()
