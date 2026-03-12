'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Zap, Sparkles, Network, Activity } from 'lucide-react';

interface QuoteData {
  name: string;
  role: string;
  text: string;
  sentiment: 'positive' | 'negative';
}

const MOCK_QUOTES: QuoteData[] = [
  {
    name: 'Sarah Chen',
    role: 'Power User',
    text: "Custom themes would let me match my brand colors across tools — I'd upgrade my plan for this alone.",
    sentiment: 'positive',
  },
  {
    name: 'Jake Morrison',
    role: 'Free Tier',
    text: "Please don't lock basic dark mode behind a subscription. Keep it free.",
    sentiment: 'negative',
  },
];

export default function OutputPage() {
  const router = useRouter();
  const [feature, setFeature] = useState('');
  const [agentCount, setAgentCount] = useState(0);

  useEffect(() => {
    const storedFeature = sessionStorage.getItem('agentsim_feature');
    if (storedFeature) {
      setFeature(storedFeature);
    }

    // Simulate agent count animation
    const interval = setInterval(() => {
      setAgentCount((prev) => {
        if (prev >= 47) {
          clearInterval(interval);
          return 47;
        }
        return prev + 1;
      });
    }, 30);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top Bar */}
      <div className="flex items-center px-12 py-3.5 w-full border-b border-border shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-sage-dark rounded-[8px] flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-[17px] font-bold text-text">AgentSim</span>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-1.5 rounded-full bg-sage-light border border-sage/20 px-3.5 py-1.5">
          <div className="w-[7px] h-[7px] rounded-full bg-sage animate-pulse-dot" />
          <span className="text-xs font-semibold text-sage-dark">
            {agentCount} agents responded
          </span>
        </div>
      </div>

      {/* Center Content */}
      <div className="flex-1 overflow-y-auto flex justify-center">
        <div className="w-[760px] max-w-full px-5 py-9 flex flex-col gap-8">
          {/* Feature Row */}
          <div className="flex items-center gap-2.5 w-full">
            <span className="text-lg font-semibold text-text">
              "{feature || 'Dark mode with custom themes'}"
            </span>
            <span className="ml-auto text-[13px] text-text-muted">1m 47s</span>
          </div>

          {/* Summary Cards */}
          <div className="flex gap-3.5 w-full">
            <SummaryCard value="72%" label="Positive" color="positive" />
            <SummaryCard value="15%" label="Curious" color="curious" />
            <SummaryCard value="5%" label="Skeptical" color="skeptical" />
            <SummaryCard value="8%" label="Negative" color="negative" />
          </div>

          {/* Insight Card */}
          <div className="rounded-[14px] bg-sage-light border border-sage/20 p-5 px-6 flex flex-col gap-2.5">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-sage-dark" />
              <span className="text-[13px] font-semibold text-sage-dark">
                Key Insight
              </span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              Most agents responded positively. Dark mode is considered a baseline
              expectation. The custom themes angle excites power users and
              developers — many mentioned willingness to upgrade plans. The main
              concern from a small group is about performance impact and keeping it
              accessible on free tiers.
            </p>
          </div>

          {/* Notable Responses */}
          <span className="text-[13px] font-semibold text-text-muted tracking-wide">
            Notable responses
          </span>

          <div className="flex flex-col gap-3.5">
            {MOCK_QUOTES.map((quote, i) => (
              <QuoteCard key={i} {...quote} />
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="flex items-center justify-center gap-4 px-12 py-4 border-t border-border w-full shrink-0">
        <button
          onClick={() => router.push('/map')}
          className="btn-primary bg-sage-dark"
        >
          <Network className="w-4 h-4" />
          <span>Open Agent Sandbox</span>
        </button>
        <button
          onClick={() => router.push('/dashboard')}
          className="btn-secondary"
        >
          <Activity className="w-4 h-4 text-text-secondary" />
          <span>View Dashboard</span>
        </button>
      </div>
    </div>
  );
}

function SummaryCard({
  value,
  label,
  color,
}: {
  value: string;
  label: string;
  color: 'positive' | 'curious' | 'skeptical' | 'negative';
}) {
  const colorMap = {
    positive: 'text-positive',
    curious: 'text-curious',
    skeptical: 'text-skeptical',
    negative: 'text-negative',
  };

  return (
    <div className="flex-1 rounded-[14px] bg-surface border border-border p-[18px] px-5 flex flex-col gap-1">
      <span className={`font-display text-[30px] font-medium ${colorMap[color]}`}>
        {value}
      </span>
      <span className="text-xs font-medium text-text-muted">{label}</span>
    </div>
  );
}

function QuoteCard({ name, role, text, sentiment }: QuoteData) {
  const avatarGradient =
    sentiment === 'positive'
      ? 'bg-gradient-to-br from-curious to-emerald-400'
      : 'bg-gradient-to-br from-negative to-orange-500';

  return (
    <div className="rounded-[14px] bg-surface border border-border p-4 px-5 flex gap-3.5">
      <div className={`w-8 h-8 rounded-full shrink-0 ${avatarGradient}`} />
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-2 w-full">
          <span className="text-[13px] font-semibold text-text">{name}</span>
          <span className="text-[11px] text-text-muted">{role}</span>
          <div className="flex-1" />
          <span
            className={`text-[11px] font-medium ${
              sentiment === 'positive' ? 'text-positive' : 'text-negative'
            }`}
          >
            {sentiment === 'positive' ? 'Positive' : 'Negative'}
          </span>
        </div>
        <p className="text-[13px] text-text-secondary leading-[1.55]">{text}</p>
      </div>
    </div>
  );
}
