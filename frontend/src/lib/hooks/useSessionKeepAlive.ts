'use client'
import { useEffect, useRef } from 'react';
import { refreshSession } from '@/lib/api/refresh';

const RECENT_PING_THRESHOLD = 5 * 60 * 1000; // 5 minutes

export function useSessionKeepAlive() {
    const lastPing = useRef(0);

    useEffect(() => {
        const maybeRefreshSession = () => {
            const now = Date.now();
            if (now - lastPing.current < RECENT_PING_THRESHOLD) return; // Don't refresh if the last ping was recent
            lastPing.current = now;
            void refreshSession();
        };

        // Below are the conditions under which we want to refresh the session. We want to refresh on user activity and when the tab becomes visible again. 
        // Maybe more but I can't think of any right now.
        const events = ['mousemove', 'keydown', 'scroll', 'click'];
        events.forEach((event) => window.addEventListener(event, maybeRefreshSession, { passive: true }));

        const onVisible = () => {
            if (document.visibilityState === 'visible') maybeRefreshSession();
        }
        document.addEventListener('visibilitychange', onVisible);

        return () => {
            events.forEach((event) => window.removeEventListener(event, maybeRefreshSession));
            document.removeEventListener('visibilitychange', onVisible);
        }
    }, []);
}