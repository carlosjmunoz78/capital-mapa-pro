// Physical SQLite adapter for separate authority process; atomic state and nonce use.
import {DatabaseSync} from 'node:sqlite';
export function openAuthorityStore(path){
 const db=new DatabaseSync(path);
 db.exec("CREATE TABLE IF NOT EXISTS grants (id TEXT PRIMARY KEY, body TEXT NOT NULL); CREATE TABLE IF NOT EXISTS used_nonces (nonce TEXT PRIMARY KEY, action TEXT NOT NULL, request_id TEXT NOT NULL)");
 const read=db.prepare('SELECT body FROM grants WHERE id=?'),add=db.prepare('INSERT INTO grants(id,body) VALUES (?,?)'),upd=db.prepare('UPDATE grants SET body=? WHERE id=?'),nonce=db.prepare('INSERT INTO used_nonces VALUES(?,?,?)');
 return {close:()=>db.close(),transition(action,id,n,g,t){
   db.exec('BEGIN IMMEDIATE');
   try{
    if(db.prepare('SELECT nonce FROM used_nonces WHERE nonce=?').get(n))throw Error('NONCE_REPLAY');
    const row=read.get(id),current=row?JSON.parse(row.body):null;
    if(action==='issue'){if(row)throw Error('GRANT_ALREADY_EXISTS');add.run(id,JSON.stringify(g));}
    else if(action==='current'){if(!current||current.revoked||!current.active||current.expires_at_epoch<=t)throw Error('GRANT_INACTIVE');}
    else if(action==='revoke'){if(!current)throw Error('GRANT_ABSENT');upd.run(JSON.stringify({...current,active:false,revoked:true}),id);}
    else throw Error('ACTION_DENIED');
    nonce.run(n,action,id);db.exec('COMMIT');return current;
   }catch(e){db.exec('ROLLBACK');throw e;}
 }};
}
