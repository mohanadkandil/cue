export type Sentiment = 'positive' | 'negative' | 'neutral';

export interface Agent {
  id: string;
  name: string;
  age: number;
  occupation: string;
  location: string;
  avatar: string;
  sentiment: Sentiment;
  influence: number; // 1-10
  personality: {
    openness: number;      // 0-100
    agreeableness: number; // 0-100
    extraversion: number;  // 0-100
  };
  currentThought: string;
  friends: string[];
}

export interface FeedEvent {
  id: string;
  timestamp: Date;
  message: string;
  agentId: string;
  agentAvatar: string;
}

export interface GraphNode {
  id: string;
  name: string;
  val: number; // node size
  color: string;
  sentiment: Sentiment;
}

export interface GraphLink {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}
