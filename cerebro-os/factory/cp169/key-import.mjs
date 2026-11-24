export function decode(s){if(typeof s!=='string'||s.length>200||!/^[A-Za-z0-9+/]+={0,2}$/.test(s))throw Error('KEY_CONFIGURATION_DENIED');return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}
export async function publicKey(s){const b=decode(s);if(b.length!==32)throw Error('KEY_LENGTH');return crypto.subtle.importKey('raw',b,{name:'Ed25519'},true,['verify']);}
export function privateKey(s){return crypto.subtle.importKey('pkcs8',decode(s),{name:'Ed25519'},false,['sign']);}
