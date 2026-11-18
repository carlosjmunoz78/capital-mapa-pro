// Authorized test to owner only; no live list campaigns.
export const OWNER="carlosj.munozcabeza@gmail.com";
export function eligibleTestCampaign(id,c){
 if(![112,113].includes(id)||Number(c?.id)!==id)throw Error("NOT_ALLOWLISTED");
 if(String(c.status||c.campaignStatus).toLowerCase()!=="draft")throw Error("NOT_DRAFT");
 const expected=id===112?17:18;const ids=Array.isArray(c.recipients?.lists)?c.recipients.lists:Array.isArray(c.recipients?.listIds)?c.recipients.listIds:[];
 if(!ids.includes(expected)||ids.some(x=>x!==expected))throw Error("WRONG_RECIPIENT_LIST");
 const h=String(c.htmlContent||"");
 if(h.length<12000||(h.match(/data-block=/g)||[]).length!==10||
 (h.match(/<a(?:\s|>)/gi)||[]).length!==13||(h.match(/<img(?:\s|>)/gi)||[]).length!==2||
 !h.includes("{{ unsubscribe }}"))throw Error("CANONICAL_HTML_MISSING");
 const sender=(c.sender?.email||"").toLowerCase();
 if(sender!=="hipotecas@fenixcapital.es")throw Error("WRONG_SENDER");
 return {id,expected_list_id:expected,authorized_test_email:OWNER,sending_to_contacts:false};
}
