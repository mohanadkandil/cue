'use client';

import { useState, useCallback } from 'react';
import TopBar from '@/components/TopBar';
import GraphCanvas from '@/components/GraphCanvas';
import Sidebar from '@/components/Sidebar';
import EventInjector from '@/components/EventInjector';
import LiveFeed from '@/components/LiveFeed';
import SentimentChart from '@/components/SentimentChart';
import AgentModal from '@/components/AgentModal';
import {
  mockAgents,
  mockGraphData,
  mockFeedEvents,
  getSentimentCounts,
  generateGraphData,
  ExtendedFeedEvent,
} from '@/lib/mockData';
import { Agent, Sentiment } from '@/lib/types';

export default function Home() {
  const [agents, setAgents] = useState(mockAgents);
  const [graphData, setGraphData] = useState(mockGraphData);
  const [feedEvents, setFeedEvents] = useState<ExtendedFeedEvent[]>(mockFeedEvents);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const sentimentCounts = getSentimentCounts(agents);

  const handleNodeClick = useCallback((nodeId: string) => {
    const agent = agents.find(a => a.id === nodeId);
    if (agent) {
      setSelectedAgent(agent);
    }
  }, [agents]);

  const handleCloseModal = useCallback(() => {
    setSelectedAgent(null);
  }, []);

  const handleInjectEvent = useCallback((eventText: string) => {
    const sentiments: Sentiment[] = ['positive', 'negative', 'neutral'];
    const numAffected = Math.floor(Math.random() * 5) + 3;
    const affectedIndices = new Set<number>();

    while (affectedIndices.size < numAffected) {
      affectedIndices.add(Math.floor(Math.random() * agents.length));
    }

    const updatedAgents = agents.map((agent, index) => {
      if (affectedIndices.has(index)) {
        const newSentiment = sentiments[Math.floor(Math.random() * sentiments.length)];
        return { ...agent, sentiment: newSentiment };
      }
      return agent;
    });

    setAgents(updatedAgents);
    setGraphData(generateGraphData(updatedAgents));

    const randomAgent = updatedAgents[Math.floor(Math.random() * updatedAgents.length)];
    const friendId = randomAgent.friends[0];
    const friend = updatedAgents.find(a => a.id === friendId);

    const types = ['share', 'influence', 'discuss'] as const;
    const type = types[Math.floor(Math.random() * types.length)];

    const newEvent: ExtendedFeedEvent = {
      id: `event-${Date.now()}`,
      timestamp: new Date(),
      message: `${randomAgent.name} reacted to event`,
      agentId: randomAgent.id,
      agentAvatar: randomAgent.avatar,
      type,
      agent1Name: randomAgent.name,
      agent2Name: friend?.name || 'someone',
    };

    setFeedEvents(prev => [newEvent, ...prev.slice(0, 19)]);
  }, [agents]);

  return (
    <div className="h-screen flex flex-col bg-background">
      <TopBar />

      <div className="flex-1 flex overflow-hidden">
        <GraphCanvas graphData={graphData} onNodeClick={handleNodeClick} />

        <Sidebar>
          <EventInjector onInject={handleInjectEvent} />
          <SentimentChart counts={sentimentCounts} />
          <LiveFeed events={feedEvents} />
        </Sidebar>
      </div>

      {selectedAgent && (
        <AgentModal agent={selectedAgent} onClose={handleCloseModal} />
      )}
    </div>
  );
}
