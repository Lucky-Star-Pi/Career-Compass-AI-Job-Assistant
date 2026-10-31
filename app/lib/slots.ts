import {EDUCATIONS,MAJORS,CITIES,CERTIFICATES} from './options.ts';
import type {Profile} from './match.ts';
export const EDUCATION=EDUCATIONS;
export const MAJOR=MAJORS;
export const CITY=CITIES;
export const YEAR=[2025,2026,2027,2028,2029,2030];
export const CERT=CERTIFICATES;
export type ProfileUpdates=Partial<Pick<Profile,'education'|'major'|'city'|'graduationYear'|'certificates'>>;
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
