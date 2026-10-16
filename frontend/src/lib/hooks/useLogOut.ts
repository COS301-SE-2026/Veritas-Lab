import { deleteCookie } from '@/auth/cookie';
import { useRouter } from 'next/navigation';
import { logout } from '@/lib/api/login';
//import { cookies } from 'next/headers'
export const useLogOut = () => {
	const router = useRouter();

	const logOut = async () => {
		try {
			await logout();
		} catch (error) {
			console.error('Error during logout', error);
		}
		await deleteCookie();

		router.replace('/login');
		router.refresh();
	};

	return { logOut };
};