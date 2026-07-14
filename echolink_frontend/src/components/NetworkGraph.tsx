import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import type { Recommendation } from '../api';

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  trackname: string;
  artistname: string;
  isSeed: boolean;
  connections: number;
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  jaccard: number;
  confidence: number;
  pair_count: number;
  source: GraphNode;
  target: GraphNode;
}

interface Props {
  seedTrack: string;
  seedArtist: string;
  seedItem: string;
  recommendations: Recommendation[];
  onNodeClick: (item: string) => void;
}

const MAX_NODES = 40;

export default function NetworkGraph({ seedTrack, seedArtist, seedItem, recommendations, onNodeClick }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 800, h: 500 });
  const simRef = useRef<d3.Simulation<GraphNode, GraphLink> | null>(null);

  // Build graph data from seed + recommendations
  const buildGraph = useCallback(() => {
    const nodes: GraphNode[] = [];
    const links: GraphLink[] = [];

    // Seed node
    const seedNode: GraphNode = {
      id: seedItem,
      trackname: seedTrack,
      artistname: seedArtist,
      isSeed: true,
      connections: recommendations.length,
      x: dims.w / 2,
      y: dims.h / 2,
      fx: dims.w / 2,
      fy: dims.h / 2,
    };
    nodes.push(seedNode);

    const displayed = recommendations.slice(0, MAX_NODES - 1);
    displayed.forEach(rec => {
      const node: GraphNode = {
        id: rec.item,
        trackname: rec.trackname,
        artistname: rec.artistname,
        isSeed: false,
        connections: 1,
      };
      nodes.push(node);
      links.push({
        source: seedNode,
        target: node,
        jaccard: rec.jaccard,
        confidence: rec.confidence,
        pair_count: rec.pair_count,
      } as GraphLink);
    });

    return { nodes, links };
  }, [seedItem, seedTrack, seedArtist, recommendations, dims]);

  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      const entry = entries[0];
      setDims({ w: entry.contentRect.width, h: entry.contentRect.height });
    });
    ro.observe(el.parentElement!);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    const svg = svgRef.current;
    const tooltip = tooltipRef.current;
    if (!svg || !tooltip || recommendations.length === 0) return;

    // Clear previous
    d3.select(svg).selectAll('*').remove();
    if (simRef.current) simRef.current.stop();

    const { nodes, links } = buildGraph();
    const maxJacc = d3.max(links, l => l.jaccard) || 1;

    const jaccScale = d3.scaleLinear().domain([0, maxJacc]).range([1, 4]);
    const nodeRadius = (n: GraphNode) => n.isSeed ? 22 : 10 + n.connections * 2;

    // Zoom
    const g = d3.select(svg).append('g');
    d3.select(svg).call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.4, 3])
        .on('zoom', (event) => g.attr('transform', event.transform))
    );

    // Gradient defs
    const defs = d3.select(svg).append('defs');
    const grad = defs.append('radialGradient').attr('id', 'seed-grad');
    grad.append('stop').attr('offset', '0%').attr('stop-color', '#a78bfa');
    grad.append('stop').attr('offset', '100%').attr('stop-color', '#06b6d4');

    // Simulation
    const sim = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(d => 80 + (1 - d.jaccard) * 80)
        .strength(0.6)
      )
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(dims.w / 2, dims.h / 2))
      .force('collision', d3.forceCollide<GraphNode>().radius(n => nodeRadius(n) + 8));
    simRef.current = sim as unknown as d3.Simulation<GraphNode, GraphLink>;

    // Links
    const linkEl = g.append('g').selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', 'rgba(124,58,237,0.35)')
      .attr('stroke-width', d => jaccScale(d.jaccard))
      .attr('stroke-linecap', 'round');

    // Nodes
    const nodeEl = g.append('g').selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(
        (d3.drag<SVGGElement, GraphNode>()
          .on('start', (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart();
            d.fx = d.x; d.fy = d.y;
          })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
          .on('end', (event, d) => {
            if (!event.active) sim.alphaTarget(0);
            if (!d.isSeed) { d.fx = null; d.fy = null; }
          })
        ) as unknown as (sel: any) => void
      );

    // Node circles
    nodeEl.append('circle')
      .attr('r', nodeRadius)
      .attr('fill', d => d.isSeed ? 'url(#seed-grad)' : 'var(--surface-3)')
      .attr('stroke', d => d.isSeed ? '#a78bfa' : 'rgba(124,58,237,0.3)')
      .attr('stroke-width', d => d.isSeed ? 2.5 : 1.5);

    // Labels for seed
    nodeEl.filter(d => d.isSeed)
      .append('text')
      .attr('dy', 36)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '11px')
      .attr('font-weight', '700')
      .attr('font-family', 'Inter, sans-serif')
      .text(d => d.trackname.length > 18 ? d.trackname.slice(0, 18) + '…' : d.trackname);

    // Hover tooltip
    nodeEl
      .on('mousemove', (event, d) => {
        const link = links.find(l => (l.target as GraphNode).id === d.id);
        tooltip.innerHTML = `
          <div class="network-tooltip-title">${d.trackname}</div>
          <div class="network-tooltip-row">${d.artistname}</div>
          ${link ? `
            <div class="network-tooltip-row" style="margin-top:8px">
              Jaccard <span>${link.jaccard.toFixed(3)}</span>
            </div>
            <div class="network-tooltip-row">
              Confidence <span>${link.confidence.toFixed(3)}</span>
            </div>
            <div class="network-tooltip-row">
              Pair count <span>${link.pair_count.toLocaleString()}</span>
            </div>
          ` : ''}
        `;
        const box = svg.getBoundingClientRect();
        tooltip.style.left = (event.clientX - box.left + 12) + 'px';
        tooltip.style.top  = (event.clientY - box.top  + 12) + 'px';
        tooltip.classList.add('visible');
      })
      .on('mouseleave', () => tooltip.classList.remove('visible'))
      .on('click', (_event, d) => {
        if (!d.isSeed) onNodeClick(d.id);
      });

    // Highlight on hover
    nodeEl
      .on('mouseenter', function(_, d) {
        if (d.isSeed) return;
        d3.select(this).select('circle')
          .attr('fill', 'rgba(124,58,237,0.5)')
          .attr('stroke', '#a78bfa');
      })
      .on('mouseleave.highlight', function(_, d) {
        if (d.isSeed) return;
        d3.select(this).select('circle')
          .attr('fill', 'var(--surface-3)')
          .attr('stroke', 'rgba(124,58,237,0.3)');
      });

    sim.on('tick', () => {
      linkEl
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);
      nodeEl.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => { sim.stop(); };
  }, [buildGraph, recommendations, dims, onNodeClick]);

  return (
    <div className="network-wrap">
      <svg ref={svgRef} className="network-svg" />
      <div ref={tooltipRef} className="network-tooltip" />
      <div className="network-hint">
        🖱 Drag nodes · Scroll to zoom · Click a node to explore
      </div>
    </div>
  );
}
