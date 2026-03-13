"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Zap, Sparkles, Network, Activity, Loader2 } from "lucide-react";

interface QuoteData {
  name: string;
  role: string;
  text: string;
  sentiment: "positive" | "negative";
  avatar?: string;
}

interface PollResponse {
  success: boolean;
  event: string;
  agent_count: number;
  elapsed_seconds: number;
  sentiment_percentages: {
    positive: number;
    curious: number;
    skeptical: number;
    negative: number;
  };
  key_insight: string;
  notable_themes: string[];
  notable_responses: QuoteData[];
}

export default function OutputPage() {
  const router = useRouter();
  const [feature, setFeature] = useState("");
  const [loading, setLoading] = useState(true);
  const [pollData, setPollData] = useState<PollResponse | null>(null);
  const [agentCount, setAgentCount] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const pollStarted = useRef(false);

  useEffect(() => {
    const storedFeature = sessionStorage.getItem("agentsim_feature");
    if (storedFeature) {
      setFeature(storedFeature);
    }

    // Start polling immediately
    if (!pollStarted.current && storedFeature) {
      pollStarted.current = true;
      runPoll(storedFeature);
    }
  }, []);

  // Timer effect while loading
  useEffect(() => {
    if (!loading) return;
    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [loading]);

  const runPoll = async (content: string) => {
    setLoading(true);
    setElapsedTime(0);

    try {
      const response = await fetch("http://localhost:8000/poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });

      const data = await response.json();
      console.log("Poll response:", data);

      if (data.success) {
        setPollData(data);
        // Animate agent count
        animateCount(data.agent_count);
      }
    } catch (error) {
      console.error("Poll failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const animateCount = (target: number) => {
    let current = 0;
    const step = Math.ceil(target / 30);
    const interval = setInterval(() => {
      current += step;
      if (current >= target) {
        setAgentCount(target);
        clearInterval(interval);
      } else {
        setAgentCount(current);
      }
    }, 30);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  // Sample avatars for the loading animation
  const orbitAvatars = [
    "/avatars/isabella-rodriguez.png",
    "/avatars/abigail-chen.png",
    "/avatars/klaus-mueller.png",
    "/avatars/hailey-johnson.png",
    "/avatars/john-lin.png",
    "/avatars/carmen-ortiz.png",
    "/avatars/sam-moore.png",
    "/avatars/ryan-park.png",
  ];

  // Loading state with orbiting avatars
  if (loading) {
    const radius = 150;
    const centerX = 190;
    const centerY = 190;

    // Calculate positions for connection lines
    const getPosition = (index: number, total: number) => {
      const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
      return {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    };

    return (
      <div className="h-screen flex flex-col items-center justify-center bg-surface">
        {/* Orbiting avatars */}
        <div className="relative w-[380px] h-[380px] mb-10">
          {/* SVG for connection lines */}
          <svg className="absolute inset-0 w-full h-full" style={{ animation: 'spin 20s linear infinite' }}>
            <defs>
              <linearGradient id="lineGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#7C9070" stopOpacity="0.1" />
                <stop offset="50%" stopColor="#7C9070" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#7C9070" stopOpacity="0.1" />
              </linearGradient>
              <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#5B9BD5" stopOpacity="0.1" />
                <stop offset="50%" stopColor="#5B9BD5" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#5B9BD5" stopOpacity="0.1" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Connection lines between adjacent nodes */}
            {orbitAvatars.map((_, i) => {
              const pos1 = getPosition(i, orbitAvatars.length);
              const pos2 = getPosition((i + 1) % orbitAvatars.length, orbitAvatars.length);
              return (
                <line
                  key={`line-${i}`}
                  x1={pos1.x}
                  y1={pos1.y}
                  x2={pos2.x}
                  y2={pos2.y}
                  stroke={i % 2 === 0 ? "url(#lineGradient1)" : "url(#lineGradient2)"}
                  strokeWidth="2"
                  filter="url(#glow)"
                />
              );
            })}

            {/* Lines to center */}
            {orbitAvatars.map((_, i) => {
              const pos = getPosition(i, orbitAvatars.length);
              return (
                <line
                  key={`center-line-${i}`}
                  x1={centerX}
                  y1={centerY}
                  x2={pos.x}
                  y2={pos.y}
                  stroke="#7C9070"
                  strokeWidth="1"
                  strokeOpacity="0.15"
                  strokeDasharray="4 4"
                />
              );
            })}

            {/* Animated pulse dots on lines */}
            {orbitAvatars.map((_, i) => {
              const pos1 = getPosition(i, orbitAvatars.length);
              const pos2 = getPosition((i + 1) % orbitAvatars.length, orbitAvatars.length);
              return (
                <circle
                  key={`pulse-${i}`}
                  r="3"
                  fill={i % 2 === 0 ? "#7C9070" : "#5B9BD5"}
                  filter="url(#glow)"
                >
                  <animateMotion
                    dur={`${2 + i * 0.3}s`}
                    repeatCount="indefinite"
                    path={`M${pos1.x},${pos1.y} L${pos2.x},${pos2.y}`}
                  />
                </circle>
              );
            })}
          </svg>

          {/* Outer ring */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-[300px] h-[300px] rounded-full border border-sage/20" />
          </div>

          {/* Center pulse */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-sage/10 animate-ping" />
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-sage/30 to-sage/10 backdrop-blur-sm flex items-center justify-center shadow-lg">
              <Zap className="w-9 h-9 text-sage-dark" />
            </div>
          </div>

          {/* Static positioned avatars (no orbit, lines stay connected) */}
          {orbitAvatars.map((avatar, i) => {
            const pos = getPosition(i, orbitAvatars.length);
            return (
              <div
                key={i}
                className="absolute w-14 h-14 rounded-full overflow-hidden border-[3px] border-white shadow-xl"
                style={{
                  left: pos.x - 28,
                  top: pos.y - 28,
                  animation: `pulse 2s ease-in-out infinite`,
                  animationDelay: `${i * 0.2}s`,
                }}
              >
                <img
                  src={avatar}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
            );
          })}
        </div>

        {/* Text */}
        <div className="flex flex-col items-center gap-3">
          <h2 className="text-xl font-semibold text-text">
            Gathering perspectives...
          </h2>
          <p className="text-text-muted text-center max-w-[300px]">
            30 agents are sharing their thoughts on your announcement
          </p>
          <div className="flex items-center gap-2 mt-4 text-sm text-text-muted">
            <div className="w-1.5 h-1.5 rounded-full bg-sage animate-pulse" />
            <span>{formatTime(elapsedTime)}</span>
          </div>
        </div>

        {/* CSS for animations */}
        <style jsx>{`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
          @keyframes pulse {
            0%, 100% {
              transform: scale(1);
              box-shadow: 0 4px 20px rgba(124, 144, 112, 0.2);
            }
            50% {
              transform: scale(1.05);
              box-shadow: 0 4px 30px rgba(124, 144, 112, 0.4);
            }
          }
        `}</style>
      </div>
    );
  }

  const sentiments = pollData?.sentiment_percentages || {
    positive: 0,
    curious: 0,
    skeptical: 0,
    negative: 0,
  };

  const quotes = pollData?.notable_responses || [];

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
              "{feature || "Dark mode with custom themes"}"
            </span>
            <span className="ml-auto text-[13px] text-text-muted">
              {pollData?.elapsed_seconds ? `${pollData.elapsed_seconds}s` : ""}
            </span>
          </div>

          {/* Summary Cards */}
          <div className="flex gap-3.5 w-full">
            <SummaryCard
              value={`${sentiments.positive}%`}
              label="Positive"
              color="positive"
            />
            <SummaryCard
              value={`${sentiments.curious}%`}
              label="Curious"
              color="curious"
            />
            <SummaryCard
              value={`${sentiments.skeptical}%`}
              label="Skeptical"
              color="skeptical"
            />
            <SummaryCard
              value={`${sentiments.negative}%`}
              label="Negative"
              color="negative"
            />
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
              {pollData?.key_insight || "Analyzing responses..."}
            </p>
            {pollData?.notable_themes && pollData.notable_themes.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {pollData.notable_themes.map((theme, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 text-xs bg-white/60 rounded-full text-sage-dark"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Notable Responses */}
          {quotes.length > 0 && (
            <>
              <span className="text-[13px] font-semibold text-text-muted tracking-wide">
                Notable responses
              </span>

              <div className="flex flex-col gap-3.5">
                {quotes.map((quote, i) => (
                  <QuoteCard key={i} {...quote} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="flex items-center justify-center gap-4 px-12 py-4 border-t border-border w-full shrink-0">
        <button
          onClick={() => {
            // Store the event for sandbox to use
            if (pollData?.event) {
              sessionStorage.setItem("agentsim_sandbox_event", pollData.event);
            }
            router.push("/graph");
          }}
          className="btn-primary bg-sage-dark"
        >
          <Network className="w-4 h-4" />
          <span>Open Agent Sandbox</span>
        </button>
        <button
          onClick={() => router.push("/dashboard")}
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
  color: "positive" | "curious" | "skeptical" | "negative";
}) {
  const colorMap = {
    positive: "text-positive",
    curious: "text-curious",
    skeptical: "text-skeptical",
    negative: "text-negative",
  };

  return (
    <div className="flex-1 rounded-[14px] bg-surface border border-border p-[18px] px-5 flex flex-col gap-1">
      <span
        className={`font-display text-[30px] font-medium ${colorMap[color]}`}
      >
        {value}
      </span>
      <span className="text-xs font-medium text-text-muted">{label}</span>
    </div>
  );
}

function QuoteCard({ name, role, text, sentiment, avatar }: QuoteData) {
  const avatarGradient =
    sentiment === "positive"
      ? "bg-gradient-to-br from-curious to-emerald-400"
      : "bg-gradient-to-br from-negative to-orange-500";

  // Convert name to avatar path if not provided
  const avatarPath =
    avatar || `/avatars/${name.toLowerCase().replace(/\s+/g, "-")}.png`;

  return (
    <div className="rounded-[14px] bg-surface border border-border p-4 px-5 flex gap-3.5">
      <div
        className={`w-8 h-8 rounded-full shrink-0 overflow-hidden ${avatarGradient}`}
      >
        <img
          src={avatarPath}
          alt={name}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      </div>
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-2 w-full">
          <span className="text-[13px] font-semibold text-text">{name}</span>
          <span className="text-[11px] text-text-muted">{role}</span>
          <div className="flex-1" />
          <span
            className={`text-[11px] font-medium ${
              sentiment === "positive" ? "text-positive" : "text-negative"
            }`}
          >
            {sentiment === "positive" ? "Positive" : "Negative"}
          </span>
        </div>
        <p className="text-[13px] text-text-secondary leading-[1.55]">{text}</p>
      </div>
    </div>
  );
}
