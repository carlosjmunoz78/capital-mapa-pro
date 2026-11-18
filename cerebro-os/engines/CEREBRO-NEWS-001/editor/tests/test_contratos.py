#!/usr/bin/env python3
"""Negative and positive QA for standalone editor. Does not use network, secrets or contacts."""
import sys, tempfile, pathlib, json, copy
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import crear_newsletters as n
from bs4 import BeautifulSoup
count=0

def test(name,fn):
 global count
 fn();count+=1;print('PASS',name)

def rejects(fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):return
 raise AssertionError('Rejection not enforced')

def safe(tmp,kind):
 pathlib.Path(tmp).write_text(n.make(kind,preview=False),encoding='utf-8')
 return n.validate(pathlib.Path(tmp),kind)

for audience in ('b2c','b2b'):
 with tempfile.NamedTemporaryFile(suffix='.html') as f:
  test('valid '+audience,lambda:safe(f.name,audience))
  def inject_geo():
   original=n.D[audience]['hero_title']
   n.D[audience]['hero_title']='Oferta en Córdoba'
   try:safe(f.name,audience)
   finally:n.D[audience]['hero_title']=original
  test('reject geography '+audience,lambda:rejects(inject_geo))
  def inject_video():
   original=n.D[audience]['hero_title']
   n.D[audience]['hero_title']='Vídeo de la semana'
   try:safe(f.name,audience)
   finally:n.D[audience]['hero_title']=original
  test('reject video '+audience,lambda:rejects(inject_video))

test('reject off-domain URL',lambda:rejects(lambda:n.U('https://example.org/fake','b2c','hijack')))
test('reject malformed relative URL',lambda:rejects(lambda:n.U('//example.org/fake','b2b','hijack')))

def escaping():
 o=n.D['b2c']['hero_title'];n.D['b2c']['hero_title']='<script>alert(1)</script>'
 try:
  h=n.make('b2c',preview=False)
  assert '<script>alert(1)</script>' not in h and '&lt;script&gt;' in h
 finally:n.D['b2c']['hero_title']=o

test('html escaping',escaping)
print('TOTAL PASS',count)