'use client';

import { useState, useEffect, useRef } from 'react';
import TopNav from '@/components/TopNav';
import { Send, Loader2 } from 'lucide-react';

interface FeedItem {
  id: string;
  timestamp: string;
  agent_name: string;
  content: string;
  type: string;
}
import D3ForceGraph, { type AgentNode, type AgentLink } from '@/components/graph/D3ForceGraph';

// Color palette based on location
const COLORS = {
  cafe: '#7C9070',
  college: '#5B9BD5',
  coliving: '#9B8AA8',
  pharmacy: '#D4845E',
  family: '#E9C46A',
  apartment: '#81B29A',
  bar: '#E07A5F',
};

// 25 Smallville personas
const AGENTS: AgentNode[] = [
  { id: 'isabella-rodriguez', name: 'Isabella Rodriguez', color: COLORS.cafe, activity: 'Planning Valentine\'s party', sentiment: 'positive', location: 'Hobbs Cafe', avatar: '/avatars/isabella-rodriguez.png' },
  { id: 'maria-lopez', name: 'Maria Lopez', color: COLORS.college, activity: 'Studying physics & streaming', sentiment: 'curious', location: 'Oak Hill College', avatar: '/avatars/maria-lopez.png' },
  { id: 'klaus-mueller', name: 'Klaus Mueller', color: COLORS.college, activity: 'Writing research paper', sentiment: 'curious', location: 'Oak Hill College', avatar: '/avatars/klaus-mueller.png' },
  { id: 'ayesha-khan', name: 'Ayesha Khan', color: COLORS.college, activity: 'Senior thesis research', sentiment: 'curious', location: 'Oak Hill College', avatar: '/avatars/ayesha-khan.png' },
  { id: 'wolfgang-schulz', name: 'Wolfgang Schulz', color: COLORS.college, activity: 'Training & studying', sentiment: 'positive', location: 'Oak Hill College', avatar: '/avatars/wolfgang-schulz.png' },
  { id: 'abigail-chen', name: 'Abigail Chen', color: COLORS.coliving, activity: 'Animation project', sentiment: 'positive', location: 'Artist Co-living', avatar: '/avatars/abigail-chen.png' },
  { id: 'francisco-lopez', name: 'Francisco Lopez', color: COLORS.coliving, activity: 'Web series project', sentiment: 'positive', location: 'Artist Co-living', avatar: '/avatars/francisco-lopez.png' },
  { id: 'hailey-johnson', name: 'Hailey Johnson', color: COLORS.coliving, activity: 'Writing novel', sentiment: 'curious', location: 'Artist Co-living', avatar: '/avatars/hailey-johnson.png' },
  { id: 'latoya-williams', name: 'Latoya Williams', color: COLORS.coliving, activity: 'Photography series', sentiment: 'positive', location: 'Artist Co-living', avatar: '/avatars/latoya-williams.png' },
  { id: 'rajiv-patel', name: 'Rajiv Patel', color: COLORS.coliving, activity: 'Preparing solo show', sentiment: 'positive', location: 'Artist Co-living', avatar: '/avatars/rajiv-patel.png' },
  { id: 'john-lin', name: 'John Lin', color: COLORS.pharmacy, activity: 'Shop keeping pharmacy', sentiment: 'neutral', location: 'Willow Market', avatar: '/avatars/john-lin.png' },
  { id: 'tom-moreno', name: 'Tom Moreno', color: COLORS.pharmacy, activity: 'Managing store', sentiment: 'negative', location: 'Willow Market', avatar: '/avatars/tom-moreno.png' },
  { id: 'eddy-lin', name: 'Eddy Lin', color: COLORS.family, activity: 'Music composition', sentiment: 'curious', location: 'Lin Family House', avatar: '/avatars/eddy-lin.png' },
  { id: 'mei-lin', name: 'Mei Lin', color: COLORS.family, activity: 'Teaching philosophy', sentiment: 'positive', location: 'Lin Family House', avatar: '/avatars/mei-lin.png' },
  { id: 'jane-moreno', name: 'Jane Moreno', color: COLORS.family, activity: 'At home', sentiment: 'neutral', location: 'Moreno House', avatar: '/avatars/jane-moreno.png' },
  { id: 'sam-moore', name: 'Sam Moore', color: COLORS.family, activity: 'Running for mayor', sentiment: 'positive', location: 'Moore House', avatar: '/avatars/sam-moore.png' },
  { id: 'jennifer-moore', name: 'Jennifer Moore', color: COLORS.family, activity: 'Preparing exhibition', sentiment: 'positive', location: 'Moore House', avatar: '/avatars/jennifer-moore.png' },
  { id: 'carmen-ortiz', name: 'Carmen Ortiz', color: COLORS.apartment, activity: 'Managing supply store', sentiment: 'positive', location: 'Harvey Oak Supply', avatar: '/avatars/carmen-ortiz.png' },
  { id: 'tamara-taylor', name: 'Tamara Taylor', color: COLORS.apartment, activity: 'Writing children\'s books', sentiment: 'positive', location: 'Home', avatar: '/avatars/tamara-taylor.png' },
  { id: 'adam-smith', name: 'Adam Smith', color: COLORS.apartment, activity: 'Writing book on creativity', sentiment: 'neutral', location: 'Home', avatar: '/avatars/adam-smith.png' },
  { id: 'giorgio-rossi', name: 'Giorgio Rossi', color: COLORS.apartment, activity: 'Math research', sentiment: 'curious', location: 'Home', avatar: '/avatars/giorgio-rossi.png' },
  { id: 'ryan-park', name: 'Ryan Park', color: COLORS.apartment, activity: 'Building mobile app', sentiment: 'positive', location: 'Home', avatar: '/avatars/ryan-park.png' },
  { id: 'yuriko-yamamoto', name: 'Yuriko Yamamoto', color: COLORS.apartment, activity: 'Tax compliance project', sentiment: 'neutral', location: 'Home', avatar: '/avatars/yuriko-yamamoto.png' },
  { id: 'arthur-burton', name: 'Arthur Burton', color: COLORS.bar, activity: 'Running the bar', sentiment: 'positive', location: 'The Bar', avatar: '/avatars/arthur-burton.png' },
  { id: 'carlos-gomez', name: 'Carlos Gomez', color: COLORS.apartment, activity: 'Writing poetry', sentiment: 'neutral', location: 'Home', avatar: '/avatars/carlos-gomez.png' },
];

// Relationships
const LINKS: AgentLink[] = [
  // Family
  { source: 'john-lin', target: 'mei-lin', type: 'family' },
  { source: 'john-lin', target: 'eddy-lin', type: 'family' },
  { source: 'mei-lin', target: 'eddy-lin', type: 'family' },
  { source: 'tom-moreno', target: 'jane-moreno', type: 'family' },
  { source: 'sam-moore', target: 'jennifer-moore', type: 'family' },
  { source: 'carmen-ortiz', target: 'tamara-taylor', type: 'family' },

  // Co-living artists
  { source: 'abigail-chen', target: 'francisco-lopez', type: 'coliving' },
  { source: 'abigail-chen', target: 'hailey-johnson', type: 'coliving' },
  { source: 'francisco-lopez', target: 'latoya-williams', type: 'coliving' },
  { source: 'hailey-johnson', target: 'rajiv-patel', type: 'coliving' },
  { source: 'latoya-williams', target: 'rajiv-patel', type: 'coliving' },
  { source: 'abigail-chen', target: 'latoya-williams', type: 'coliving' },

  // College students
  { source: 'maria-lopez', target: 'klaus-mueller', type: 'college' },
  { source: 'maria-lopez', target: 'ayesha-khan', type: 'college' },
  { source: 'klaus-mueller', target: 'wolfgang-schulz', type: 'college' },
  { source: 'ayesha-khan', target: 'wolfgang-schulz', type: 'college' },

  // Cafe regulars
  { source: 'isabella-rodriguez', target: 'maria-lopez', type: 'social' },
  { source: 'isabella-rodriguez', target: 'klaus-mueller', type: 'social' },
  { source: 'isabella-rodriguez', target: 'abigail-chen', type: 'social' },

  // Work
  { source: 'john-lin', target: 'tom-moreno', type: 'work' },
  { source: 'carmen-ortiz', target: 'john-lin', type: 'social' },

  // Mayor election interest
  { source: 'sam-moore', target: 'tom-moreno', type: 'social' },
  { source: 'sam-moore', target: 'giorgio-rossi', type: 'social' },
  { source: 'sam-moore', target: 'adam-smith', type: 'social' },
  { source: 'latoya-williams', target: 'adam-smith', type: 'social' },
  { source: 'yuriko-yamamoto', target: 'john-lin', type: 'social' },

  // Artists & mentorship
  { source: 'jennifer-moore', target: 'abigail-chen', type: 'social' },
  { source: 'jennifer-moore', target: 'rajiv-patel', type: 'social' },

  // Bar
  { source: 'arthur-burton', target: 'tom-moreno', type: 'social' },
  { source: 'arthur-burton', target: 'carlos-gomez', type: 'social' },

  // Tech
  { source: 'ryan-park', target: 'eddy-lin', type: 'social' },
  { source: 'ryan-park', target: 'giorgio-rossi', type: 'social' },
];

export default function GraphPage() {
  const [selectedAgent, setSelectedAgent] = useState<AgentNode | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [connected, setConnected] = useState(false);
  const [simTime, setSimTime] = useState('');
  const [liveAgents, setLiveAgents] = useState<Record<string, any>>({});
  const [eventInput, setEventInput] = useState('');
  const [injecting, setInjecting] = useState(false);
  const hasInjectedRef = useRef(false);

  // Check for sandbox event from output page
  useEffect(() => {
    const sandboxEvent = sessionStorage.getItem('agentsim_sandbox_event');
    if (sandboxEvent && !hasInjectedRef.current) {
      hasInjectedRef.current = true;
      // Auto-inject the event from poll results
      setTimeout(() => {
        injectEvent(sandboxEvent);
        sessionStorage.removeItem('agentsim_sandbox_event');
      }, 1500); // Wait for connection
    }
  }, [connected]);

  const injectEvent = async (content: string) => {
    if (!content.trim() || injecting) return;

    setInjecting(true);
    try {
      const response = await fetch('http://localhost:8000/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      const data = await response.json();
      console.log('Injected:', data);
      setEventInput('');
    } catch (error) {
      console.error('Inject failed:', error);
    } finally {
      setInjecting(false);
    }
  };

  // SSE connection to backend - simpler and auto-reconnects
  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8000/events');

    eventSource.onopen = () => {
      console.log('[SSE] Connected');
      setConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const state = JSON.parse(event.data);
        const serverFeed = state.feed || [];

        // Merge new items, preserve history
        setFeed(prev => {
          const existingIds = new Set(prev.map(f => f.id));
          const newItems = serverFeed.filter((f: FeedItem) => !existingIds.has(f.id));
          if (newItems.length > 0) {
            const merged = [...newItems, ...prev];
            return merged.slice(0, 100);
          }
          return prev;
        });
        setSimTime(state.time || '');

        // Update live agent data (activity, sentiment, location)
        if (state.agents) {
          const agentMap: Record<string, any> = {};
          state.agents.forEach((a: any) => {
            agentMap[a.name.toLowerCase().replace(/\s+/g, '-')] = a;
          });
          setLiveAgents(agentMap);
        }
      } catch (e) {
        console.error('[SSE] Parse error:', e);
      }
    };

    eventSource.onerror = () => {
      console.log('[SSE] Connection lost, reconnecting...');
      setConnected(false);
      // EventSource auto-reconnects!
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#F7F6F3]">
      <TopNav />

      <div className="flex-1 flex">
        {/* Graph Area */}
        <div className="flex-1 relative">
          <D3ForceGraph
            nodes={AGENTS}
            links={LINKS}
            onNodeClick={setSelectedAgent}
          />


          {/* Legend */}
          <div className="absolute bottom-6 left-6 bg-white rounded-[12px] border border-[#F0EFEC] shadow-[0_4px_20px_rgba(0,0,0,0.06)] p-4">
            <div className="text-[11px] font-semibold text-[#8E8E93] mb-3">LOCATIONS</div>
            <div className="flex flex-col gap-2">
              {Object.entries(COLORS).map(([key, color]) => (
                <div key={key} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-[11px] text-[#6B6B6B] capitalize">{key}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Stats */}
          <div className="absolute top-6 right-6 bg-white rounded-[12px] border border-[#F0EFEC] shadow-[0_4px_20px_rgba(0,0,0,0.06)] p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[11px] font-semibold text-[#8E8E93]">SIMULATION</div>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-[#22C55E] animate-pulse' : 'bg-[#8E8E93]'}`} />
                <span className="text-[10px] text-[#8E8E93]">{connected ? simTime || 'Live' : 'Offline'}</span>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-4">
                <span className="text-[12px] text-[#6B6B6B]">Agents</span>
                <span className="text-[13px] font-semibold text-[#2D2D2D]">{AGENTS.length}</span>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-[12px] text-[#6B6B6B]">Connections</span>
                <span className="text-[13px] font-semibold text-[#2D2D2D]">{LINKS.length}</span>
              </div>
            </div>
          </div>

          {/* Event Injector - Bottom Center */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10">
            <div className="bg-white/90 backdrop-blur-sm rounded-full border border-[#E5E5E5] shadow-sm px-4 py-2 flex items-center gap-2 w-[340px]">
              <input
                type="text"
                value={eventInput}
                onChange={(e) => setEventInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    injectEvent(eventInput);
                  }
                }}
                placeholder="Announce something..."
                className="flex-1 text-[12px] text-[#2D2D2D] placeholder-[#AEAEB2] bg-transparent outline-none"
                disabled={injecting}
              />
              <button
                onClick={() => injectEvent(eventInput)}
                disabled={!eventInput.trim() || injecting}
                className="flex items-center justify-center w-7 h-7 rounded-full bg-[#7C9070] text-white hover:bg-[#6A7D60] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {injecting ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* Live Feed - Bottom Right Vertical Stack */}
          <div className="absolute bottom-6 right-6 flex flex-col gap-3 w-[300px] max-h-[450px] overflow-y-auto">
            {feed.slice(0, 20).map((item, i) => (
              <div
                key={item.id || i}
                className="bg-white rounded-[12px] border border-[#E5E5E5] shadow-[0_4px_12px_rgba(0,0,0,0.08)] px-4 py-3"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    item.type === 'conversation' ? 'bg-[#7C9070]' :
                    item.type === 'thought' ? 'bg-[#5B9BD5]' :
                    item.type === 'reaction' ? 'bg-[#E9C46A]' :
                    item.type === 'event' ? 'bg-[#E07A5F]' :
                    'bg-[#9B8AA8]'
                  }`} />
                  <span className="text-[12px] font-semibold text-[#2D2D2D]">{item.agent_name || '📢 Event'}</span>
                  <span className="text-[10px] text-[#8E8E93] ml-auto">{item.type}</span>
                </div>
                <div className="text-[13px] text-[#4A4A4A] leading-relaxed">{item.content}</div>
              </div>
            ))}
            {feed.length === 0 && connected && (
              <div className="bg-white/80 rounded-[12px] px-4 py-3 text-[12px] text-[#8E8E93]">
                Waiting for activity...
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        {selectedAgent && (
          <div className="w-[320px] bg-white border-l border-[#F0EFEC] p-6 overflow-y-auto">
            <div className="flex flex-col gap-5">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {selectedAgent.avatar ? (
                    <img
                      src={selectedAgent.avatar}
                      alt={selectedAgent.name}
                      className="w-14 h-14 rounded-full object-cover border-2 border-white shadow-md"
                    />
                  ) : (
                    <div
                      className="w-14 h-14 rounded-full flex items-center justify-center text-white text-lg font-semibold"
                      style={{ backgroundColor: selectedAgent.color }}
                    >
                      {selectedAgent.name.split(' ').map(n => n[0]).join('')}
                    </div>
                  )}
                  <div>
                    <div className="text-[15px] font-semibold text-[#2D2D2D]">{selectedAgent.name}</div>
                    <div className="text-[12px] text-[#8E8E93]">{selectedAgent.location}</div>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="text-[#8E8E93] hover:text-[#2D2D2D] transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Activity - Live from backend */}
              {(() => {
                const live = liveAgents[selectedAgent.id];
                return (
                  <div className="bg-[#F7F6F3] rounded-[10px] p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-[11px] font-semibold text-[#8E8E93]">CURRENT ACTIVITY</div>
                      {live?.can_socialize && (
                        <span className="text-[9px] bg-[#E8F5E9] text-[#7C9070] px-1.5 py-0.5 rounded-full">Available</span>
                      )}
                    </div>
                    <div className="text-[13px] text-[#2D2D2D]">{live?.activity || selectedAgent.activity}</div>
                    {live?.location && (
                      <div className="text-[11px] text-[#8E8E93] mt-1">📍 {live.location}</div>
                    )}
                    {live?.current_thought && (
                      <div className="text-[11px] text-[#6B6B6B] mt-2 italic">"{live.current_thought}"</div>
                    )}
                  </div>
                );
              })()}

              {/* Sentiment - Live */}
              {(() => {
                const live = liveAgents[selectedAgent.id];
                const sentiment = live?.sentiment || selectedAgent.sentiment;
                return (
                  <div>
                    <div className="text-[11px] font-semibold text-[#8E8E93] mb-2">SENTIMENT</div>
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor:
                            sentiment === 'positive' ? '#22C55E' :
                            sentiment === 'negative' ? '#EF4444' :
                            sentiment === 'curious' ? '#5B9BD5' : '#9B8AA8'
                        }}
                      />
                      <span className="text-[13px] capitalize text-[#2D2D2D]">{sentiment}</span>
                    </div>
                  </div>
                );
              })()}

              {/* Connections */}
              <div>
                <div className="text-[11px] font-semibold text-[#8E8E93] mb-2">
                  CONNECTIONS ({LINKS.filter(l => l.source === selectedAgent.id || l.target === selectedAgent.id).length})
                </div>
                <div className="flex flex-col gap-2">
                  {LINKS
                    .filter(l => l.source === selectedAgent.id || l.target === selectedAgent.id)
                    .map((link, i) => {
                      const otherId = link.source === selectedAgent.id ? link.target : link.source;
                      const other = AGENTS.find(a => a.id === otherId);
                      return (
                        <div key={i} className="flex items-center justify-between py-2 border-b border-[#F0EFEC] last:border-0">
                          <span className="text-[12px] text-[#2D2D2D]">{other?.name}</span>
                          <span className="text-[11px] text-[#8E8E93] capitalize">{link.type}</span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
