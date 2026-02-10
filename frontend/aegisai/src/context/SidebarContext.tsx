import { createContext, useCallback, useState, type ReactNode } from 'react';

interface SidebarContextType {
  isCollapsed: boolean;
  isMobileOpen: boolean;
  toggle: () => void;
  toggleMobile: () => void;
  closeMobile: () => void;
}

export const SidebarContext = createContext<SidebarContextType | null>(null);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const toggle = useCallback(() => setIsCollapsed(prev => !prev), []);
  const toggleMobile = useCallback(() => setIsMobileOpen(prev => !prev), []);
  const closeMobile = useCallback(() => setIsMobileOpen(false), []);

  return (
    <SidebarContext.Provider value={{ isCollapsed, isMobileOpen, toggle, toggleMobile, closeMobile }}>
      {children}
    </SidebarContext.Provider>
  );
}
