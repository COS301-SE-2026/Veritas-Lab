'use client';

import Link from 'next/link';
import { useState } from 'react';
import {
    ChevronLeft, Menu
} from 'lucide-react';


export default function Sidebar() {
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
    </div>
  );
}