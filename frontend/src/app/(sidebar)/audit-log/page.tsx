'use client';
import AuditLogs from '@/components/common/auditLogs';
import { useUserRole } from '@/context/UserRoleContext';
import useAuditLog from '@/lib/hooks/useAuditLog';
import { useRouter } from 'next/dist/client/components/navigation';
import { useEffect } from 'react';
import Card from '@/components/ui/card';
export default function AuditLogPage() {
    const router = useRouter();
    const userRole = useUserRole();
    useEffect(() => {
      if (userRole !== 'ADMIN') {
        router.replace('/dashboard');
      }  
    })

    const { auditLogs, isLoading, error } = useAuditLog();

    if (isLoading) {
        return <div>Loading...</div>;
    }

    // if (error) {
    //     return <div>Error: {error}</div>;
    // }

    // if (!auditLogs) {
    //     return <div>No audit logs found</div>;
    // }

    return (
        <div className='mt-8 ml-8 mr-8'>
            <div className='flex items-start justify-between gap-4 mb-4'>
                <div>
                    <div className='text-[32px] font-bold text-[var(--color-text)]'>Audit Log</div>
                    <div className='text-[16px] text-[var(--color-light)]'>View audit logs for all activities</div>
                </div>
            </div>
            <Card 
                content={( <div className='space-y-3'><AuditLogs /> </div> )}
                className='rounded-[24px] border border-[var(--color-light)]/25 bg-[var(--color-secondary)]/8 p-5 text-[var(--color-text)]'
            />
        </div>
    )
}