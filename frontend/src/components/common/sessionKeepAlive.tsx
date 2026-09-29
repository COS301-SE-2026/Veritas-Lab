'use client'
import { useSessionKeepAlive } from '@/lib/hooks/useSessionKeepAlive';
    
export default function SessionKeepAlive() {
    useSessionKeepAlive();
    return null;
}