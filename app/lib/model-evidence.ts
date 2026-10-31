import {raw,type Job} from './match.ts';

// Preserve source facts separately from the unchanged eligibility policy.
export function modelFacts(job:Job){
 const end=job.application_end;
 const date=typeof end==='string'?end:end&&typeof end==='object'&&'normalized' in end?end.normalized:undefined;
 return {
  location:job.location||'unknown',
  education:raw(job.education)||'unknown',
  major:raw(job.major)||'unknown',
  batch:job.batch||'unknown',
  open:typeof date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(date)?'截止'+date:job.open_basis==='长期招聘'?'长期招聘，无固定截止日期':'未载明',
 };
}
