//user roles context
'use client';
import { createContext, useContext } from 'react';

type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
type CurrentUser = { //added to ensure admin cant delete itself or role change
    id: string;
    username: string;
    role: UserRole;
};

const UserRoleContext = createContext<UserRole>('USER');
const CurrentUserContext = createContext<CurrentUser | null>(null);
export function UserRoleProvider({ user, children }: { user: CurrentUser; children: React.ReactNode }) {
    return (
        <CurrentUserContext.Provider value={user}>
            <UserRoleContext.Provider value={user.role}>{children}</UserRoleContext.Provider>
        </CurrentUserContext.Provider>
    );
}

export function useUserRole() {
    return useContext(UserRoleContext);
}
export function useCurrentUser() {
    return useContext(CurrentUserContext);
}