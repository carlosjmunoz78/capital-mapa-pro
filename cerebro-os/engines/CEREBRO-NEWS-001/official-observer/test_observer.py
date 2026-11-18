import unittest
from datetime import date
from observer import FEEDS, extract, refresh
NOW=date(2026,11,18)
GOOD='''<rss><channel><item><title>El Banco de España informa de las hipotecas y tipos de interés</title><link>https://www.bde.es/wbe/es/noticias-eventos/actualidad-banco-espana/prueba.html</link><pubDate>Tue, 17 Nov 2026 08:00:00 GMT</pubDate><description><![CDATA[Informe oficial sobre crédito hipotecario y tipos de interés destinado a explicar la información económica de las entidades.]]></description></item></channel></rss>'''
class TestObserver(unittest.TestCase):
 def test_parses_only_official_fresh(self):
  a=extract(GOOD,today=NOW,feed=FEEDS[0]);self.assertEqual(len(a),1);self.assertEqual(a[0]['published_at'],'2026-11-17')
 def test_official_host_required(self):
  s=GOOD.replace('https://www.bde.es/','https://bad.example/');self.assertEqual(extract(s,today=NOW,feed=FEEDS[0]),[])
 def test_stale_news_blocked(self):
  self.assertEqual(extract(GOOD.replace('17 Nov 2026','17 Oct 2026'),today=NOW,feed=FEEDS[0]),[])
 def test_future_news_blocked(self):
  self.assertEqual(extract(GOOD.replace('17 Nov 2026','20 Nov 2026'),today=NOW,feed=FEEDS[0]),[])
 def test_empty_feed_holds(self):
  with self.assertRaisesRegex(RuntimeError,'HOLD_NO_FRESH'):refresh(today=NOW,getter=lambda u:b'<rss><channel/></rss>')
 def test_successful_regenerate(self):
  x=refresh(today=NOW,getter=lambda u:GOOD.encode());self.assertEqual(len(x['items']),1);self.assertEqual(x['verification_policy']['status'],'SOURCE_SNIPPETS_ONLY_PENDING_EDITORIAL_QA')
 def test_untrusted_feed_denied(self):
  with self.assertRaisesRegex(ValueError,'UNAPPROVED'):extract(GOOD,today=NOW,feed='https://bad.example/rss')
 def test_missing_pub_date(self):
  x=GOOD.replace('<pubDate>Tue, 17 Nov 2026 08:00:00 GMT</pubDate>','');self.assertEqual(extract(x,today=NOW,feed=FEEDS[0]),[])
if __name__=='__main__':unittest.main()
