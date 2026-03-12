'use client';

import TopNav from '@/components/TopNav';
import { Calendar } from 'lucide-react';

interface MetricData {
  label: string;
  value: string;
  change: string;
  changeType: 'sage' | 'curious' | 'skeptical';
  valueColor?: string;
}

interface SimulationRow {
  feature: string;
  sentiment: number;
  sentimentType: 'sage' | 'curious' | 'skeptical' | 'neutral';
  agents: string;
}

const METRICS: MetricData[] = [
  { label: 'Total Simulations', value: '48', change: '+12', changeType: 'sage' },
  { label: 'Avg. Sentiment', value: '74%', change: '+5%', changeType: 'sage', valueColor: '#7C9070' },
  { label: 'Agent Responses', value: '12.4k', change: '+34%', changeType: 'curious' },
  { label: 'Features Tested', value: '23', change: '+3', changeType: 'skeptical' },
];

const CHART_DATA = [
  { day: 'Mon', height: 160, color: '#7C9070' },
  { day: 'Tue', height: 200, color: '#7C9070' },
  { day: 'Wed', height: 140, color: '#7C9070' },
  { day: 'Thu', height: 240, color: '#7C9070' },
  { day: 'Fri', height: 180, color: '#7C9070' },
  { day: 'Sat', height: 100, color: '#9B8AA8' },
  { day: 'Sun', height: 260, color: '#7C9070' },
];

const SIMULATIONS: SimulationRow[] = [
  { feature: 'Dark mode + themes', sentiment: 72, sentimentType: 'sage', agents: '2,847' },
  { feature: 'AI copilot assistant', sentiment: 89, sentimentType: 'sage', agents: '1,523' },
  { feature: 'Remove free tier', sentiment: 23, sentimentType: 'skeptical', agents: '2,100' },
  { feature: 'Mobile app launch', sentiment: 61, sentimentType: 'curious', agents: '980' },
  { feature: 'Redesign onboarding', sentiment: 45, sentimentType: 'neutral', agents: '1,205' },
];

const CHANGE_STYLES = {
  sage: 'bg-sage-light text-sage-dark',
  curious: 'bg-[rgba(91,155,213,0.08)] text-curious',
  skeptical: 'bg-[rgba(212,132,94,0.08)] text-skeptical',
  neutral: 'bg-[rgba(155,138,168,0.08)] text-neutral',
};

export default function DashboardPage() {
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <TopNav />

      <div className="flex-1 px-12 py-8 flex flex-col gap-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center w-full">
          <h1 className="font-display text-[28px] font-medium text-text tracking-[-0.8px]">
            Analytics Overview
          </h1>
          <div className="flex-1" />
          <button className="flex items-center gap-1.5 rounded-[8px] px-3.5 py-2 border border-border bg-transparent cursor-pointer">
            <Calendar className="w-3.5 h-3.5 text-text-muted" />
            <span className="text-[13px] font-medium text-text-secondary">
              Last 7 days
            </span>
          </button>
        </div>

        {/* Metrics Grid */}
        <div className="flex gap-5 w-full">
          {METRICS.map((metric) => (
            <div
              key={metric.label}
              className="flex-1 rounded-[16px] bg-surface border border-border shadow-[0_4px_30px_#00000006] p-6 flex flex-col gap-2"
            >
              <span className="text-[13px] font-medium text-text-secondary">
                {metric.label}
              </span>
              <div className="flex items-end gap-2">
                <span
                  className="font-display text-4xl font-medium tracking-[-1px] leading-none"
                  style={{ color: metric.valueColor || '#2D2D2D' }}
                >
                  {metric.value}
                </span>
                <span
                  className={`rounded-[6px] px-2 py-1 font-mono text-[11px] leading-none mb-1 ${
                    CHANGE_STYLES[metric.changeType]
                  }`}
                >
                  {metric.change}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom Row: Chart + Table */}
        <div className="flex gap-5 flex-1 min-h-0">
          {/* Chart Card */}
          <div className="flex-1 rounded-[16px] bg-surface border border-border shadow-[0_4px_30px_#00000006] p-6 flex flex-col gap-5">
            <div className="flex items-center w-full">
              <span className="font-display text-lg font-medium text-text">
                Sentiment Over Time
              </span>
              <div className="flex-1" />
              <div className="flex gap-3">
                <LegendItem color="#7C9070" label="Positive" />
                <LegendItem color="#5B9BD5" label="Curious" />
                <LegendItem color="#9B8AA8" label="Neutral" />
              </div>
            </div>
            <div className="flex-1 flex gap-4 px-2 items-end">
              {CHART_DATA.map((bar) => (
                <div
                  key={bar.day}
                  className="flex-1 flex flex-col items-center gap-1.5 justify-end h-full"
                >
                  <div
                    className="w-full rounded-t-[8px]"
                    style={{ height: bar.height, backgroundColor: bar.color }}
                  />
                  <span className="text-[11px] font-medium text-text-muted">
                    {bar.day}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Table Card */}
          <div className="w-[420px] shrink-0 rounded-[16px] bg-surface border border-border shadow-[0_4px_30px_#00000006] flex flex-col overflow-hidden">
            <div className="flex items-center px-6 py-[18px]">
              <span className="font-display text-lg font-medium text-text">
                Recent Simulations
              </span>
              <div className="flex-1" />
              <span className="text-xs font-semibold text-sage cursor-pointer">
                View all
              </span>
            </div>
            <div className="flex items-center px-6 py-2.5 bg-surface-alt border-t border-b border-border">
              <span className="flex-1 text-xs font-semibold text-text-muted">
                Feature
              </span>
              <span className="w-20 text-xs font-semibold text-text-muted">
                Sentiment
              </span>
              <span className="w-[60px] text-xs font-semibold text-text-muted">
                Agents
              </span>
            </div>
            <div className="flex-1 overflow-y-auto">
              {SIMULATIONS.map((sim) => (
                <div
                  key={sim.feature}
                  className="flex items-center px-6 py-3.5 border-b border-border last:border-b-0"
                >
                  <span className="flex-1 text-[13px] font-medium text-text">
                    {sim.feature}
                  </span>
                  <div className="w-20">
                    <span
                      className={`inline-flex items-center rounded-[6px] px-2 py-1 font-mono text-[11px] ${
                        CHANGE_STYLES[sim.sentimentType]
                      }`}
                    >
                      {sim.sentiment}%
                    </span>
                  </div>
                  <span className="w-[60px] text-[13px] text-text-secondary">
                    {sim.agents}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1">
      <div
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="text-[11px] text-text-secondary">{label}</span>
    </div>
  );
}
