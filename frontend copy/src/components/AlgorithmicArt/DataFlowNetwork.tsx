import { useEffect, useRef, useState } from 'react';

interface DataFlowNetworkProps {
  className?: string;
}

export default function DataFlowNetwork({ className = '' }: DataFlowNetworkProps) {
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

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 500 300"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Definitions for gradients and filters */}
        <defs>
          <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.2" />
            <stop offset="50%" stopColor="#2600FF" stopOpacity="1" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0.2" />
          </linearGradient>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="nodeGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background grid pattern */}
        <g className={`transition-opacity duration-1000 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
          {[...Array(11)].map((_, i) => (
            <line
              key={`vline-${i}`}
              x1={50 * i}
              y1="0"
              x2={50 * i}
              y2="300"
              stroke="rgba(0,0,0,0.03)"
              strokeWidth="1"
            />
          ))}
          {[...Array(7)].map((_, i) => (
            <line
              key={`hline-${i}`}
              x1="0"
              y1={50 * i}
              x2="500"
              y2={50 * i}
              stroke="rgba(0,0,0,0.03)"
              strokeWidth="1"
            />
          ))}
        </g>

        {/* Connection paths - animated with stroke-dasharray */}
        <g className="connection-paths">
          {/* Path 1: Email to AI */}
          <path
            d="M80 150 C 130 150, 140 100, 190 100"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            className={`path-line ${isVisible ? 'animate-path-1' : ''}`}
            style={{
              strokeDasharray: 200,
              strokeDashoffset: isVisible ? 0 : 200,
              transition: 'stroke-dashoffset 1.5s ease-out 0.5s'
            }}
          />
          {/* Path 2: Email to AI (lower) */}
          <path
            d="M80 150 C 130 150, 140 200, 190 200"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            className={`path-line ${isVisible ? 'animate-path-2' : ''}`}
            style={{
              strokeDasharray: 200,
              strokeDashoffset: isVisible ? 0 : 200,
              transition: 'stroke-dashoffset 1.5s ease-out 0.7s'
            }}
          />
          {/* Path 3: AI upper to center */}
          <path
            d="M230 100 C 260 100, 260 150, 290 150"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            style={{
              strokeDasharray: 150,
              strokeDashoffset: isVisible ? 0 : 150,
              transition: 'stroke-dashoffset 1.2s ease-out 1.5s'
            }}
          />
          {/* Path 4: AI lower to center */}
          <path
            d="M230 200 C 260 200, 260 150, 290 150"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            style={{
              strokeDasharray: 150,
              strokeDashoffset: isVisible ? 0 : 150,
              transition: 'stroke-dashoffset 1.2s ease-out 1.7s'
            }}
          />
          {/* Path 5: ERP to Output upper */}
          <path
            d="M330 150 C 360 150, 360 100, 390 100"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            style={{
              strokeDasharray: 150,
              strokeDashoffset: isVisible ? 0 : 150,
              transition: 'stroke-dashoffset 1.2s ease-out 2.5s'
            }}
          />
          {/* Path 6: ERP to Output lower */}
          <path
            d="M330 150 C 360 150, 360 200, 390 200"
            stroke="#2600FF"
            strokeWidth="2"
            fill="none"
            strokeOpacity="0.15"
            style={{
              strokeDasharray: 150,
              strokeDashoffset: isVisible ? 0 : 150,
              transition: 'stroke-dashoffset 1.2s ease-out 2.7s'
            }}
          />
        </g>

        {/* Animated particles on paths */}
        {isVisible && (
          <g className="particles">
            <circle r="3" fill="#2600FF" filter="url(#glow)">
              <animateMotion
                dur="3s"
                repeatCount="indefinite"
                path="M80 150 C 130 150, 140 100, 190 100"
                begin="1s"
              />
            </circle>
            <circle r="3" fill="#2600FF" filter="url(#glow)">
              <animateMotion
                dur="3s"
                repeatCount="indefinite"
                path="M80 150 C 130 150, 140 200, 190 200"
                begin="1.5s"
              />
            </circle>
            <circle r="2.5" fill="#2600FF" filter="url(#glow)">
              <animateMotion
                dur="2.5s"
                repeatCount="indefinite"
                path="M230 100 C 260 100, 260 150, 290 150 C 320 150, 360 150, 360 100 L 390 100"
                begin="2s"
              />
            </circle>
            <circle r="2.5" fill="#2600FF" filter="url(#glow)">
              <animateMotion
                dur="2.5s"
                repeatCount="indefinite"
                path="M230 200 C 260 200, 260 150, 290 150 C 320 150, 360 150, 360 200 L 390 200"
                begin="2.3s"
              />
            </circle>
          </g>
        )}

        {/* Node 1: Input/Email - Document icon */}
        <g
          className={`node-email transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '0s' }}
        >
          <circle cx="60" cy="150" r="28" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.3" />
          <circle cx="60" cy="150" r="20" fill="white" stroke="#2600FF" strokeWidth="1.5" />
          {/* Document icon */}
          <path
            d="M52 142 L52 158 L68 158 L68 146 L64 142 L52 142 Z"
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
          />
          <path d="M64 142 L64 146 L68 146" fill="none" stroke="#2600FF" strokeWidth="1.5" />
          <line x1="55" y1="149" x2="65" y2="149" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
          <line x1="55" y1="153" x2="62" y2="153" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
        </g>

        {/* Node 2: AI Processing (dual nodes converging) */}
        <g
          className={`node-ai-upper transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '0.8s' }}
        >
          <circle cx="210" cy="100" r="22" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.3" />
          <circle cx="210" cy="100" r="15" fill="white" stroke="#2600FF" strokeWidth="1.5" />
          {/* AI brain pattern */}
          <circle cx="210" cy="100" r="6" fill="none" stroke="#2600FF" strokeWidth="1" />
          <circle cx="210" cy="100" r="3" fill="#2600FF" fillOpacity="0.3" />
          <path d="M204 100 L202 100 M216 100 L218 100 M210 94 L210 92 M210 106 L210 108" stroke="#2600FF" strokeWidth="1" />
        </g>
        <g
          className={`node-ai-lower transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '1s' }}
        >
          <circle cx="210" cy="200" r="22" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.3" />
          <circle cx="210" cy="200" r="15" fill="white" stroke="#2600FF" strokeWidth="1.5" />
          {/* AI brain pattern */}
          <circle cx="210" cy="200" r="6" fill="none" stroke="#2600FF" strokeWidth="1" />
          <circle cx="210" cy="200" r="3" fill="#2600FF" fillOpacity="0.3" />
          <path d="M204 200 L202 200 M216 200 L218 200 M210 194 L210 192 M210 206 L210 208" stroke="#2600FF" strokeWidth="1" />
        </g>

        {/* Node 3: Central ERP - Main hub */}
        <g
          className={`node-erp transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '1.8s' }}
        >
          <circle cx="310" cy="150" r="35" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.2" filter="url(#nodeGlow)" />
          <circle cx="310" cy="150" r="28" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.4" />
          <circle cx="310" cy="150" r="20" fill="white" stroke="#2600FF" strokeWidth="2" />
          {/* ERP/Database icon */}
          <ellipse cx="310" cy="143" rx="10" ry="4" fill="none" stroke="#2600FF" strokeWidth="1.5" />
          <path d="M300 143 L300 157 C300 159.5 304.5 162 310 162 C315.5 162 320 159.5 320 157 L320 143" fill="none" stroke="#2600FF" strokeWidth="1.5" />
          <path d="M300 150 C300 152.5 304.5 155 310 155 C315.5 155 320 152.5 320 150" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />

          {/* Pulsing ring */}
          {isVisible && (
            <circle cx="310" cy="150" r="35" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.3">
              <animate attributeName="r" values="35;45;35" dur="2s" repeatCount="indefinite" />
              <animate attributeName="stroke-opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite" />
            </circle>
          )}
        </g>

        {/* Node 4: Output nodes */}
        <g
          className={`node-output-upper transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '2.8s' }}
        >
          <circle cx="420" cy="100" r="22" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.3" />
          <circle cx="420" cy="100" r="15" fill="white" stroke="#2600FF" strokeWidth="1.5" />
          {/* Quote/Output icon */}
          <rect x="412" y="93" width="16" height="14" rx="2" fill="none" stroke="#2600FF" strokeWidth="1.5" />
          <line x1="415" y1="97" x2="425" y2="97" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
          <line x1="415" y1="100" x2="423" y2="100" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
          <line x1="415" y1="103" x2="420" y2="103" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.5" />
        </g>
        <g
          className={`node-output-lower transition-all duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`}
          style={{ transitionDelay: '3s' }}
        >
          <circle cx="420" cy="200" r="22" fill="white" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.3" />
          <circle cx="420" cy="200" r="15" fill="white" stroke="#2600FF" strokeWidth="1.5" />
          {/* Checkmark/Complete icon */}
          <circle cx="420" cy="200" r="8" fill="none" stroke="#2600FF" strokeWidth="1.5" />
          <path d="M415 200 L418 203 L425 196" fill="none" stroke="#2600FF" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </g>

        {/* Labels */}
        <g className={`labels transition-opacity duration-700 ${isVisible ? 'opacity-100' : 'opacity-0'}`} style={{ transitionDelay: '3.5s' }}>
          <text x="60" y="195" textAnchor="middle" className="fill-black text-[10px] font-medium opacity-40">RFQ Input</text>
          <text x="210" y="245" textAnchor="middle" className="fill-black text-[10px] font-medium opacity-40">AI Processing</text>
          <text x="310" y="205" textAnchor="middle" className="fill-black text-[10px] font-medium opacity-40">ERP System</text>
          <text x="420" y="245" textAnchor="middle" className="fill-black text-[10px] font-medium opacity-40">Quotes</text>
        </g>
      </svg>
    </div>
  );
}
