import Sidebar from '@/components/common/sidebar';
import { SidebarWrapper } from '@/context/SidebarContext';
import { getCookie } from '@/auth/cookie';
import { UserRoleProvider } from '@/context/UserRoleContext';
type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
type CurrentUser = { //added to ensure admin cant delete itself or role change
    id: string;
    username: string;
    role: UserRole;
};
function decodeJwtPayload(segment: string): Record<string, unknown>
{
    return JSON.parse(Buffer.from(segment, 'base64url').toString('utf8'));
}
function getUserFromToken(token: string): CurrentUser {
    if(!token)
    {
        return{ id: '', username: '', role: 'USER' };
    }
    try
    {
        const payload = decodeJwtPayload(token.split('.')[1]);
        return{
            id: typeof payload.sub === 'string' ? payload.sub : '',
            username: typeof payload.username === 'string' ? payload.username : '',
            role: (payload.role ?? 'USER') as UserRole,
        };
    }
    catch
    {
        return{ id: '', username: '', role: 'USER' };
    }
}

export default async function SidebarLayout({ children }: { children: React.ReactNode }) {
    const token = await getCookie();
    const currentUser = getUserFromToken(token);

    return (
        <SidebarWrapper>
            <UserRoleProvider user={currentUser}>
                <div className="flex min-h-screen bg-[var(--color-primary)]">
                    <Sidebar />
                    <main className="relative z-10 min-w-0 flex-1 overflow-x-hidden
                                    bg-[var(--color-lightest)] rounded-l-3xl
                                    shadow-[-8px_0_24px_var(--color-dark)]/50">
                        {children}
                    </main>
                </div>
            </UserRoleProvider>
        </SidebarWrapper>
    );
}