import Sidebar from '@/components/common/sidebar';
import { SidebarWrapper } from '@/context/SidebarContext';
import { getCookie } from '@/auth/cookie';
import { UserRoleProvider } from '@/context/UserRoleContext';
import { redirect } from 'next/dist/client/components/navigation';
type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';
type CurrentUser = { //added to ensure admin cant delete itself or role change
    id: string;
    username: string;
    role: UserRole;
};
function decodeJwtPayload(segment: string): Record<string, unknown> {
    return JSON.parse(Buffer.from(segment, 'base64url').toString('utf8'));
}

function isExpired(payload: Record<string, unknown>): boolean {
    return typeof payload.exp === 'number' && payload.exp * 1000 < Date.now();
}

function getUserFromToken(token: string): CurrentUser {
    if (!token) {
        return { id: '', username: '', role: 'USER' };
    }
    try {
        const payload = decodeJwtPayload(token.split('.')[1]);
        return {
            id: typeof payload.sub === 'string' ? payload.sub : '',
            username: typeof payload.username === 'string' ? payload.username : '',
            role: (payload.role ?? 'USER') as UserRole,
        };
    }
    catch {
        return { id: '', username: '', role: 'USER' };
    }
}

export default async function SidebarLayout({ children }: { children: React.ReactNode }) {
    const token = await getCookie();
    if(!token) redirect('/login');
    try {
        const payload = decodeJwtPayload(token.split('.')[1]);
        if (isExpired(payload)) redirect('/login');
    } catch {
        redirect('/login');
    }
    const currentUser = getUserFromToken(token);

    return (
        <SidebarWrapper>
            <UserRoleProvider user={currentUser}>
                <div className="flex min-h-screen bg-[var(--color-primary)]">
                    <Sidebar />
                    <main className="relative z-10 min-w-0 flex-1 overflow-x-hidden
                                    bg-(--color-canvas) rounded-l-[28px]
                                    shadow-[-14px_0_44px_-16px_rgba(0,0,0,0.45)]">
                        {children}
                    </main>
                </div>
            </UserRoleProvider>
        </SidebarWrapper>
    );
}