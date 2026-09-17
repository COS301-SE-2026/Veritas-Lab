'use client';
import AuditLogs from '@/components/common/auditLogs';
import { useUserRole } from '@/context/UserRoleContext';
import { useRouter } from 'next/dist/client/components/navigation';
import { useEffect } from 'react';
export default function AuditLogPage() {
    const router = useRouter();
    const userRole = useUserRole();
    useEffect(() => {
      if (userRole !== 'ADMIN') {
        router.replace('/dashboard');
      }
    }, [userRole, router]);

    return (
        <div className='mx-auto max-w-7xl px-6 sm:px-8 pt-10 pb-16'>
            <div className='mb-8'>
                <h1 className='text-[30px] sm:text-[34px] font-bold tracking-tight text-(--color-text-strong)'>Audit Log</h1>
                <p className='mt-1 text-[15px] text-(--color-text-muted)'>View audit logs for all activities</p>
            </div>
            <div className='vl-panel p-5'>
                <div className='space-y-3'>
                    <AuditLogs />
                </div>
            </div>
        </div>
    )
}