'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { useLogOut } from '@/lib/hooks/useLogOut';
import { useUserRole } from '@/context/UserRoleContext';
import Image from 'next/image';
// Uses Lucide for some nice icons. Pretty cool. // for admin we can change but user-star looks best atm
import {
    ChevronLeft, Menu, Home, LogOut, UserStar, HelpCircle, Settings, ScrollText,
} from 'lucide-react';
import Button from '@/components/ui/button';
import ResetPasswordModal from '@/components/common/resetPasswordModal';

export default function Sidebar() {
    const pathname = usePathname();
    const caseId = pathname.split('/')[2];
    const userRole = useUserRole();
    const { collapsed, toggle } = useSidebar();
    const { logOut } = useLogOut();
    const [isResetPasswordOpen, setIsResetPasswordOpen] = useState(false);

    const navItems = [
        { label: 'Dashboard', href: '/dashboard', icon: Home },
        ...(userRole === 'ADMIN' ? [{ label: 'Admin', href: '/admin', icon: UserStar }] : []),
        ...(userRole === 'ADMIN' ? [{ label: 'Audit Logs', href: '/audit-log', icon: ScrollText }] : []),
        { label: 'Help', href: '/help', icon: HelpCircle },
    ];
    const caseTabs = [ 'Evidence', 'Comments', 'Audit Timeline', 'Case Board' ]

    const footerItemClasses = (collapsed: boolean) =>
        `flex items-center gap-3 text-sm rounded-l-full rounded-r-none bg-white/[0.06] text-white/80 hover:bg-white/[0.14] hover:text-white -translate-x-1 hover:translate-x-0 transition-[transform,background-color,color] duration-200 ease-out ${collapsed ? 'justify-center py-3 pr-4 -mr-3 w-full' : 'justify-start py-3 pl-4 pr-16 -mr-12 w-full'}`;

    return (
        <div
            className={`relative z-0 flex flex-col h-screen sticky top-0 bg-gradient-to-b from-[#26221f] via-(--color-primary) to-[#1b1817] text-white transition-all duration-300 ease-in-out ${collapsed ? 'w-16' : 'w-64'}`}
        >
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
                        : <ChevronLeft size={18} className="text-white/70" />}
                </Button>
            </header>

            <nav className={`flex-1 py-4 space-y-2.5 ${collapsed ? 'pl-2 pr-0' : 'pl-7 pr-0'}`}>
                {navItems.map(({ label, href, icon: Icon }) => {
                    const isActive = pathname === href;
                    return (
                        <div key={href} className="relative">
                            <Link
                                href={href}
                                aria-current={isActive ? 'page' : undefined}
                                className={`group relative flex items-center gap-3 text-sm rounded-l-full rounded-r-none transition-[transform,background-color,color] duration-200 ease-out
                                    ${collapsed
                                            ? 'justify-center py-3 pl-0 pr-4 -mr-3'
                                            : 'justify-start py-3 pl-4 pr-16 -mr-12'}
                                    ${isActive
                                            ? 'bg-(--color-secondary) text-(--color-text) font-semibold shadow-[0_6px_18px_-8px_color-mix(in_srgb,var(--b-600)_80%,transparent)] translate-x-0'
                                            : 'bg-white/[0.06] text-white/80 -translate-x-1 hover:translate-x-0 hover:bg-white/[0.14] hover:text-white'}
                                `}
                            >
                                <Icon size={18} className="shrink-0" />
                                {!collapsed && <span className="truncate">{label}</span>}
                            </Link>
                        </div>
                    );
                })}
                {caseId && (
                    <>
                        <div>
                            {caseTabs.map((tab) => {
                                const isActive = pathname.includes(`tab=${tab}`);
                                return (
                                    <Link
                                        key={tab}
                                        href={`/case-page/${caseId}?tab=${tab}`}
                                        className={`group relative flex items-center gap-3 text-sm rounded-l-full rounded-r-none transition-[transform,background-color,color] duration-200 ease-out
                                            ${collapsed
                                                ? 'justify-center py-3 pl-0 pr-4 -mr-3'
                                                : 'justify-start py-3 pl-4 pr-16 -mr-12'}
                                            ${isActive
                                                ? 'bg-(--color-secondary) text-(--color-text) font-semibold shadow-[0_6px_18px_-8px_color-mix(in_srgb,var(--b-600)_80%,transparent)] translate-x-0'
                                                : 'bg-white/[0.06] text-white/80 -translate-x-1 hover:translate-x-0 hover:bg-white/[0.14] hover:text-white'}
                                        `}
                                    >
                                        
                                        {!collapsed && <span className="truncate">{tab}</span>}
                                    </Link>
                                );
                            })}
                        </div>
                    </>
                )}
            </nav>

            <footer className={`pb-6 ${collapsed ? 'pl-2' : 'pl-7'} space-y-3`}>
                <button
                    onClick={() => setIsResetPasswordOpen(true)}
                    className={footerItemClasses(collapsed)}
                >
                    <Settings size={18} className="shrink-0" />
                    {!collapsed && <span>Settings</span>}
                </button>

                <button
                    onClick={logOut}
                    className={footerItemClasses(collapsed)}
                >
                    <LogOut size={18} className="shrink-0" />
                    {!collapsed && <span>Log Out</span>}
                </button>
            </footer>

            <ResetPasswordModal
                isOpen={isResetPasswordOpen}
                onClose={() => setIsResetPasswordOpen(false)}
            />
        </div>
    );
}