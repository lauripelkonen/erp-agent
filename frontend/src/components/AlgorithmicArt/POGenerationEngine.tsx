'use client';

import { useEffect, useRef, useState } from 'react';

interface POGenerationEngineProps {
  className?: string;
}

export default function POGenerationEngine({ className = '' }: POGenerationEngineProps) {
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
  const centerY = 140;

  // Input: Inventory levels (bar chart declining)
  const InventoryInput = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0s'
      }}
    >
      <rect x="20" y="70" width="70" height="55" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

      {/* Bar chart */}
      <g>
        {[
          { x: 30, h: 30, delay: 0 },
          { x: 42, h: 25, delay: 0.1 },
          { x: 54, h: 18, delay: 0.2 },
          { x: 66, h: 10, delay: 0.3 },
        ].map((bar, i) => (
          <rect
            key={i}
            x={bar.x}
            y={115 - bar.h}
            width="8"
            height={bar.h}
            fill="#2600FF"
            fillOpacity="0.3"
            rx="1"
            className="transition-all duration-500"
            style={{ transitionDelay: `${0.5 + bar.delay}s` }}
          >
            {isVisible && (
              <animate
                attributeName="height"
                values={`${bar.h};${bar.h - 3};${bar.h}`}
                dur="2s"
                repeatCount="indefinite"
                begin={`${bar.delay}s`}
              />
            )}
          </rect>
        ))}
        {/* Declining trend line */}
        <path
          d="M30 88 L42 93 L54 100 L74 110"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeDasharray="50"
          strokeDashoffset={isVisible ? 0 : 50}
          className="transition-all duration-1000"
          style={{ transitionDelay: '0.8s' }}
        />
        {/* Warning indicator */}
        <circle cx="74" cy="110" r="3" fill="#2600FF" fillOpacity="0.8">
          {isVisible && (
            <animate attributeName="fill-opacity" values="0.8;0.3;0.8" dur="1s" repeatCount="indefinite" />
          )}
        </circle>
      </g>

      <text x="55" y="135" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Inventory
      </text>
    </g>
  );

  // Input: Sales velocity (line chart trending)
  const SalesInput = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0.3s'
      }}
    >
      <rect x="20" y="155" width="70" height="55" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

      {/* Line chart */}
      <path
        d="M30 195 L40 188 L50 192 L60 180 L70 175 L80 165"
        fill="none"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeDasharray="80"
        strokeDashoffset={isVisible ? 0 : 80}
        className="transition-all duration-1000"
        style={{ transitionDelay: '1s' }}
      />
      {/* Data points */}
      {[
        { x: 30, y: 195 },
        { x: 40, y: 188 },
        { x: 50, y: 192 },
        { x: 60, y: 180 },
        { x: 70, y: 175 },
        { x: 80, y: 165 },
      ].map((point, i) => (
        <circle
          key={i}
          cx={point.x}
          cy={point.y}
          r="2"
          fill="#2600FF"
          fillOpacity={isVisible ? 0.6 : 0}
          className="transition-all duration-300"
          style={{ transitionDelay: `${1.2 + i * 0.1}s` }}
        />
      ))}
      {/* Up arrow indicator */}
      <path d="M78 165 L80 160 L82 165" stroke="#2600FF" strokeWidth="1.5" fill="none" strokeLinecap="round" />

      <text x="55" y="220" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Sales Velocity
      </text>
    </g>
  );

  // Input: Supplier data (list icon)
  const SupplierInput = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0.6s'
      }}
    >
      <rect x="20" y="240" width="70" height="45" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

      {/* List items */}
      {[0, 1, 2].map((i) => (
        <g key={i}>
          <circle cx="30" cy={252 + i * 10} r="2" fill="#2600FF" fillOpacity="0.4" />
          <line
            x1="36"
            y1={252 + i * 10}
            x2={55 + (i === 1 ? 10 : i === 2 ? 5 : 15)}
            y2={252 + i * 10}
            stroke="#2600FF"
            strokeWidth="2"
            strokeOpacity="0.2"
            strokeLinecap="round"
          />
        </g>
      ))}

      <text x="55" y="295" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Suppliers
      </text>
    </g>
  );

  // Central AI processor
  const AIProcessor = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0.9s'
      }}
    >
      {/* Outer ring */}
      <circle cx={centerX} cy={centerY} r="35" fill="white" stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.3" />
      {/* Inner circle */}
      <circle cx={centerX} cy={centerY} r="28" fill="white" stroke="#2600FF" strokeWidth="2" />

      {/* AI/Brain icon */}
      <g>
        {/* Central processing unit */}
        <rect x={centerX - 10} y={centerY - 10} width="20" height="20" fill="none" stroke="#2600FF" strokeWidth="1.5" rx="3" />
        {/* Connection points */}
        <line x1={centerX} y1={centerY - 10} x2={centerX} y2={centerY - 18} stroke="#2600FF" strokeWidth="1.5" />
        <line x1={centerX} y1={centerY + 10} x2={centerX} y2={centerY + 18} stroke="#2600FF" strokeWidth="1.5" />
        <line x1={centerX - 10} y1={centerY} x2={centerX - 18} y2={centerY} stroke="#2600FF" strokeWidth="1.5" />
        <line x1={centerX + 10} y1={centerY} x2={centerX + 18} y2={centerY} stroke="#2600FF" strokeWidth="1.5" />
        {/* Inner dot */}
        <circle cx={centerX} cy={centerY} r="4" fill="#2600FF" fillOpacity="0.3">
          {isVisible && (
            <animate attributeName="fill-opacity" values="0.3;0.8;0.3" dur="1.5s" repeatCount="indefinite" />
          )}
        </circle>
      </g>

      {/* Pulsing ring */}
      {isVisible && (
        <circle cx={centerX} cy={centerY} r="28" fill="none" stroke="#2600FF" strokeWidth="1">
          <animate attributeName="r" values="28;40;28" dur="2s" repeatCount="indefinite" />
          <animate attributeName="stroke-opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite" />
        </circle>
      )}

      <text x={centerX} y={centerY + 50} textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        AI Engine
      </text>
    </g>
  );

  // Output: Generated PO document
  const POOutput = () => (
    <g
      className="transition-all duration-700"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '1.5s'
      }}
    >
      {/* Document */}
      <rect x="210" y="100" width="60" height="80" fill="white" stroke="#2600FF" strokeWidth="2" rx="4" />
      {/* Document corner fold */}
      <path d="M255 100 L270 100 L270 115 L255 115 Z" fill="white" stroke="#2600FF" strokeWidth="1.5" />
      <path d="M255 100 L255 115 L270 115" fill="none" stroke="#2600FF" strokeWidth="1.5" />

      {/* PO header */}
      <rect x="218" y="108" width="30" height="6" fill="#2600FF" fillOpacity="0.2" rx="1" />

      {/* Content lines */}
      {[0, 1, 2, 3, 4].map((i) => (
        <line
          key={i}
          x1="218"
          y1={125 + i * 10}
          x2={250 - (i % 2) * 10}
          y2={125 + i * 10}
          stroke="#2600FF"
          strokeWidth="2"
          strokeOpacity="0.15"
          strokeLinecap="round"
          strokeDasharray="40"
          strokeDashoffset={isVisible ? 0 : 40}
          className="transition-all duration-500"
          style={{ transitionDelay: `${1.8 + i * 0.1}s` }}
        />
      ))}

      {/* Checkmark when complete */}
      <g
        className="transition-all duration-500"
        style={{
          opacity: isVisible ? 1 : 0,
          transitionDelay: '2.5s'
        }}
      >
        <circle cx="260" cy="170" r="8" fill="#2600FF" fillOpacity="0.1" stroke="#2600FF" strokeWidth="1" />
        <path d="M255 170 L258 173 L265 166" fill="none" stroke="#2600FF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </g>

      <text x="240" y="195" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Purchase Order
      </text>
    </g>
  );

  // Connection arrows from inputs to AI
  const InputConnections = () => (
    <g>
      {/* Inventory to AI */}
      <path
        d={`M90 97 Q110 97 ${centerX - 35} ${centerY - 10}`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '1s' }}
      />
      {/* Sales to AI */}
      <path
        d={`M90 182 Q110 160 ${centerX - 35} ${centerY}`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '1.1s' }}
      />
      {/* Supplier to AI */}
      <path
        d={`M90 262 Q110 220 ${centerX - 35} ${centerY + 10}`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeOpacity={isVisible ? 0.2 : 0}
        strokeDasharray="4 4"
        className="transition-all duration-700"
        style={{ transitionDelay: '1.2s' }}
      />

      {/* Animated data flowing to AI */}
      {isVisible && (
        <>
          <circle r="3" fill="#2600FF" opacity="0.7">
            <animateMotion dur="2s" repeatCount="indefinite" path={`M90 97 Q110 97 ${centerX - 35} ${centerY - 10}`} />
          </circle>
          <circle r="3" fill="#2600FF" opacity="0">
            <animateMotion dur="2s" repeatCount="indefinite" begin="0.7s" path={`M90 182 Q110 160 ${centerX - 35} ${centerY}`} />
            <animate attributeName="opacity" values="0;0.7;0.7;0.7" dur="2s" repeatCount="indefinite" begin="0.7s" />
          </circle>
          <circle r="3" fill="#2600FF" opacity="0">
            <animateMotion dur="2s" repeatCount="indefinite" begin="1.4s" path={`M90 262 Q110 220 ${centerX - 35} ${centerY + 10}`} />
            <animate attributeName="opacity" values="0;0.7;0.7;0.7" dur="2s" repeatCount="indefinite" begin="1.4s" />
          </circle>
        </>
      )}
    </g>
  );

  // Connection from AI to PO output
  const OutputConnection = () => (
    <g>
      <path
        d={`M${centerX + 35} ${centerY} Q190 ${centerY} 210 ${centerY}`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.3 : 0}
        className="transition-all duration-700"
        style={{ transitionDelay: '1.3s' }}
      />
      {/* Arrow head */}
      <path
        d="M205 135 L210 140 L205 145"
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity={isVisible ? 0.3 : 0}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="transition-all duration-700"
        style={{ transitionDelay: '1.4s' }}
      />

      {/* Animated output */}
      {isVisible && (
        <rect x="-4" y="-4" width="8" height="8" fill="#2600FF" rx="1" opacity="0">
          <animateMotion dur="1.5s" repeatCount="indefinite" begin="2s" path={`M${centerX + 35} ${centerY} Q190 ${centerY} 210 ${centerY}`} />
          <animate attributeName="opacity" values="0;0.6;0.6;0.6" dur="1.5s" repeatCount="indefinite" begin="2s" />
        </rect>
      )}
    </g>
  );

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 310"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <InputConnections />
        <OutputConnection />
        <InventoryInput />
        <SalesInput />
        <SupplierInput />
        <AIProcessor />
        <POOutput />
      </svg>
    </div>
  );
}
