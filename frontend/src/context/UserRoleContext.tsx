// context/UserRoleContext.tsx
'use client';
import { createContext, useContext } from 'react';

type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';

const UserRoleContext = createContext<UserRole>('USER');

export function UserRoleProvider({ role, children }: { role: UserRole; children: React.ReactNode }) {
    return <UserRoleContext.Provider value={role}>{children}</UserRoleContext.Provider>;
}

export function useUserRole() {
    return useContext(UserRoleContext);
}