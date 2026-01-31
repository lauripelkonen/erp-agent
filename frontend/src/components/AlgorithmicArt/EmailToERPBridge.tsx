import { useEffect, useRef, useState } from 'react';

interface EmailToERPBridgeProps {
  className?: string;
}

export default function EmailToERPBridge({ className = '' }: EmailToERPBridgeProps) {
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

  // Email inbox on the left
  const EmailInbox = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0s' }}
    >
      {/* Inbox container */}
      <rect x="15" y="60" width="60" height="80" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

      {/* Inbox header */}
      <rect x="15" y="60" width="60" height="16" fill="#2600FF" fillOpacity="0.1" rx="4" />
      <text x="45" y="72" textAnchor="middle" className="fill-[#2600FF] text-[7px] font-medium opacity-60" style={{ fontFamily: 'Inter, sans-serif' }}>
        Inbox
      </text>

      {/* Email items */}
      {[0, 1, 2].map((i) => (
        <g
          key={`email-${i}`}
          className="transition-all duration-500"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${0.2 + i * 0.2}s` }}
        >
          <rect x="20" y={82 + i * 18} width="50" height="14" fill="white" stroke="#2600FF" strokeWidth="0.75" strokeOpacity="0.3" rx="2" />
          {/* Email icon */}
          <rect x="23" y={85 + i * 18} width="8" height="6" fill="none" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.5" />
          <path d={`M23 ${85 + i * 18} L27 ${88 + i * 18} L31 ${85 + i * 18}`} fill="none" stroke="#2600FF" strokeWidth="0.5" strokeOpacity="0.5" />
          {/* Subject line */}
          <line x1="34" y1={88 + i * 18} x2="65" y2={88 + i * 18} stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.15" strokeLinecap="round" />
          <line x1="34" y1={92 + i * 18} x2="55" y2={92 + i * 18} stroke="#2600FF" strokeWidth="1" strokeOpacity="0.1" strokeLinecap="round" />
          {/* Attachment indicator */}
          <circle cx="67" cy={89 + i * 18} r="2" fill="#2600FF" fillOpacity="0.3" />
        </g>
      ))}

      {/* Unread badge */}
      <g
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.8s' }}
      >
        <circle cx="70" cy="62" r="8" fill="#2600FF" />
        <text x="70" y="65" textAnchor="middle" className="fill-white text-[7px] font-bold" style={{ fontFamily: 'Inter, sans-serif' }}>
          7
        </text>
        {isVisible && (
          <circle cx="70" cy="62" r="8" fill="none" stroke="#2600FF" strokeWidth="1">
            <animate attributeName="r" values="8;14;8" dur="2s" repeatCount="indefinite" />
            <animate attributeName="stroke-opacity" values="0.5;0;0.5" dur="2s" repeatCount="indefinite" />
          </circle>
        )}
      </g>

      <text x="45" y="155" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        RFQ Emails
      </text>
    </g>
  );

  // Bridge/tunnel in the middle
  const Bridge = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.5s' }}
    >
      {/* Bridge structure */}
      <path
        d="M90 75 L110 65 L190 65 L210 75 L210 125 L190 135 L110 135 L90 125 Z"
        fill="white"
        stroke="#2600FF"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />

      {/* Inner tunnel */}
      <path
        d="M100 80 L115 72 L185 72 L200 80 L200 120 L185 128 L115 128 L100 120 Z"
        fill="none"
        stroke="#2600FF"
        strokeWidth="1"
        strokeOpacity="0.2"
        strokeDasharray="4 4"
      />

      {/* Processing nodes inside bridge */}
      {['Parse', 'Match', 'Price'].map((label, i) => (
        <g
          key={label}
          className="transition-all duration-500"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${1 + i * 0.3}s` }}
        >
          <circle cx={120 + i * 30} cy="100" r="12" fill="white" stroke="#2600FF" strokeWidth="1" />
          <circle cx={120 + i * 30} cy="100" r="6" fill="#2600FF" fillOpacity="0.2">
            {isVisible && (
              <animate
                attributeName="fill-opacity"
                values="0.2;0.5;0.2"
                dur="1.5s"
                repeatCount="indefinite"
                begin={`${i * 0.3}s`}
              />
            )}
          </circle>
          <text
            x={120 + i * 30}
            y="118"
            textAnchor="middle"
            className="fill-[#2600FF] text-[6px] font-medium opacity-50"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {label}
          </text>
        </g>
      ))}

      {/* Connection lines between nodes */}
      <line x1="132" y1="100" x2="138" y2="100" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.3" />
      <line x1="162" y1="100" x2="168" y2="100" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.3" />

      <text x="150" y="150" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        AI Processing
      </text>
    </g>
  );

  // ERP system on the right
  const ERPSystem = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1s' }}
    >
      {/* Database cylinder */}
      <ellipse cx="255" cy="70" rx="25" ry="10" fill="white" stroke="#2600FF" strokeWidth="1.5" />
      <path
        d="M230 70 L230 130 C230 136 241 142 255 142 C269 142 280 136 280 130 L280 70"
        fill="white"
        stroke="#2600FF"
        strokeWidth="1.5"
      />
      <ellipse cx="255" cy="130" rx="25" ry="10" fill="none" stroke="#2600FF" strokeWidth="1.5" />

      {/* Data rows inside */}
      {[0, 1, 2].map((i) => (
        <ellipse
          key={`data-${i}`}
          cx="255"
          cy={85 + i * 15}
          rx="22"
          ry="5"
          fill="none"
          stroke="#2600FF"
          strokeWidth="0.75"
          strokeOpacity="0.2"
          className="transition-all duration-500"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${1.5 + i * 0.2}s` }}
        />
      ))}

      {/* Quote documents filing into database */}
      {isVisible && (
        <g className="filing-docs">
          {[0, 1, 2].map((i) => (
            <g key={`doc-${i}`}>
              <rect x="-6" y="-8" width="12" height="16" fill="white" stroke="#2600FF" strokeWidth="1" rx="1" opacity="0">
                <animateMotion
                  dur="2s"
                  repeatCount="indefinite"
                  begin={`${2 + i * 0.8}s`}
                  path="M220 100 Q240 90 255 75"
                />
                <animate
                  attributeName="opacity"
                  values="0;1;1;0"
                  dur="2s"
                  repeatCount="indefinite"
                  begin={`${2 + i * 0.8}s`}
                />
              </rect>
            </g>
          ))}
        </g>
      )}

      {/* ERP label */}
      <rect
        x="240"
        y="95"
        width="30"
        height="14"
        fill="#2600FF"
        fillOpacity="0.1"
        stroke="#2600FF"
        strokeWidth="0.75"
        rx="3"
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1.8s' }}
      />
      <text
        x="255"
        y="105"
        textAnchor="middle"
        className="fill-[#2600FF] text-[7px] font-bold opacity-70"
        style={{ fontFamily: 'Inter, sans-serif', opacity: isVisible ? 1 : 0, transitionDelay: '1.8s' }}
      >
        ERP
      </text>

      <text x="255" y="158" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
        Quote Database
      </text>
    </g>
  );

  // Animated data flow
  const DataFlow = () => {
    if (!isVisible) return null;

    return (
      <g className="data-flow">
        {/* Email to bridge flow */}
        <path
          d="M75 100 L90 100"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1.5"
          strokeOpacity="0.2"
        />

        {/* Emails transforming to docs */}
        {[0, 1, 2].map((i) => (
          <g key={`flow-${i}`}>
            {/* Start as envelope */}
            <g>
              <rect x="-5" y="-4" width="10" height="8" fill="#2600FF" rx="1" opacity="0">
                <animateMotion
                  dur="3s"
                  repeatCount="indefinite"
                  begin={`${i * 1}s`}
                  path="M75 100 Q150 100 210 100"
                />
                <animate
                  attributeName="opacity"
                  values="0;0.6;0.6;0.6"
                  dur="3s"
                  repeatCount="indefinite"
                  begin={`${i * 1}s`}
                />
                <animate
                  attributeName="width"
                  values="10;8;12"
                  dur="3s"
                  repeatCount="indefinite"
                  begin={`${i * 1}s`}
                />
                <animate
                  attributeName="height"
                  values="8;10;15"
                  dur="3s"
                  repeatCount="indefinite"
                  begin={`${i * 1}s`}
                />
              </rect>
            </g>
          </g>
        ))}

        {/* Bridge to ERP flow */}
        <path
          d="M210 100 L230 100"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1.5"
          strokeOpacity="0.2"
        />
      </g>
    );
  };

  // Arrows
  const Arrows = () => (
    <g
      className="transition-all duration-700"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.6s' }}
    >
      {/* Left arrow */}
      <path d="M78 97 L85 100 L78 103" fill="none" stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.3" strokeLinecap="round" strokeLinejoin="round" />
      {/* Right arrow */}
      <path d="M215 97 L222 100 L215 103" fill="none" stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.3" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  );

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 170"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        <DataFlow />
        <Arrows />
        <EmailInbox />
        <Bridge />
        <ERPSystem />
      </svg>
    </div>
  );
}
