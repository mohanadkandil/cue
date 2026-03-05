'use client';

import { useState } from 'react';

interface EventInjectorProps {
  onInject: (event: string) => void;
}

export default function EventInjector({ onInject }: EventInjectorProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onInject(value.trim());
      setValue('');
    }
  };

  return (
    <div className="flex flex-col gap-2.5">
      <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
        Inject Event
      </h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Describe an idea or event..."
          className="w-full h-20 px-3 py-2.5 bg-surface-alt border border-border rounded-xl text-sm text-text placeholder-text-muted resize-none focus:outline-none focus:border-text-muted transition-colors"
        />
        <button
          type="submit"
          className="px-4 py-2.5 bg-primary text-white text-sm font-medium rounded-xl hover:bg-primary-hover transition-colors"
        >
          Inject
        </button>
      </form>
    </div>
  );
}
