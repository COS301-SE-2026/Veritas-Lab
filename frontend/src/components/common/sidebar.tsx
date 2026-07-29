'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { useLogOut } from '@/lib/hooks/useLogOut';
import { useUserRole } from '@/context/UserRoleContext';
import Image from 'next/image';
// Uses Lucide for some nice icons. Pretty cool. // for admin we can change but user-star looks best atm
import {
  ChevronLeft, Menu, Home, LogOut, UserStar, HelpCircle,
} from 'lucide-react';
import Button from '@/components/ui/button';

export default function Sidebar() {
  const pathname = usePathname();
  const userRole = useUserRole();
  const { collapsed, toggle } = useSidebar();
  const { logOut } = useLogOut();

  const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    ...(userRole === 'ADMIN' ? [{ label: 'Admin', href: '/admin', icon: UserStar }] : []),
    { label: 'Help', href: '/help', icon: HelpCircle },
  ];

  return (
    <div
      className={`
        relative z-0 flex flex-col h-screen sticky top-0
        bg-[var(--color-primary)] text-white
        transition-all duration-300 ease-in-out
        ${collapsed ? 'w-16' : 'w-64'}
      `}
    >
      <div/>

      <header className="flex items-center justify-between px-4 py-5">
        {!collapsed && (
          <div className="flex items-center gap-2 ml-3">
            <Image src="/VL_Logo.svg" alt="Veritas Lab Logo" width={0} height={0} className="w-10 h-10" />
            <div className="font-semibold text-xl mt-1 text-white">Veritas Lab</div>
          </div>
        )}
        <Button onClick={toggle} variant="sidebar">
          {collapsed
            ? <Menu size={18} />
            : <ChevronLeft size={18} className="text-[var(--color-light)]" />}
        </Button>
      </header>

      <nav className={`flex-1 py-4 space-y-3 ${collapsed ? 'pl-2 pr-0' : 'pl-7 pr-0'}`}>
        {navItems.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <div key={href} className="relative">
              <Link
                href={href}
                className={`
                  group relative flex items-center gap-3 text-sm
                  rounded-l-full rounded-r-none
                  transition-[transform,background-color,color] duration-200 ease-out
                  ${collapsed
                    ? 'justify-center py-3 pl-0 pr-4 -mr-3'
                    : 'justify-start py-3 pl-4 pr-16 -mr-12'}
                  ${isActive
                    ? 'bg-[var(--color-secondary)] text-[var(--color-text)] font-medium translate-x-0'
                    : 'bg-white/8 text-white/90 -translate-x-1 hover:translate-x-0 hover:bg-white/15'}
                `}
              >
                <Icon size={18} className="shrink-0" />
                {!collapsed && <span className="truncate">{label}</span>}
              </Link>

              <span
                className={`absolute right-0 top-1/2 -translate-y-1/2
                            h-6 w-px ${isActive ? 'bg-black/20' : 'bg-white/10'}`}
              />
            </div>
          );
        })}
      </nav>

      <footer className={`pb-6 ${collapsed ? 'pl-2' : 'pl-7'}`}>
        <button
          onClick={logOut}
          className={`
            flex items-center gap-3 text-sm rounded-l-full rounded-r-none
            bg-white/8 text-white/90 hover:bg-white/15
            -translate-x-1 hover:translate-x-0
            transition-[transform,background-color] duration-200 ease-out
            ${collapsed ? 'justify-center py-3 pr-4 -mr-3 w-full' : 'justify-start py-3 pl-4 pr-16 -mr-12 w-full'}
          `}
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Log Out</span>}
        </button>
      </footer>
    </div>
  );
}