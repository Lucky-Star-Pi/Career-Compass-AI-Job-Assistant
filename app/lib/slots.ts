import {EDUCATIONS,MAJORS,CITIES,CERTIFICATES} from './options.ts';
import type {Profile} from './match.ts';
export const EDUCATION=EDUCATIONS;
export const MAJOR=MAJORS;
export const CITY=CITIES;
export const YEAR=[2025,2026,2027,2028,2029,2030];
export const CERT=CERTIFICATES;
export type ProfileUpdates=Partial<Pick<Profile,'education'|'major'|'city'|'graduationYear'|'certificates'>>;
// Conservative local fallback: explicit, unambiguous enum mentions only. It never
// infers absent qualifications; conflicting education/year mentions are omitted.
export function explicitResumeSlots(text:string):ProfileUpdates{
 const value:ProfileUpdates={};
 const one=(values:string[])=>values.length===1?values[0]:undefined;
 value.education=one(EDUCATION.filter(v=>text.includes(v)));
 value.major=one(MAJOR.filter(v=>v!=='其他/待核实'&&text.includes(v)));
 const cities=CITY.filter(v=>v==='不限地区'?text.includes(v):text.includes(v.replace(/市$/,'')));
 value.city=one(cities);
 const years=[...new Set([...text.matchAll(/(20\d{2})\s*(?:届|年毕业)/g)].map(m=>Number(m[1])).filter(y=>YEAR.includes(y)))];
 if(years.length===1)value.graduationYear=years[0];
 const certs=CERT.filter(v=>text.toUpperCase().includes(v.toUpperCase()));if(certs.length)value.certificates=certs;
 return filterProfileUpdates(Object.fromEntries(Object.entries(value).filter(([,v])=>v!==undefined))).profile_updates;
}
export function filterProfileUpdates(value:unknown):{profile_updates:ProfileUpdates;dropped_fields:string[]}{
 const profile_updates:ProfileUpdates={};const dropped_fields:string[]=[];
 if(value===undefined)return {profile_updates,dropped_fields};
 if(!value||typeof value!=='object'||Array.isArray(value))return {profile_updates,dropped_fields:['profile_updates']};
 for(const [key,entry] of Object.entries(value)){
  if(key==='education'&&typeof entry==='string'&&EDUCATION.includes(entry))profile_updates.education=entry;
  else if(key==='major'&&typeof entry==='string'&&MAJOR.includes(entry))profile_updates.major=entry;
  else if(key==='city'&&typeof entry==='string'&&CITY.includes(entry))profile_updates.city=entry;
  else if(key==='graduationYear'&&typeof entry==='number'&&YEAR.includes(entry))profile_updates.graduationYear=entry;
  else if(key==='certificates'&&Array.isArray(entry)){
   const accepted=entry.filter((v):v is string=>typeof v==='string'&&CERT.includes(v));
   if(accepted.length||entry.length===0)profile_updates.certificates=[...new Set(accepted)];
   if(accepted.length!==entry.length)dropped_fields.push(key);
  }else dropped_fields.push(/^[a-zA-Z_]{1,40}$/.test(key)?key:'unknown_field');
 }
 return {profile_updates,dropped_fields:[...new Set(dropped_fields)]};
}
