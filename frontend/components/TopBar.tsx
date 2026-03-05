'use client';

export default function TopBar() {
  return (
    <header className="h-14 flex items-center justify-between px-5 bg-surface border-b border-border">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" fill="white"/>
            <circle cx="12" cy="4" r="2" fill="white" opacity="0.6"/>
            <circle cx="12" cy="20" r="2" fill="white" opacity="0.6"/>
            <circle cx="4" cy="12" r="2" fill="white" opacity="0.6"/>
            <circle cx="20" cy="12" r="2" fill="white" opacity="0.6"/>
          </svg>
        </div>
        <span className="text-base font-semibold text-text tracking-tight">
          Cue
        </span>
      </div>

      <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-alt">
        <span className="w-1.5 h-1.5 rounded-full bg-positive animate-pulse-dot" />
        <span className="text-xs font-medium text-text-secondary">
          Live
        </span>
      </div>
    </header>
  );
}
