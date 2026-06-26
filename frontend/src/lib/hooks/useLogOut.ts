import { deleteCookie } from '@/auth/cookie';
import { useRouter } from 'next/navigation';
//import { cookies } from 'next/headers'
export const useLogOut = () => {
  const router = useRouter();

  const logOut = async () => {
    await deleteCookie();

    router.replace('/login');
    router.refresh();
  };

  return { logOut };
};