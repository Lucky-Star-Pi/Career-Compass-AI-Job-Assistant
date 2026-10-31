import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {userFromToken} from '../lib/session';
import JobAssistant from './components/JobAssistant';
export const dynamic='force-dynamic';
export default async function Page(){const user=await userFromToken((await cookies()).get('cc_session')?.value);if(!user)redirect('/login');return <JobAssistant username={user.username} userId={user.userId}/>;}
