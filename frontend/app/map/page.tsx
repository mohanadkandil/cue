'use client';

import { useEffect, useState } from 'react';
import TopNav from '@/components/TopNav';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface AgentNode {
  id: number;
  x: number;
  y: number;
  size: number;
  color: string;
  opacity: number;
}

interface Reaction {
  id: number;
  text: string;
  x: number;
  y: number;
  color: string;
  bgColor: string;
}

interface Message {
  id: number;
  name: string;
  avatar: string;
  time: string;
  text: string;
}

const AGENT_COLORS = ['#7C9070', '#5B9BD5', '#D4845E', '#9B8AA8', '#C9B8A8'];

const REACTIONS: Reaction[] = [
  { id: 1, text: 'Love this!', x: 90, y: 30, color: '#7C9070', bgColor: 'rgba(124,144,112,0.09)' },
  { id: 2, text: 'Need more details', x: 200, y: 60, color: '#5B9BD5', bgColor: 'rgba(91,155,213,0.09)' },
  { id: 3, text: 'Finally!', x: 350, y: 20, color: '#D4845E', bgColor: 'rgba(212,132,94,0.09)' },
  { id: 4, text: "Meh, don't care", x: 480, y: 80, color: '#9B8AA8', bgColor: 'rgba(155,138,168,0.09)' },
  { id: 5, text: 'Take my money!', x: 600, y: 35, color: '#7C9070', bgColor: 'rgba(124,144,112,0.09)' },
  { id: 6, text: 'When is ETA?', x: 100, y: 185, color: '#5B9BD5', bgColor: 'rgba(91,155,213,0.09)' },
  { id: 7, text: 'About time!', x: 420, y: 200, color: '#D4845E', bgColor: 'rgba(212,132,94,0.09)' },
  { id: 8, text: 'Will it slow things?', x: 300, y: 280, color: '#8A7A6A', bgColor: 'rgba(201,184,168,0.19)' },
  { id: 9, text: 'Yes!! Ship it', x: 580, y: 290, color: '#7C9070', bgColor: 'rgba(124,144,112,0.09)' },
];

const MESSAGES: Message[] = [
  {
    id: 1,
    name: 'Agent Sarah',
    avatar: '#7C9070',
    time: 'just now',
    text: 'Dark mode is a must-have for me. I use this app late at night and the bright screen is painful. This will make a huge difference!',
  },
  {
    id: 2,
    name: 'Agent James',
    avatar: '#5B9BD5',
    time: '30s ago',
    text: "Custom themes are a smart move. I'd love to match my brand colors across the workspace. Any API for this?",
  },
  {
    id: 3,
    name: 'Agent Maya',
    avatar: '#D4845E',
    time: '1m ago',
    text: 'Performance concerns here. Heavy theming with CSS variables can create jank on lower-end devices. Will there be a lite mode?',
  },
  {
    id: 4,
    name: 'Agent Dev',
    avatar: '#9B8AA8',
    time: '1m ago',
    text: 'I switched to dark mode on every tool I use. This is overdue. Ship it yesterday!',
  },
  {
    id: 5,
    name: 'Agent Priya',
    avatar: '#C9B8A8',
    time: '2m ago',
    text: 'Would the palette editor support importing from Figma? That would be a killer feature for design teams.',
  },
];

function generateAgentNodes(): AgentNode[] {
  const nodes: AgentNode[] = [];
  for (let i = 0; i < 18; i++) {
    nodes.push({
      id: i,
      x: 50 + Math.random() * 750,
      y: 40 + Math.random() * 340,
      size: 14 + Math.random() * 38,
      color: AGENT_COLORS[Math.floor(Math.random() * AGENT_COLORS.length)],
      opacity: 0.3 + Math.random() * 0.6,
    });
  }
  return nodes;
}

export default function MapPage() {
  const [feature, setFeature] = useState('Dark mode with custom themes');
  const [nodes, setNodes] = useState<AgentNode[]>([]);
  const [newMessages, setNewMessages] = useState(142);

  useEffect(() => {
    const storedFeature = sessionStorage.getItem('agentsim_feature');
    if (storedFeature) {
      setFeature(storedFeature);
    }
    setNodes(generateAgentNodes());
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <TopNav />

      <div className="flex flex-1 overflow-hidden">
        {/* Map Side */}
        <div className="flex-1 p-6 flex flex-col gap-4 overflow-hidden">
          {/* Map Header */}
          <div className="flex items-center w-full">
            <div className="flex-1 flex flex-col gap-1">
              <span className="font-display text-2xl font-medium text-text tracking-[-0.5px]">
                Agent Network
              </span>
              <span className="text-[13px] text-text-secondary">
                {feature} — 2,847 agents reacting
              </span>
            </div>
            <div className="flex gap-2">
              <span className="pill pill-sage">
                <TrendingUp className="w-3 h-3 text-sage" />
                72% Positive
              </span>
              <span className="pill pill-skeptical">
                <TrendingDown className="w-3 h-3 text-skeptical" />
                8% Negative
              </span>
              <span className="pill pill-neutral">
                <Minus className="w-3 h-3 text-neutral" />
                20% Neutral
              </span>
            </div>
          </div>

          {/* Map Card */}
          <div className="flex-1 rounded-[16px] bg-surface border border-border shadow-[0_4px_30px_#00000006] relative overflow-hidden">
            {/* Agent Nodes */}
            {nodes.map((node) => (
              <div
                key={node.id}
                className="absolute rounded-full transition-all duration-300"
                style={{
                  width: node.size,
                  height: node.size,
                  backgroundColor: node.color,
                  opacity: node.opacity,
                  left: node.x,
                  top: node.y,
                }}
              />
            ))}

            {/* Reaction Labels */}
            {REACTIONS.map((reaction) => (
              <div
                key={reaction.id}
                className="absolute rounded-[6px] px-2.5 py-1 text-[11px] font-medium whitespace-nowrap"
                style={{
                  left: reaction.x,
                  top: reaction.y,
                  backgroundColor: reaction.bgColor,
                  color: reaction.color,
                }}
              >
                {reaction.text}
              </div>
            ))}
          </div>
        </div>

        {/* Chat Panel */}
        <div className="w-[380px] bg-surface border-l border-border flex flex-col shrink-0">
          <div className="flex items-center px-5 py-[18px] border-b border-border gap-2.5">
            <span className="font-display text-lg font-medium text-text">
              Agent Chatter
            </span>
            <span className="bg-sage-light rounded-[6px] px-2.5 py-1 text-[11px] font-semibold text-sage-dark">
              {newMessages} new
            </span>
          </div>
          <div className="flex-1 overflow-y-auto flex flex-col">
            {MESSAGES.map((msg) => (
              <div
                key={msg.id}
                className="flex flex-col gap-2 px-5 py-3.5 border-b border-border last:border-b-0"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-7 h-7 rounded-full shrink-0"
                    style={{ backgroundColor: msg.avatar }}
                  />
                  <span className="text-[13px] font-semibold text-text">
                    {msg.name}
                  </span>
                  <span className="text-[11px] text-text-muted">{msg.time}</span>
                </div>
                <p className="text-[13px] text-text-secondary leading-[1.5]">
                  {msg.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
