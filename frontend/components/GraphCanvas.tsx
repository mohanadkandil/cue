'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { GraphData } from '@/lib/types';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
});

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ForceGraphInstance = any;

interface GraphCanvasProps {
  graphData: GraphData;
  onNodeClick: (nodeId: string) => void;
}

interface NodeObject {
  id?: string | number;
  x?: number;
  y?: number;
  val?: number;
  color?: string;
  name?: string;
  [key: string]: unknown;
}

interface LinkObject {
  source?: string | number | NodeObject;
  target?: string | number | NodeObject;
  [key: string]: unknown;
}

const BG_COLOR = '#FFFDF9';
const EDGE_COLOR = '#D4D0C8';

export default function GraphCanvas({ graphData, onNodeClick }: GraphCanvasProps) {
  const graphRef = useRef<ForceGraphInstance>(null);
  const [size, setSize] = useState({ width: 1, height: 1 });
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);

    const updateSize = () => {
      const width = window.innerWidth - 320;
      const height = window.innerHeight - 56;
      setSize({ width, height });
    };

    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  useEffect(() => {
    if (graphRef.current && mounted) {
      graphRef.current.d3Force('charge')?.strength(-2500).distanceMax(800);
      graphRef.current.d3Force('link')?.distance(220);
      graphRef.current.d3Force('center')?.strength(0.1);
      graphRef.current.d3ReheatSimulation();

      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50);
      }, 2000);
    }
  }, [mounted, size]);

  const handleNodeClick = useCallback((node: NodeObject) => {
    if (node.id) {
      onNodeClick(String(node.id));
    }
  }, [onNodeClick]);

  const nodeCanvasObject = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D) => {
    const influence = (node.val as number) || 5;
    const radius = 10 + (influence / 2.5);
    const x = node.x || 0;
    const y = node.y || 0;
    const color = (node.color as string) || '#78716C';

    // Clean circle with solid fill
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Crisp white border
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Thin dark outline for definition
    ctx.beginPath();
    ctx.arc(x, y, radius + 1.25, 0, 2 * Math.PI);
    ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }, []);

  const linkCanvasObject = useCallback((link: LinkObject, ctx: CanvasRenderingContext2D) => {
    const source = link.source as NodeObject;
    const target = link.target as NodeObject;

    if (!source?.x || !source?.y || !target?.x || !target?.y) return;

    ctx.beginPath();
    ctx.strokeStyle = EDGE_COLOR;
    ctx.lineWidth = 1.5;
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);
    ctx.stroke();
  }, []);

  if (!mounted) return <div className="w-full h-full bg-background" />;

  return (
    <ForceGraph2D
      ref={graphRef}
      width={size.width}
      height={size.height}
      graphData={graphData}
      nodeCanvasObject={nodeCanvasObject}
      linkCanvasObject={linkCanvasObject}
      onNodeClick={handleNodeClick}
      nodeRelSize={5}
      linkColor={() => EDGE_COLOR}
      backgroundColor={BG_COLOR}
      cooldownTicks={400}
      d3AlphaDecay={0.008}
      d3VelocityDecay={0.15}
      warmupTicks={200}
      enableNodeDrag={true}
      minZoom={0.1}
      maxZoom={10}
    />
  );
}
