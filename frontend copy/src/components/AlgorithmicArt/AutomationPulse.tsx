import { useEffect, useRef, useState } from 'react';

interface AutomationPulseProps {
  className?: string;
}

interface Node {
  id: number;
  x: number;
  y: number;
  label: string;
  delay: number;
}

export default function AutomationPulse({ className = '' }: AutomationPulseProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.2 }
    );

    if (svgRef.current) {
      observer.observe(svgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const center = { x: 150, y: 150 };

  // Outer nodes representing different data sources/outputs
  const nodes: Node[] = [
    { id: 1, x: 150, y: 50, label: 'Inventory', delay: 0.2 },
    { id: 2, x: 230, y: 90, label: 'Sales', delay: 0.4 },
    { id: 3, x: 260, y: 170, label: 'Suppliers', delay: 0.6 },
    { id: 4, x: 220, y: 240, label: 'Orders', delay: 0.8 },
    { id: 5, x: 150, y: 260, label: 'POs', delay: 1.0 },
    { id: 6, x: 80, y: 240, label: 'Analytics', delay: 1.2 },
    { id: 7, x: 40, y: 170, label: 'Rules', delay: 1.4 },
    { id: 8, x: 70, y: 90, label: 'History', delay: 1.6 }
  ];

  // Radiating pulse rings from center
  const PulseRings = () => {
    if (!isVisible) return null;

    return (
      <g className="pulse-rings">
        {[0, 1, 2].map((i) => (
          <circle
            key={`pulse-${i}`}
            cx={center.x}
            cy={center.y}
            r="30"
            fill="none"
            stroke="#2600FF"
            strokeWidth="1"
            strokeOpacity="0"
          >
            <animate
              attributeName="r"
              values="30;80;80"
              dur="3s"
              begin={`${i * 1}s`}
              repeatCount="indefinite"
            />
            <animate
              attributeName="stroke-opacity"
              values="0.4;0;0"
              dur="3s"
              begin={`${i * 1}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </g>
    );
  };

  // Connection lines from center to nodes
  const ConnectionLines = () => (
    <g className="connections">
      {nodes.map((node) => (
        <g key={`conn-${node.id}`}>
          {/* Static connection line */}
          <line
            x1={center.x}
            y1={center.y}
            x2={node.x}
            y2={node.y}
            stroke="#2600FF"
            strokeWidth="1"
            strokeOpacity={isVisible ? 0.15 : 0}
            className="transition-all duration-700"
            style={{ transitionDelay: `${node.delay}s` }}
          />

          {/* Animated data packet traveling along the line */}
          {isVisible && (
            <circle r="3" fill="#2600FF" fillOpacity="0.8">
              <animateMotion
                dur={`${2 + node.id * 0.3}s`}
                repeatCount="indefinite"
                begin={`${node.delay + 1}s`}
                path={`M${center.x} ${center.y} L${node.x} ${node.y}`}
              />
              <animate
                attributeName="fill-opacity"
                values="0.8;0.3;0.8"
                dur={`${2 + node.id * 0.3}s`}
                repeatCount="indefinite"
                begin={`${node.delay + 1}s`}
              />
            </circle>
          )}

          {/* Return packet (traveling back to center) */}
          {isVisible && node.id % 2 === 0 && (
            <circle r="2" fill="#2600FF" fillOpacity="0.5">
              <animateMotion
                dur={`${2.5 + node.id * 0.2}s`}
                repeatCount="indefinite"
                begin={`${node.delay + 2}s`}
                path={`M${node.x} ${node.y} L${center.x} ${center.y}`}
              />
            </circle>
          )}
        </g>
      ))}
    </g>
  );

  // Outer nodes
  const OuterNodes = () => (
    <g className="outer-nodes">
      {nodes.map((node) => (
        <g
          key={`node-${node.id}`}
          className="transition-all duration-700"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: `${node.delay}s`
          }}
        >
          {/* Node outer ring */}
          <circle
            cx={node.x}
            cy={node.y}
            r="18"
            fill="white"
            stroke="#2600FF"
            strokeWidth="1"
            strokeOpacity="0.2"
          />
          {/* Node inner circle */}
          <circle
            cx={node.x}
            cy={node.y}
            r="12"
            fill="white"
            stroke="#2600FF"
            strokeWidth="1.5"
          />
          {/* Node center dot */}
          <circle
            cx={node.x}
            cy={node.y}
            r="4"
            fill="#2600FF"
            fillOpacity="0.3"
          >
            {isVisible && (
              <animate
                attributeName="fill-opacity"
                values="0.3;0.7;0.3"
                dur={`${1.5 + node.id * 0.1}s`}
                repeatCount="indefinite"
                begin={`${node.delay + 0.5}s`}
              />
            )}
          </circle>
        </g>
      ))}
    </g>
  );

  // Central hub (AI processor)
  const CentralHub = () => (
    <g className="central-hub">
      {/* Outer glow ring */}
      <circle
        cx={center.x}
        cy={center.y}
        r="40"
        fill="none"
        stroke="#2600FF"
        strokeWidth="1"
        strokeOpacity={isVisible ? 0.1 : 0}
        className="transition-all duration-1000"
      />

      {/* Middle ring */}
      <circle
        cx={center.x}
        cy={center.y}
        r="32"
        fill="white"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.3 : 0}
        className="transition-all duration-700"
        style={{ transitionDelay: '0.2s' }}
      />

      {/* Inner ring */}
      <circle
        cx={center.x}
        cy={center.y}
        r="24"
        fill="white"
        stroke="#2600FF"
        strokeWidth="2"
        className="transition-all duration-700"
        style={{
          opacity: isVisible ? 1 : 0,
          transitionDelay: '0.3s'
        }}
      />

      {/* AI icon in center */}
      <g
        className="transition-all duration-700"
        style={{
          opacity: isVisible ? 1 : 0,
          transitionDelay: '0.5s'
        }}
      >
        {/* Brain/circuit pattern */}
        <circle cx={center.x} cy={center.y} r="10" fill="none" stroke="#2600FF" strokeWidth="1.5" />
        <circle cx={center.x} cy={center.y} r="5" fill="#2600FF" fillOpacity="0.4" />

        {/* Connection points */}
        <circle cx={center.x} cy={center.y - 10} r="2" fill="#2600FF" />
        <circle cx={center.x + 10} cy={center.y} r="2" fill="#2600FF" />
        <circle cx={center.x} cy={center.y + 10} r="2" fill="#2600FF" />
        <circle cx={center.x - 10} cy={center.y} r="2" fill="#2600FF" />
      </g>

      {/* Breathing animation on central hub */}
      {isVisible && (
        <circle
          cx={center.x}
          cy={center.y}
          r="24"
          fill="none"
          stroke="#2600FF"
          strokeWidth="2"
          strokeOpacity="0.3"
        >
          <animate attributeName="r" values="24;30;24" dur="2s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite" />
        </circle>
      )}
    </g>
  );

  // Rotating outer ring
  const RotatingRing = () => {
    if (!isVisible) return null;

    return (
      <g>
        <circle
          cx={center.x}
          cy={center.y}
          r="95"
          fill="none"
          stroke="#2600FF"
          strokeWidth="0.5"
          strokeOpacity="0.15"
          strokeDasharray="8 12"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from={`0 ${center.x} ${center.y}`}
            to={`360 ${center.x} ${center.y}`}
            dur="60s"
            repeatCount="indefinite"
          />
        </circle>

        {/* Counter-rotating inner ring */}
        <circle
          cx={center.x}
          cy={center.y}
          r="70"
          fill="none"
          stroke="#2600FF"
          strokeWidth="0.5"
          strokeOpacity="0.1"
          strokeDasharray="4 8"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from={`360 ${center.x} ${center.y}`}
            to={`0 ${center.x} ${center.y}`}
            dur="45s"
            repeatCount="indefinite"
          />
        </circle>
      </g>
    );
  };


  // Arc segments around center
  const ArcSegments = () => {
    const arcs = [
      { start: 0, end: 60 },
      { start: 90, end: 150 },
      { start: 180, end: 240 },
      { start: 270, end: 330 }
    ];

    return (
      <g>
        {arcs.map((arc, i) => {
          const r = 55;
          const startRad = (arc.start * Math.PI) / 180;
          const endRad = (arc.end * Math.PI) / 180;
          const x1 = center.x + r * Math.cos(startRad);
          const y1 = center.y + r * Math.sin(startRad);
          const x2 = center.x + r * Math.cos(endRad);
          const y2 = center.y + r * Math.sin(endRad);

          return (
            <path
              key={`arc-${i}`}
              d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
              fill="none"
              stroke="#2600FF"
              strokeWidth="2"
              strokeLinecap="round"
              className="transition-all duration-1000"
              style={{
                strokeDasharray: 60,
                strokeDashoffset: isVisible ? 0 : 60,
                transitionDelay: `${0.8 + i * 0.2}s`,
                opacity: isVisible ? 0.25 : 0
              }}
            />
          );
        })}
      </g>
    );
  };

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 300"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <defs>
          <filter id="pulseGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Subtle center glow */}
        <circle
          cx={center.x}
          cy={center.y}
          r="60"
          fill="url(#centerGlow)"
          className="transition-opacity duration-1000"
          style={{ opacity: isVisible ? 1 : 0 }}
        />

        {/* Rotating outer rings */}
        <RotatingRing />

        {/* Arc segments */}
        <ArcSegments />

        {/* Pulse rings */}
        <PulseRings />

        {/* Connection lines with data packets */}
        <ConnectionLines />

        {/* Outer nodes */}
        <OuterNodes />

        {/* Central AI hub */}
        <CentralHub />

      </svg>
    </div>
  );
}
