'use client';

import { useEffect, useRef, useState } from 'react';

interface DistributionPipelineProps {
  className?: string;
}

export default function DistributionPipeline({ className = '' }: DistributionPipelineProps) {
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

  const centerX = 150;

  // Supplier/Factory icon at top
  const SupplierIcon = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0s'
      }}
    >
      {/* Factory building */}
      <rect x={centerX - 30} y="25" width="60" height="35" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="2" />
      {/* Chimneys */}
      <rect x={centerX - 20} y="15" width="8" height="15" fill="white" stroke="#2600FF" strokeWidth="1" />
      <rect x={centerX + 12} y="15" width="8" height="15" fill="white" stroke="#2600FF" strokeWidth="1" />
      {/* Windows */}
      <rect x={centerX - 20} y="35" width="10" height="10" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.4" />
      <rect x={centerX - 5} y="35" width="10" height="10" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.4" />
      <rect x={centerX + 10} y="35" width="10" height="10" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.4" />
      {/* Smoke animation */}
      {isVisible && (
        <>
          <circle cx={centerX - 16} cy="10" r="3" fill="#2600FF" fillOpacity="0.2">
            <animate attributeName="cy" values="10;0;10" dur="2s" repeatCount="indefinite" />
            <animate attributeName="fill-opacity" values="0.2;0;0.2" dur="2s" repeatCount="indefinite" />
          </circle>
          <circle cx={centerX + 16} cy="10" r="3" fill="#2600FF" fillOpacity="0.2">
            <animate attributeName="cy" values="10;0;10" dur="2.5s" repeatCount="indefinite" begin="0.5s" />
            <animate attributeName="fill-opacity" values="0.2;0;0.2" dur="2.5s" repeatCount="indefinite" begin="0.5s" />
          </circle>
        </>
      )}
      <text x={centerX} y="75" textAnchor="middle" className="fill-black text-[9px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Suppliers
      </text>
    </g>
  );

  // Warehouse in middle
  const WarehouseIcon = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0.5s'
      }}
    >
      {/* Main building */}
      <rect x={centerX - 35} y="115" width="70" height="45" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="2" />
      {/* Roof */}
      <path d={`M${centerX - 38} 115 L${centerX} 95 L${centerX + 38} 115`} fill="white" stroke="#2600FF" strokeWidth="1.5" strokeLinejoin="round" />
      {/* Shelves inside */}
      <line x1={centerX - 25} y1="125" x2={centerX + 25} y2="125" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3" />
      <line x1={centerX - 25} y1="135" x2={centerX + 25} y2="135" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3" />
      <line x1={centerX - 25} y1="145" x2={centerX + 25} y2="145" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3" />
      {/* Boxes on shelves */}
      {[
        { x: centerX - 20, y: 127, w: 8, h: 6 },
        { x: centerX - 8, y: 127, w: 10, h: 6 },
        { x: centerX + 8, y: 127, w: 8, h: 6 },
        { x: centerX - 15, y: 137, w: 12, h: 6 },
        { x: centerX + 5, y: 137, w: 10, h: 6 },
        { x: centerX - 22, y: 147, w: 8, h: 6 },
        { x: centerX - 5, y: 147, w: 14, h: 6 },
        { x: centerX + 12, y: 147, w: 8, h: 6 },
      ].map((box, i) => (
        <rect
          key={i}
          x={box.x}
          y={box.y}
          width={box.w}
          height={box.h}
          fill="#2600FF"
          fillOpacity="0.15"
          rx="1"
        />
      ))}
      {/* Loading dock */}
      <rect x={centerX - 8} y="150" width="16" height="10" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
      <text x={centerX} y="175" textAnchor="middle" className="fill-black text-[9px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Your Warehouse
      </text>
    </g>
  );

  // Customer icons at bottom (B2B and Retail)
  const CustomerIcons = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '1s'
      }}
    >
      {/* B2B Customer - Office building */}
      <g>
        <rect x="55" y="215" width="40" height="50" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="2" />
        {/* Windows grid */}
        {[0, 1, 2, 3].map((row) => (
          [0, 1, 2].map((col) => (
            <rect
              key={`${row}-${col}`}
              x={60 + col * 12}
              y={220 + row * 11}
              width="8"
              height="7"
              fill="none"
              stroke="#2600FF"
              strokeWidth="0.5"
              strokeOpacity="0.3"
            />
          ))
        ))}
        <text x="75" y="280" textAnchor="middle" className="fill-black text-[9px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
          B2B
        </text>
      </g>

      {/* Retail Customer - Store */}
      <g>
        <rect x="205" y="230" width="40" height="35" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="2" />
        {/* Awning */}
        <path d="M203 230 L225 220 L247 230" fill="white" stroke="#2600FF" strokeWidth="1.5" strokeLinejoin="round" />
        {/* Door */}
        <rect x="220" y="245" width="10" height="20" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
        {/* Window */}
        <rect x="210" y="240" width="8" height="12" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.4" />
        <text x="225" y="280" textAnchor="middle" className="fill-black text-[9px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
          Retail
        </text>
      </g>
    </g>
  );

  // Flow arrows and products
  const FlowElements = () => (
    <g>
      {/* Supplier to Warehouse */}
      <line
        x1={centerX}
        y1="65"
        x2={centerX}
        y2="95"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '0.3s' }}
      />

      {/* Warehouse to Customers */}
      <path
        d={`M${centerX} 165 Q${centerX} 190 75 210`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '0.8s' }}
      />
      <path
        d={`M${centerX} 165 Q${centerX} 190 225 210`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '0.8s' }}
      />

      {/* Animated products flowing down */}
      {isVisible && (
        <>
          {/* Supplier to warehouse */}
          <rect x="-4" y="-4" width="8" height="8" fill="#2600FF" fillOpacity="0.7" rx="1">
            <animateMotion dur="2s" repeatCount="indefinite" path={`M${centerX} 65 L${centerX} 95`} />
          </rect>
          <rect x="-4" y="-4" width="8" height="8" fill="#2600FF" fillOpacity="0.7" rx="1">
            <animateMotion dur="2s" repeatCount="indefinite" begin="1s" path={`M${centerX} 65 L${centerX} 95`} />
          </rect>

          {/* Warehouse to B2B */}
          <rect x="-3" y="-3" width="6" height="6" fill="#2600FF" fillOpacity="0.6" rx="1">
            <animateMotion dur="2.5s" repeatCount="indefinite" begin="0.5s" path={`M${centerX} 165 Q${centerX} 190 75 210`} />
          </rect>

          {/* Warehouse to Retail */}
          <rect x="-3" y="-3" width="6" height="6" fill="#2600FF" fillOpacity="0.6" rx="1">
            <animateMotion dur="2.5s" repeatCount="indefinite" begin="1.2s" path={`M${centerX} 165 Q${centerX} 190 225 210`} />
          </rect>
        </>
      )}
    </g>
  );

  // Document flow (PO going up, Invoice going down)
  const DocumentFlow = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '1.5s'
      }}
    >
      {/* PO Document going to supplier */}
      <g>
        <rect x="185" y="45" width="20" height="25" fill="white" stroke="#2600FF" strokeWidth="1" rx="2" />
        <line x1="188" y1="52" x2="202" y2="52" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <line x1="188" y1="57" x2="200" y2="57" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <line x1="188" y1="62" x2="198" y2="62" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <text x="195" y="80" textAnchor="middle" className="fill-[#2600FF] text-[7px] font-medium opacity-60" style={{ fontFamily: 'Inter, sans-serif' }}>
          PO
        </text>
        {/* Arrow pointing up */}
        <path d="M195 40 L195 35 M192 38 L195 35 L198 38" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" fill="none" />
      </g>

      {/* Invoice coming from supplier */}
      <g>
        <rect x="95" y="45" width="20" height="25" fill="white" stroke="#2600FF" strokeWidth="1" rx="2" />
        <line x1="98" y1="52" x2="112" y2="52" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <line x1="98" y1="57" x2="110" y2="57" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <line x1="98" y1="62" x2="108" y2="62" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.4" />
        <text x="105" y="80" textAnchor="middle" className="fill-[#2600FF] text-[7px] font-medium opacity-60" style={{ fontFamily: 'Inter, sans-serif' }}>
          INV
        </text>
        {/* Arrow pointing down */}
        <path d="M105 75 L105 85 M102 82 L105 85 L108 82" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" fill="none" />
      </g>
    </g>
  );

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 300"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <FlowElements />
        <SupplierIcon />
        <WarehouseIcon />
        <CustomerIcons />
        <DocumentFlow />
      </svg>
    </div>
  );
}
