'use client';

import Link from 'next/link';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import {
    ChevronLeft, Menu, Home, Construction, Settings,
} from 'lucide-react';

const navItems = [
  { label: 'Home',      href: '/',           icon: Home },
  { label: 'Page', href: '/login',  icon: Construction },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [collapsed, setCollapsed] = useState(false);

    return (
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
            <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-md hover:bg-[#231F20] transition-colors ml-auto"
            >
            {collapsed ? <Menu size={18} /> : <ChevronLeft size={18} />}
            </button>
        </div>
        <nav className="flex-1 px-2 py-4 space-y-1">
        {navItems.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href;
          return (
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