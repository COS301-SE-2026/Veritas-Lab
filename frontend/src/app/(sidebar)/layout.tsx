import Sidebar from '@/components/common/sidebar';
import { SidebarWrapper } from '@/context/SidebarContext';
import AuthGuard from '@/guard/authGuard';

export default function SidebarLayout({ children }: { children: React.ReactNode }) {
    return (
    <AuthGuard>
            <SidebarWrapper>
                <div className="flex">
                    <Sidebar />
                    <main className="flex-1 p-4">{children}</main>
                </div>
            </SidebarWrapper>
    </AuthGuard>
    );
}