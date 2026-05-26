
'use client';

import { useRouter } from 'next/navigation';

export const useLogOut = () => {
  const router = useRouter();

  const logOut = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('authToken');
    }

    router.replace('/login');
    router.refresh();
  };

  return { logOut };
};