'use client';

import React, { createContext, useState, ReactNode } from 'react';

const SidebarContext = createContext({ collapsed: false, toggle: () => {} });

export function SidebarWrapper({ children }: { children: ReactNode }) {
    // Manages the sidebar's collapse state here instead of in the sidebar component
    // This stops the sidebar from resetting its state when navigating between pages
    const [collapsed, setCollapsed] = useState(false);
    return (
        <SidebarContext.Provider value={{ collapsed, toggle: () => setCollapsed(!collapsed) }}>
            {children}
        </SidebarContext.Provider>
    );
};

export const useSidebar = () => React.useContext(SidebarContext);