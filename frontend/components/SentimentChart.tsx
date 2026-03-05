'use client';

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface SentimentChartProps {
  counts: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

// Premium, sophisticated colors
const COLORS = {
  positive: '#2D6A4F',
  negative: '#9D174D',
  neutral: '#78716C',
};

export default function SentimentChart({ counts }: SentimentChartProps) {
  const data = [
    { name: 'Positive', value: counts.positive, color: COLORS.positive },
    { name: 'Negative', value: counts.negative, color: COLORS.negative },
    { name: 'Neutral', value: counts.neutral, color: COLORS.neutral },
  ];

  const total = counts.positive + counts.negative + counts.neutral;

  return (
    <div className="flex flex-col gap-2.5">
      <h2 className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
        Sentiment
      </h2>
      <div className="flex items-center gap-4">
        <div className="w-16 h-16">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={18}
                outerRadius={30}
                paddingAngle={3}
                dataKey="value"
                strokeWidth={0}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-col gap-1.5">
          {data.map((item) => (
            <div key={item.name} className="flex items-center gap-2 text-xs">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-text-secondary">
                {item.name}
              </span>
              <span className="text-text-muted">
                {Math.round((item.value / total) * 100)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
