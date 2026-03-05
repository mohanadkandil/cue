import { Agent, FeedEvent, GraphData, Sentiment } from './types';

// Premium, sophisticated colors for creamy theme
const SENTIMENT_COLORS = {
  positive: '#2D6A4F',  // Forest green
  negative: '#9D174D',  // Wine
  neutral: '#78716C',   // Warm gray
};

const names = [
  'Elena', 'Marco', 'Sofia', 'Lucas', 'Anna', 'David', 'Clara', 'Noah',
  'Emma', 'Oliver', 'Mia', 'Liam', 'Zoe', 'Ethan', 'Luna', 'Leo',
  'Aria', 'Jack', 'Stella', 'Max', 'Ivy', 'Oscar', 'Ruby', 'Felix',
  'Violet', 'Hugo', 'Lily', 'Theo', 'Hazel', 'Kai', 'Aurora', 'Finn',
  'Nora', 'Atlas', 'Iris', 'Jasper'
];

const occupations = [
  'Software Engineer', 'Designer', 'Student', 'Teacher', 'Entrepreneur',
  'Doctor', 'Artist', 'Writer', 'Scientist', 'Chef', 'Photographer',
  'Musician', 'Lawyer', 'Architect', 'Marketing Manager'
];

const locations = [
  'Zurich', 'Geneva', 'Basel', 'Bern', 'Lausanne', 'Lucerne',
  'St. Gallen', 'Lugano', 'Winterthur', 'Zug'
];

const avatars = [
  '👩‍💻', '👨‍🎨', '🧑‍🎓', '👩‍🏫', '🧑‍💼', '👨‍⚕️', '👩‍🎤', '🧑‍🔬',
  '👨‍🍳', '👩‍🔧', '🧑‍🎭', '👨‍✈️', '👩‍🚀', '🧙', '🧝', '🧛',
  '🦸', '🦹', '🧜', '🧚', '👸', '🤴', '🥷', '🧑‍🎄'
];

const thoughts = {
  positive: [
    "This is exactly what we needed. I can see the potential here.",
    "Finally, someone gets it. This could change everything.",
    "I'm genuinely excited about this. It aligns with my values.",
    "My friends were right, this is actually promising.",
    "I was skeptical at first, but now I'm convinced.",
  ],
  negative: [
    "I don't trust this at all. Something feels off.",
    "My gut says this is a bad idea. I'm warning my friends.",
    "This goes against everything I believe in.",
    "I've seen things like this fail before. Not interested.",
    "The risks far outweigh any potential benefits here.",
  ],
  neutral: [
    "I need more information before I make up my mind.",
    "Interesting, but I'm not sure how I feel about it yet.",
    "I'll wait to see what my friends think.",
    "Could go either way. Time will tell.",
    "I'm keeping an open mind but staying cautious.",
  ],
};

function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomElement<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateAgents(): Agent[] {
  const agents: Agent[] = [];
  const sentiments: Sentiment[] = ['positive', 'negative', 'neutral'];

  for (let i = 0; i < 36; i++) {
    const sentiment = randomElement(sentiments);
    agents.push({
      id: `agent-${i}`,
      name: names[i],
      age: randomInt(22, 55),
      occupation: randomElement(occupations),
      location: randomElement(locations),
      avatar: avatars[i % avatars.length],
      sentiment,
      influence: randomInt(1, 10),
      personality: {
        openness: randomInt(20, 95),
        agreeableness: randomInt(20, 95),
        extraversion: randomInt(20, 95),
      },
      currentThought: randomElement(thoughts[sentiment]),
      friends: [],
    });
  }

  agents.forEach((agent, index) => {
    const numFriends = randomInt(1, 2);
    const possibleFriends = agents.filter((_, i) => i !== index && !agent.friends.includes(`agent-${i}`));

    for (let i = 0; i < numFriends && possibleFriends.length > 0; i++) {
      const friendIndex = randomInt(0, possibleFriends.length - 1);
      const friend = possibleFriends[friendIndex];
      agent.friends.push(friend.id);
      if (!friend.friends.includes(agent.id)) {
        friend.friends.push(agent.id);
      }
      possibleFriends.splice(friendIndex, 1);
    }
  });

  return agents;
}

export const mockAgents = generateAgents();

export function generateGraphData(agents: Agent[]): GraphData {
  const nodes = agents.map(agent => ({
    id: agent.id,
    name: agent.name,
    val: agent.influence * 2,
    color: SENTIMENT_COLORS[agent.sentiment],
    sentiment: agent.sentiment,
  }));

  const linkSet = new Set<string>();
  const links: { source: string; target: string }[] = [];

  agents.forEach(agent => {
    agent.friends.forEach(friendId => {
      const linkKey = [agent.id, friendId].sort().join('-');
      if (!linkSet.has(linkKey)) {
        linkSet.add(linkKey);
        links.push({ source: agent.id, target: friendId });
      }
    });
  });

  return { nodes, links };
}

export const mockGraphData = generateGraphData(mockAgents);

export type EventType = 'share' | 'influence' | 'disagree' | 'discuss' | 'connect';

const eventTemplates: { type: EventType; template: string }[] = [
  { type: 'share', template: '{agent1} shared thoughts with {agent2}' },
  { type: 'discuss', template: '{agent1} discussed with {agent2}' },
  { type: 'influence', template: '{agent1} influenced {agent2}' },
  { type: 'disagree', template: '{agent1} disagreed with {agent2}' },
  { type: 'connect', template: '{agent1} connected with {agent2}' },
];

export interface ExtendedFeedEvent extends FeedEvent {
  type: EventType;
  agent1Name: string;
  agent2Name: string;
}

export function generateInitialFeedEvents(): ExtendedFeedEvent[] {
  const events: ExtendedFeedEvent[] = [];
  const now = new Date();

  for (let i = 0; i < 8; i++) {
    const agent1 = randomElement(mockAgents);
    const agent2Id = randomElement(agent1.friends);
    const agent2 = mockAgents.find(a => a.id === agent2Id);

    if (agent2) {
      const eventData = randomElement(eventTemplates);
      events.push({
        id: `event-${i}`,
        timestamp: new Date(now.getTime() - i * 30000),
        message: eventData.template.replace('{agent1}', agent1.name).replace('{agent2}', agent2.name),
        agentId: agent1.id,
        agentAvatar: agent1.avatar,
        type: eventData.type,
        agent1Name: agent1.name,
        agent2Name: agent2.name,
      });
    }
  }

  return events;
}

export const mockFeedEvents = generateInitialFeedEvents();

export function getSentimentCounts(agents: Agent[]): { positive: number; negative: number; neutral: number } {
  return agents.reduce(
    (acc, agent) => {
      acc[agent.sentiment]++;
      return acc;
    },
    { positive: 0, negative: 0, neutral: 0 }
  );
}

export { SENTIMENT_COLORS };
