import {raw,type Job} from './match.ts';
export type ListingJob=Job & {employer:string;location:string;education:unknown;major:unknown;recruitment_type?:string;application_end:unknown;open_basis?:string;condition_text:string;evidence_excerpt:string;obtained_at:string};
export type Filters={query:string;education:string[];recruitment:string[];locations:string[];sort:'deadline'|'original'};
export function deadline(job:ListingJob):string|null{const end=job.application_end;if(end&&typeof end==='object'&&'normalized' in end&&typeof end.normalized==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(end.normalized))return end.normalized;return null;}
export function deadlineLabel(job:ListingJob){return deadline(job)||(job.open_basis==='长期招聘'?'长期招聘，无固定截止日期':'公告未载明');}
export function filterJobs(jobs:readonly ListingJob[],filters:Filters){
 const query=filters.query.trim().toLocaleLowerCase();
 const result=jobs.filter(job=>(!query||[job.name,job.employer,job.location].some(v=>v.toLocaleLowerCase().includes(query)))&&(!filters.education.length||filters.education.some(v=>raw(job.education).includes(v)))&&(!filters.recruitment.length||filters.recruitment.includes(job.recruitment_type||'unknown'))&&(!filters.locations.length||filters.locations.includes(job.location)));
 if(filters.sort==='deadline')result.sort((a,b)=>{const da=deadline(a),db=deadline(b);const ga=da?0:a.open_basis==='长期招聘'?1:2;const gb=db?0:b.open_basis==='长期招聘'?1:2;return ga-gb||(da&&db?da.localeCompare(db):0);});
 return result;
}
