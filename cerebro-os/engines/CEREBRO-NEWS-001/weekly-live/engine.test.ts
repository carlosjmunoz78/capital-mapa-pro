import {render,parseFeed,weekOf} from "./engine.ts";
const now=new Date("2026-11-18T20:00:00Z");
Deno.test("two editions maintain brand and exact lists",()=>{
 const a=render("pro",now),b=render("hogar",now);
 if(a.listId!==18||b.listId!==17||a.subject===b.subject)throw Error("AUDIENCE_MISMATCH");
 for(const x of [a,b])if(x.blocks!==10||x.images!==2||!x.htmlContent.includes("{{ unsubscribe }}")||!x.htmlContent.includes("Logo-Fenix"))throw Error("QA_FAILED");
});
Deno.test("evergreen content never invents economic rates",()=>{
 const x=render("hogar",now);
 if(!x.htmlContent.includes("guía práctica")||/euríbor.{0,20}\d,\d+ %/i.test(x.htmlContent))throw Error("FALSE_RATE");
});
Deno.test("official Spanish RSS only valid host and recent dates",()=>{
 const x="<rss><item><title>Hipotecas y tipos de interés publicados por el Banco de España</title><link>https://www.bde.es/wbe/es/noticia.html</link><pubDate>Tue, 17 Nov 2026 10:00:00 GMT</pubDate></item></rss>";
 if(parseFeed(x,now).length!==1||parseFeed(x.replace("www.bde.es","fake.example"),now).length!==0||parseFeed(x.replace("17 Nov","17 Oct"),now).length!==0)throw Error("RSS_GATE_FAILED");
});
Deno.test("ISO week verifies 2026-W47",()=>{if(weekOf(now)!=="2026-W47")throw Error("WEEK_BAD");});
