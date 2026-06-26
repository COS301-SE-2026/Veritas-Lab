import Sidebar from '@/components/common/sidebar';
import { SidebarWrapper } from '@/context/SidebarContext';
import { getCookie } from '@/auth/cookie';
import { UserRoleProvider } from '@/context/UserRoleContext';
type UserRole = 'ADMIN' | 'INVESTIGATOR' | 'USER';

function getRoleFromToken(token: string): UserRole {
    if (!token) return 'USER';
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return (payload.role ?? 'USER') as UserRole;
    } catch {
        return 'USER';
    }
}

export default async function SidebarLayout({ children }: { children: React.ReactNode }) {
    const token = await getCookie();
    const userRole = getRoleFromToken(token);

    return (
        <SidebarWrapper>
            <div className="flex">
                <Sidebar />
                <main className="flex-1 p-4">
                    <UserRoleProvider role={userRole}>
                        {children}
                    </UserRoleProvider>
                </main>
            </div>
        </SidebarWrapper>
    );
}