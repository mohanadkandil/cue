'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { ExtendedFeedEvent } from '@/lib/mockData';

interface LiveFeedProps {
  events: ExtendedFeedEvent[];
}

export default function LiveFeed({ events }: LiveFeedProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActionText = (type: string) => {
    switch (type) {
      case 'share': return 'shared with';
      case 'influence': return 'influenced';
      case 'disagree': return 'disagreed with';
      case 'discuss': return 'discussed with';
      case 'connect': return 'connected with';
      default: return 'interacted with';
    }
  };

  return (
    <div className="flex flex-col gap-2.5 flex-1 min-h-0">
      <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
        Activity
      </h2>
      <div className="flex-1 overflow-y-auto space-y-1.5">
        <AnimatePresence>
          {events.map((event) => (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="px-3 py-2.5 rounded-lg border border-border bg-surface"
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-[13px] text-text leading-snug">
                  <span className="font-medium">{event.agent1Name}</span>
                  <span className="text-text-secondary"> {getActionText(event.type)} </span>
                  <span className="font-medium">{event.agent2Name}</span>
                </p>
                <span className="text-[11px] text-text-muted flex-shrink-0">
                  {formatTime(event.timestamp)}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
