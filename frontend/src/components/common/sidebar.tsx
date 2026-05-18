'use client';

import Link from 'next/link';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
// Uses Lucide for some nice icons. Pretty cool.
import {
    ChevronLeft, Menu, Home, Construction, Briefcase,
} from 'lucide-react';
import Button from '@/components/ui/button';

// List of navigation items with their labels, paths, and icons
const navItems = [
  { label: 'Home',      href: '/',           icon: Home },
  { label: 'Case Management', href: '/case-management',  icon: Briefcase },
  { label: 'Login', href: '/login',  icon: Construction },
  { label: 'Register', href: '/register',  icon: Construction },
];

export default function Sidebar() {
    // Get the current pathname to determine which nav item is active
    const pathname = usePathname();
    // State to manage whether the sidebar is collapsed or expanded
    const { collapsed, toggle } = useSidebar();

    return (
      // Sidebar container with dynamic width based on collapsed state
        <div
        className={`
            flex flex-col h-screen sticky top-0
            bg-[#3DBF79] text-[#ffffff] border-r 
            transition-all duration-300 ease-in-out
            ${collapsed ? 'w-16' : 'w-64'}
        `}
        >
        <div className="flex items-center justify-between px-4 py-5">
            {!collapsed && (
            <div className="font-semibold text-sm text-white">
                Veritas Lab
            </div>
            )}
            {/* Toggle button to collapse or expand the sidebar */}
            <Button
            onClick={toggle}
            variant="sidebar"
            >
            {collapsed ? <Menu size={18} /> : <ChevronLeft size={18} />}
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
                  ? 'bg-[#231F20] text-white font-medium'
                  : 'text-white hover:bg-[#231F20] hover:text-white'
                }
                ${collapsed ? 'justify-center' : 'justify-start'}
              `}
            >
              <Icon size={18} />
              {!collapsed && <div>{label}</div>}
            </Link>
          );
        })}
      </nav>
        </div>
  );
}