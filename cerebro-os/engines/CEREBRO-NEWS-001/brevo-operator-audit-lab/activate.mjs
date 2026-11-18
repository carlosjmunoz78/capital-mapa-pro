// Gate for activating *email templates only*. This does NOT activate any automation or send.
export function eligibleTemplate(id,t){
 if(![114,115].includes(id)||Number(t?.id)!==id)throw Error("TEMPLATE_ID_NOT_ALLOWED");
 const html=String(t?.htmlContent||"");
 if(t.isActive===true)return {already_active:true,id};
 if(t.isActive!==false)throw Error("TEMPLATE_STATE_UNKNOWN");
 if(!t.sender?.email||t.sender.email.toLowerCase()!=="hipotecas@fenixcapital.es")throw Error("SENDER_NOT_VERIFIED");
 if((html.match(/data-block=/g)||[]).length!==10||
 (html.match(/<a(?:\s|>)/gi)||[]).length!==13||
 (html.match(/<img(?:\s|>)/gi)||[]).length!==2||
 !html.includes("{{ unsubscribe }}")||
 html.length<12000||
 /<script\b|data:image\/|javascript:/i.test(html))throw Error("FULL_BRAND_HTML_QA_NOT_GREEN");
 return {already_active:false,id};
}
