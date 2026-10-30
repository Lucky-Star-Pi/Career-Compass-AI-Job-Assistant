import {createHmac,randomBytes,timingSafeEqual} from 'node:crypto';
import type {Profile} from './match';
import {EDUCATIONS,MAJORS,CITIES,CERTIFICATES} from './options';
const globalSecret=globalThis as typeof globalThis & {__careerSecret?:string};
const secret=process.env.PROFILE_COOKIE_SECRET||(globalSecret.__careerSecret??=randomBytes(32).toString('hex'));
export function validProfile(value:unknown):value is Profile {
 if(!value||typeof value!=='object')return false;
 const p=value as Record<string,unknown>;
 if(Object.keys(p).some(k=>!['confirmed','education','major','graduationYear','city','certificates'].includes(k)))return false;
 return typeof p.confirmed==='boolean'&&(p.education===undefined||EDUCATIONS.includes(String(p.education)))&&(p.major===undefined||MAJORS.includes(String(p.major)))&&(p.city===undefined||CITIES.includes(String(p.city)))&&(p.graduationYear===undefined||(Number.isInteger(p.graduationYear)&&Number(p.graduationYear)>=2025&&Number(p.graduationYear)<=2030))&&(p.certificates===undefined||(Array.isArray(p.certificates)&&p.certificates.length<=3&&p.certificates.every(v=>CERTIFICATES.includes(v))));
}
export function sign(profile:Profile){const payload=Buffer.from(JSON.stringify({profile,expires:Date.now()+8*3600_000})).toString('base64url');return payload+'.'+createHmac('sha256',secret).update(payload).digest('base64url');}
export function read(request:Request):Profile {
 try{const token=request.headers.get('cookie')?.split(';').map(x=>x.trim()).find(x=>x.startsWith('career_profile='))?.slice(15);if(!token||token.length>4096)return {confirmed:false};const [payload,sig]=token.split('.');const expected=createHmac('sha256',secret).update(payload).digest();const actual=Buffer.from(sig||'','base64url');if(actual.length!==expected.length||!timingSafeEqual(actual,expected))return {confirmed:false};const value=JSON.parse(Buffer.from(payload,'base64url').toString());return value.expires>Date.now()&&validProfile(value.profile)?value.profile:{confirmed:false};}catch{return {confirmed:false};}
}
