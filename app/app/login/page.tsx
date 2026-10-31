import LoginForm from '../components/LoginForm';
import {cookies} from 'next/headers';
import {redirect} from 'next/navigation';
import {userFromToken} from '../../lib/session';
export const dynamic='force-dynamic';
export default async function LoginPage(){const user=await userFromToken((await cookies()).get('cc_session')?.value);if(user)redirect('/');return <LoginForm/>;}
