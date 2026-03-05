'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Agent } from '@/lib/types';

interface AgentModalProps {
  agent: Agent | null;
  onClose: () => void;
}

// Premium, sophisticated colors
const SENTIMENT_COLORS = {
  positive: '#2D6A4F',
  negative: '#9D174D',
  neutral: '#78716C',
};

export default function AgentModal({ agent, onClose }: AgentModalProps) {
  if (!agent) return null;

  const PersonalityBar = ({ label, value }: { label: string; value: number }) => (
    <div className="flex flex-col gap-1.5">
      <div className="flex justify-between text-xs">
        <span className="text-text-secondary">{label}</span>
        <span className="text-text-muted">{value}%</span>
      </div>
      <div className="h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );

  return (
    <AnimatePresence>
      <div
        className="fixed inset-0 z-50 flex justify-end bg-black/20"
        onClick={onClose}
      >
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className="w-80 h-full bg-surface border-l border-border p-5 overflow-y-auto shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-start mb-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-surface-alt flex items-center justify-center text-2xl">
                {agent.avatar}
              </div>
              <div>
                <h2 className="text-base font-semibold text-text">{agent.name}</h2>
                <p className="text-xs text-text-muted">{agent.occupation}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-surface-alt transition-colors text-text-muted"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M1 1L11 11M1 11L11 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          <div className="flex gap-2 mb-5">
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium"
              style={{
                backgroundColor: SENTIMENT_COLORS[agent.sentiment] + '18',
                color: SENTIMENT_COLORS[agent.sentiment],
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: SENTIMENT_COLORS[agent.sentiment] }}
              />
              {agent.sentiment.charAt(0).toUpperCase() + agent.sentiment.slice(1)}
            </span>
            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-surface-alt text-text-secondary">
              {agent.location}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="p-3 rounded-xl bg-surface-alt">
              <p className="text-[11px] text-text-muted uppercase tracking-wide">Age</p>
              <p className="text-sm font-medium text-text mt-0.5">{agent.age}</p>
            </div>
            <div className="p-3 rounded-xl bg-surface-alt">
              <p className="text-[11px] text-text-muted uppercase tracking-wide">Influence</p>
              <p className="text-sm font-medium text-text mt-0.5">{agent.influence}/10</p>
            </div>
          </div>

          <div className="mb-5">
            <h3 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-2">
              Current Thought
            </h3>
            <div className="p-3 rounded-xl bg-surface-alt">
              <p className="text-sm text-text-secondary italic leading-relaxed">
                "{agent.currentThought}"
              </p>
            </div>
          </div>

          <div className="mb-5">
            <h3 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-3">
              Personality
            </h3>
            <div className="space-y-3">
              <PersonalityBar label="Openness" value={agent.personality.openness} />
              <PersonalityBar label="Agreeableness" value={agent.personality.agreeableness} />
              <PersonalityBar label="Extraversion" value={agent.personality.extraversion} />
            </div>
          </div>

          <div>
            <h3 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider mb-2">
              Network
            </h3>
            <p className="text-sm text-text-secondary">
              Connected to {agent.friends.length} agents
            </p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
