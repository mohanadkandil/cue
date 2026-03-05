'use client';

import { ReactNode } from 'react';

interface SidebarProps {
  children: ReactNode;
}

export default function Sidebar({ children }: SidebarProps) {
  return (
    <aside className="w-80 h-full bg-surface border-l border-border flex flex-col gap-5 p-5 overflow-hidden">
      {children}
    </aside>
  );
}
