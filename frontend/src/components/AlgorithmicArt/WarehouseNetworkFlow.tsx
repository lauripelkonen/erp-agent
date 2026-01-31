'use client';

import { useEffect, useRef, useState } from 'react';

interface WarehouseNetworkFlowProps {
  className?: string;
}

export default function WarehouseNetworkFlow({ className = '' }: WarehouseNetworkFlowProps) {
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

  // Warehouse positions (triangle layout)
  const warehouses = [
    { id: 1, x: 150, y: 50, stock: 0.8, label: 'HQ' },
    { id: 2, x: 50, y: 200, stock: 0.4, label: 'West' },
    { id: 3, x: 250, y: 200, stock: 0.6, label: 'East' },
  ];

  // Connection paths between warehouses
  const connections = [
    { from: warehouses[0], to: warehouses[1], path: 'M150 80 Q100 140 50 170' },
    { from: warehouses[0], to: warehouses[2], path: 'M150 80 Q200 140 250 170' },
    { from: warehouses[1], to: warehouses[2], path: 'M80 200 Q150 230 220 200' },
  ];

  // Warehouse building icon
  const WarehouseIcon = ({ x, y, stock, label, delay }: { x: number; y: number; stock: number; label: string; delay: number }) => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: `${delay}s`
      }}
    >
      {/* Warehouse building */}
      <rect
        x={x - 25}
        y={y - 15}
        width="50"
        height="35"
        fill="white"
        stroke="#2600FF"
        strokeWidth="1.5"
        rx="2"
      />
      {/* Roof */}
      <path
        d={`M${x - 28} ${y - 15} L${x} ${y - 30} L${x + 28} ${y - 15}`}
        fill="white"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      {/* Door */}
      <rect
        x={x - 6}
        y={y + 5}
        width="12"
        height="15"
        fill="none"
        stroke="#2600FF"
        strokeWidth="1"
        strokeOpacity="0.5"
      />
      {/* Stock level indicator */}
      <g>
        <rect
          x={x + 15}
          y={y - 10}
          width="6"
          height="25"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.3"
          rx="1"
        />
        <rect
          x={x + 16}
          y={y - 9 + (24 * (1 - stock))}
          width="4"
          height={24 * stock}
          fill="#2600FF"
          fillOpacity="0.4"
          rx="1"
          className="transition-all duration-1000"
          style={{ transitionDelay: `${delay + 0.5}s` }}
        >
          {isVisible && (
            <animate
              attributeName="height"
              values={`${24 * stock};${24 * (stock - 0.1)};${24 * stock}`}
              dur="3s"
              repeatCount="indefinite"
              begin={`${delay}s`}
            />
          )}
        </rect>
      </g>
      {/* Label */}
      <text
        x={x}
        y={y + 45}
        textAnchor="middle"
        className="fill-black text-[9px] font-medium opacity-40"
        style={{ fontFamily: 'Inter, sans-serif' }}
      >
        {label}
      </text>
    </g>
  );

  // Animated package traveling on path
  const TravelingPackage = ({ path, delay, duration }: { path: string; delay: number; duration: number }) => {
    if (!isVisible) return null;

    return (
      <g opacity="0">
        {/* Package box */}
        <g>
          <rect
            x="-5"
            y="-5"
            width="10"
            height="10"
            fill="#2600FF"
            rx="1"
          />
          <line x1="-5" y1="0" x2="5" y2="0" stroke="white" strokeWidth="0.5" />
          <line x1="0" y1="-5" x2="0" y2="5" stroke="white" strokeWidth="0.5" />
          <animateMotion
            dur={`${duration}s`}
            repeatCount="indefinite"
            begin={`${delay}s`}
            path={path}
          />
        </g>
        <animate
          attributeName="opacity"
          values="0;0.8;0.8;0.8"
          dur={`${duration}s`}
          repeatCount="indefinite"
          begin={`${delay}s`}
        />
      </g>
    );
  };

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <defs>
          <filter id="warehouseGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Connection paths */}
        {connections.map((conn, i) => (
          <g key={`conn-${i}`}>
            {/* Path line */}
            <path
              d={conn.path}
              fill="none"
              stroke="#2600FF"
              strokeWidth="2"
              strokeOpacity={isVisible ? 0.2 : 0}
              strokeDasharray="4 4"
              className="transition-all duration-1000"
              style={{ transitionDelay: `${0.3 + i * 0.2}s` }}
            />
            {/* Animated packages */}
            <TravelingPackage path={conn.path} delay={1 + i * 1.5} duration={3 + i * 0.5} />
          </g>
        ))}

        {/* Warehouses */}
        {warehouses.map((wh, i) => (
          <WarehouseIcon
            key={wh.id}
            x={wh.x}
            y={wh.y}
            stock={wh.stock}
            label={wh.label}
            delay={i * 0.3}
          />
        ))}

        {/* Central "optimization" indicator */}
        <g
          className="transition-all duration-700"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: '1.5s'
          }}
        >
          <circle
            cx="150"
            cy="150"
            r="15"
            fill="white"
            stroke="#2600FF"
            strokeWidth="1.5"
          />
          {/* Sync/optimize icon */}
          <path
            d="M145 150 A5 5 0 1 1 155 150"
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <path
            d="M155 150 A5 5 0 1 1 145 150"
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
          <polygon points="145,147 143,150 147,150" fill="#2600FF" />
          <polygon points="155,153 157,150 153,150" fill="#2600FF" />

          {isVisible && (
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 150 150"
              to="360 150 150"
              dur="8s"
              repeatCount="indefinite"
            />
          )}
        </g>
      </svg>
    </div>
  );
}
