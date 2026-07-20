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

    return(
        <SidebarWrapper>
            <UserRoleProvider user={currentUser}>
                <div className="flex">
                    <Sidebar />
                    <main className="flex-1 p-4">
                        {children}
                    </main>
                </div>
            </UserRoleProvider>
        </SidebarWrapper>
    );
}