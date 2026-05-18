import Sidebar from '@/components/common/sidebar';
import { SidebarWrapper } from '@/context/SidebarContext';
export default function SidebarLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    //Uses the SidebarProvider to wrap the layout. This persists the sidebar's state across pages.
    <SidebarWrapper>
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-4">
          {children}
        </main>
      </div>
    </SidebarWrapper>
  );
}