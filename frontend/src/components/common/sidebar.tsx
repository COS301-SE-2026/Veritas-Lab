'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { useLogOut } from '@/lib/hooks/useLogOut';
import { useUserRole } from '@/context/UserRoleContext';
import Image from 'next/image';
// Uses Lucide for some nice icons. Pretty cool. // for admin we can change but user-star looks best atm
import {
  ChevronLeft, Menu, Home, Construction, LogOut, UserStar, HelpCircle,
} from 'lucide-react';
import Button from '@/components/ui/button';

// List of navigation items with their labels, paths, and icons
const navItems = [
  { label: 'Dashboard', href: '/dashboard',  icon: Home },
];

export default function Sidebar() {
    // Get the current pathname to determine which nav item is active
    const pathname = usePathname();
    const userRole = useUserRole();
    // State to manage whether the sidebar is collapsed or expanded
    const { collapsed, toggle } = useSidebar();
  const { logOut } = useLogOut();

    const navItems = [
      { label: 'Dashboard', href: '/dashboard',  icon: Home },
      ...(userRole === 'ADMIN' ? [{ label: 'Admin', href: '/admin', icon: UserStar }] : []),
      { label: 'Help', href: '/help', icon: HelpCircle },
    ];

    return (
      // Sidebar container with dynamic width based on collapsed state
        <div
        className={`
            flex flex-col h-screen sticky top-0
            bg-(--color-primary) text-(--color-background) border-r 
            transition-all duration-300 ease-in-out
            ${collapsed ? 'w-16' : 'w-64'}
        `}
        >
        <div className="flex items-center justify-between px-4 py-5">
            {!collapsed && (
              <div className="flex items-center gap-2 ml-4">
                <Image src="/VL_Logo.svg" alt="Veritas Lab Logo" width={0} height={0} className="w-10 h-10" />
                <div className="font-semibold text-xl mt-1 text-white">
                  Veritas Lab
                </div>
              </div>
            )}
            {/* Toggle button to collapse or expand the sidebar */}
            <Button
            onClick={toggle}
            variant="sidebar"
            >
            {collapsed ? <Menu size={18} /> : <ChevronLeft size={18} className='text-(--color-light)'/>}
            </Button>
        </div>
        {/* Navigation items */}
        <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            /* The navigation links and their styles depending on their active state */
            <Link
              key={href}
              href={href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-full text-sm
                transition-colors duration-150
                ${isActive
                  ? 'bg-(--color-secondary) text-(--color-text) font-medium'
                  : 'text-white hover:bg-(--color-dark) hover:text-white'
                }
                ${collapsed ? 'justify-center' : 'justify-start'}
              `}
            >
              <Icon size={18} />
              {!collapsed && <div>{label}</div>}
            </Link>
          );
        })}
        <footer className="absolute bottom-0 w-full p-4 space-y-1 text-center text-xs text-gray-400">

    <Button variant="sidebar" onClick={logOut} className="">
      <div className="flex items-center gap-2 justify-center pr-15 rounded-full text-sm text-white hover:bg-(--color-dark) transition-colors">
        {!collapsed && (
          <div>
            Log Out
          </div>
        )}
        <div>
          <LogOut size={18} />
        </div>
      </div>
    </Button>
</footer>
      </nav>
        </div>
  );
}