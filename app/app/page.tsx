import {cookies} from 'next/headers';
import {userFromToken} from '../lib/session';
import {getData} from '../lib/user-store';
import jobs from '../lib/jobs.json';
import type {Profile} from '../lib/match';
import JobList from './components/JobList';
export const dynamic='force-dynamic';
export default async function Page(){let user:Awaited<ReturnType<typeof userFromToken>>=null;let profile:Profile|null=null;try{user=await userFromToken((await cookies()).get('cc_session')?.value);if(user)profile=(await getData(user.userId)).profile;}catch{user=null;profile=null;}return <JobList jobs={jobs} initialUser={user} initialProfile={profile}/>;}
