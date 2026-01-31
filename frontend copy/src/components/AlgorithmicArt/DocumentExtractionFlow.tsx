import { useEffect, useRef, useState } from 'react';

interface DocumentExtractionFlowProps {
  className?: string;
}

export default function DocumentExtractionFlow({ className = '' }: DocumentExtractionFlowProps) {
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

  // Email with attachments on the left
  const EmailWithAttachments = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0s' }}
    >
      {/* Email envelope */}
      <rect x="15" y="80" width="70" height="50" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="3" />
      {/* Envelope flap (open) */}
      <path d="M15 80 L50 105 L85 80" fill="white" stroke="#2600FF" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M15 80 L50 60 L85 80" fill="white" stroke="#2600FF" strokeWidth="1.5" strokeLinejoin="round" />

      {/* Attachments stacked */}
      {/* PDF */}
      <g
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.3s' }}
      >
        <rect x="25" y="35" width="22" height="28" fill="white" stroke="#2600FF" strokeWidth="1" rx="2" />
        <rect x="28" y="38" width="16" height="4" fill="#2600FF" fillOpacity="0.2" rx="1" />
        <line x1="28" y1="46" x2="44" y2="46" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.2" />
        <line x1="28" y1="50" x2="42" y2="50" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.2" />
        <line x1="28" y1="54" x2="40" y2="54" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.2" />
        <text x="36" y="60" textAnchor="middle" className="fill-[#2600FF] text-[5px] font-bold opacity-50" style={{ fontFamily: 'Inter, sans-serif' }}>PDF</text>
      </g>

      {/* Excel */}
      <g
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.5s' }}
      >
        <rect x="52" y="30" width="22" height="28" fill="white" stroke="#2600FF" strokeWidth="1" rx="2" />
        {/* Grid pattern */}
        <line x1="55" y1="38" x2="71" y2="38" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="55" y1="44" x2="71" y2="44" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="55" y1="50" x2="71" y2="50" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="60" y1="33" x2="60" y2="55" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="66" y1="33" x2="66" y2="55" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <text x="63" y="60" textAnchor="middle" className="fill-[#2600FF] text-[5px] font-bold opacity-50" style={{ fontFamily: 'Inter, sans-serif' }}>XLS</text>
      </g>

      {/* Messy lines coming out of documents */}
      {isVisible && (
        <g className="messy-lines">
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <line
              key={`mess-${i}`}
              x1={30 + (i % 3) * 15}
              y1={70 - i * 2}
              x2={45 + (i % 4) * 10}
              y2={68 - i * 2}
              stroke="#2600FF"
              strokeWidth="1"
              strokeOpacity="0.2"
              strokeLinecap="round"
            >
              <animate
                attributeName="x2"
                values={`${45 + (i % 4) * 10};${50 + (i % 4) * 10};${45 + (i % 4) * 10}`}
                dur="2s"
                repeatCount="indefinite"
                begin={`${i * 0.1}s`}
              />
            </line>
          ))}
        </g>
      )}

      <text x="50" y="145" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        RFQ Email
      </text>
    </g>
  );

  // Processing funnel in the middle
  const ProcessingFunnel = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.8s' }}
    >
      {/* Funnel shape */}
      <path
        d="M115 50 L155 50 L145 90 L145 120 L125 120 L125 90 Z"
        fill="white"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />

      {/* AI processing indicator inside */}
      <circle cx="135" cy="70" r="12" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.3" />
      <circle cx="135" cy="70" r="6" fill="#2600FF" fillOpacity="0.2">
        {isVisible && (
          <animate attributeName="fill-opacity" values="0.2;0.5;0.2" dur="1s" repeatCount="indefinite" />
        )}
      </circle>

      {/* Swirl lines inside funnel */}
      {isVisible && (
        <g>
          <path d="M125 55 Q135 65 125 75" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3">
            <animateTransform attributeName="transform" type="rotate" from="0 135 70" to="360 135 70" dur="3s" repeatCount="indefinite" />
          </path>
          <path d="M145 55 Q135 65 145 75" fill="none" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3">
            <animateTransform attributeName="transform" type="rotate" from="0 135 70" to="-360 135 70" dur="3s" repeatCount="indefinite" />
          </path>
        </g>
      )}

      <text x="135" y="140" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        AI Parser
      </text>
    </g>
  );

  // Organized quote output on the right
  const OrganizedOutput = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1.5s' }}
    >
      {/* Quote document */}
      <rect x="175" y="40" width="80" height="100" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

      {/* Header */}
      <rect x="183" y="48" width="45" height="8" fill="#2600FF" fillOpacity="0.15" rx="2" />

      {/* Table header */}
      <g className="transition-all duration-500" style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1.8s' }}>
        <rect x="183" y="62" width="64" height="8" fill="#2600FF" fillOpacity="0.1" />
        <line x1="200" y1="62" x2="200" y2="70" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="220" y1="62" x2="220" y2="70" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
        <line x1="237" y1="62" x2="237" y2="70" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.3" />
      </g>

      {/* Product rows */}
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <g
          key={`row-${i}`}
          className="transition-all duration-300"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: `${2 + i * 0.15}s`
          }}
        >
          <line x1="183" y1={74 + i * 9} x2="247" y2={74 + i * 9} stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.1" />
          <rect x="184" y={75 + i * 9} width="14" height="5" fill="#2600FF" fillOpacity="0.08" rx="1" />
          <rect x="201" y={75 + i * 9} width="17" height="5" fill="#2600FF" fillOpacity="0.08" rx="1" />
          <rect x="221" y={75 + i * 9} width="14" height="5" fill="#2600FF" fillOpacity="0.08" rx="1" />
          <rect x="238" y={75 + i * 9} width="8" height="5" fill="#2600FF" fillOpacity="0.08" rx="1" />
        </g>
      ))}

      {/* Row counter badge */}
      <g
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '3s' }}
      >
        <rect x="232" y="42" width="22" height="12" fill="#2600FF" fillOpacity="0.1" stroke="#2600FF" strokeWidth="0.75" rx="6" />
        <text x="243" y="51" textAnchor="middle" className="fill-[#2600FF] text-[7px] font-medium" style={{ fontFamily: 'Inter, sans-serif' }}>
          127
        </text>
      </g>

      <text x="215" y="155" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Structured Quote
      </text>
    </g>
  );

  // Data flow animation (chaotic lines becoming organized)
  const DataFlow = () => {
    if (!isVisible) return null;

    return (
      <g className="data-flow">
        {/* Chaotic particles flowing from docs to funnel */}
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={`chaos-${i}`}>
            <rect x="-3" y="-2" width="6" height="4" fill="#2600FF" fillOpacity="0.5" rx="1">
              <animateMotion
                dur={`${1.5 + i * 0.2}s`}
                repeatCount="indefinite"
                begin={`${i * 0.4}s`}
                path={`M85 ${60 + i * 8} Q100 ${55 + i * 5} 115 ${55 + i * 3}`}
              />
              <animate
                attributeName="fill-opacity"
                values="0.5;0.8;0.5"
                dur={`${1.5 + i * 0.2}s`}
                repeatCount="indefinite"
                begin={`${i * 0.4}s`}
              />
            </rect>
          </g>
        ))}

        {/* Organized rows flowing from funnel to output */}
        {[0, 1, 2].map((i) => (
          <g key={`order-${i}`}>
            <rect x="-8" y="-2" width="16" height="4" fill="#2600FF" fillOpacity="0.4" rx="1">
              <animateMotion
                dur="2s"
                repeatCount="indefinite"
                begin={`${1.5 + i * 0.5}s`}
                path="M145 115 Q160 100 175 85"
              />
            </rect>
          </g>
        ))}

        {/* Connection paths */}
        <path
          d="M85 70 Q100 65 115 60"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.15"
          strokeDasharray="4 4"
        />
        <path
          d="M145 115 Q160 100 175 85"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1.5"
          strokeOpacity="0.2"
        />
      </g>
    );
  };

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 270 165"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <DataFlow />
        <EmailWithAttachments />
        <ProcessingFunnel />
        <OrganizedOutput />
      </svg>
    </div>
  );
}
