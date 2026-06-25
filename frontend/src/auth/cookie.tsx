'use server'
import { cookies } from 'next/headers'

export async function getCookie() {
  const cookieStore = await cookies();
  const token = cookieStore.get('JWT_token')?.value;
  if (!token) {
    return "";
  }
  return token;
};

export async function deleteCookie() {
  const cookieStore = await cookies();
  cookieStore.delete('JWT_token');
};
