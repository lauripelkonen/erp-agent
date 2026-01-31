'use client';

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
      className="transition-all duration-1000 ease-out"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateX(0)' : 'translateX(-10px)',
        transitionDelay: '0s'
      }}
    >
      {/* Soft glow behind */}
      <ellipse cx="65" cy="105" rx="50" ry="40" fill="url(#inboxGlow)" />

      {/* Inbox container - smooth rounded card */}
      <rect
        x="20"
        y="55"
        width="90"
        height="100"
        fill="white"
        stroke="url(#borderGradient)"
        strokeWidth="1.5"
        rx="16"
        ry="16"
        filter="url(#softShadow)"
      />

      {/* Inbox header pill */}
      <rect
        x="32"
        y="65"
        width="66"
        height="22"
        fill="#2600FF"
        fillOpacity="0.06"
        rx="11"
        ry="11"
      />
      <text
        x="65"
        y="80"
        textAnchor="middle"
        className="fill-[#2600FF] text-[9px] font-semibold"
        style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '0.02em' }}
      >
        Inbox
      </text>

      {/* Email items - smooth cards */}
      {[0, 1, 2].map((i) => (
        <g
          key={`email-${i}`}
          className="transition-all duration-700 ease-out"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${0.3 + i * 0.15}s` }}
        >
          <rect
            x="28"
            y={95 + i * 18}
            width="74"
            height="14"
            fill="white"
            stroke="#2600FF"
            strokeWidth="0.75"
            strokeOpacity={0.15 + i * 0.05}
            rx="7"
            ry="7"
          />
          {/* Email envelope icon */}
          <rect
            x="33"
            y={98 + i * 18}
            width="10"
            height="7"
            fill="none"
            stroke="#2600FF"
            strokeWidth="0.6"
            strokeOpacity="0.4"
            rx="1.5"
          />
          <path
            d={`M33 ${98 + i * 18} L38 ${101.5 + i * 18} L43 ${98 + i * 18}`}
            fill="none"
            stroke="#2600FF"
            strokeWidth="0.6"
            strokeOpacity="0.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Subject lines */}
          <rect
            x="47"
            y={99.5 + i * 18}
            width="28"
            height="2"
            fill="#2600FF"
            fillOpacity="0.12"
            rx="1"
          />
          <rect
            x="47"
            y={103.5 + i * 18}
            width="18"
            height="1.5"
            fill="#2600FF"
            fillOpacity="0.06"
            rx="0.75"
          />
          {/* Attachment dot */}
          <circle
            cx="95"
            cy={102 + i * 18}
            r="2.5"
            fill="#2600FF"
            fillOpacity={0.2 - i * 0.04}
          />
        </g>
      ))}

      {/* Unread badge - pulsing */}
      <g
        className="transition-all duration-700 ease-out"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.6s' }}
      >
        <circle cx="102" cy="62" r="11" fill="#2600FF" filter="url(#badgeGlow)" />
        <text
          x="102"
          y="66"
          textAnchor="middle"
          className="fill-white text-[9px] font-bold"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          7
        </text>
        {isVisible && (
          <circle cx="102" cy="62" r="11" fill="none" stroke="#2600FF" strokeWidth="2">
            <animate attributeName="r" values="11;18;11" dur="2.5s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1" />
            <animate attributeName="stroke-opacity" values="0.4;0;0.4" dur="2.5s" repeatCount="indefinite" calcMode="spline" keySplines="0.4 0 0.2 1; 0.4 0 0.2 1" />
          </circle>
        )}
      </g>

      {/* Label */}
      <text
        x="65"
        y="172"
        textAnchor="middle"
        className="fill-black text-[10px] font-medium opacity-35"
        style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '-0.01em' }}
      >
        RFQ Emails
      </text>
    </g>
  );

  // Bridge/tunnel in the middle - refined processing pipeline
  const Bridge = () => (
    <g
      className="transition-all duration-1000 ease-out"
      style={{
        opacity: isVisible ? 1 : 0,
        transitionDelay: '0.4s'
      }}
    >
      {/* Soft glow */}
      <ellipse cx="250" cy="105" rx="90" ry="50" fill="url(#bridgeGlow)" />

      {/* Bridge structure - sleek rounded container */}
      <rect
        x="135"
        y="55"
        width="230"
        height="100"
        fill="white"
        stroke="url(#borderGradient)"
        strokeWidth="1.5"
        rx="20"
        ry="20"
        filter="url(#softShadow)"
      />

      {/* Inner processing track */}
      <rect
        x="150"
        y="70"
        width="200"
        height="70"
        fill="#2600FF"
        fillOpacity="0.02"
        rx="14"
        ry="14"
      />

      {/* Dashed inner border */}
      <rect
        x="150"
        y="70"
        width="200"
        height="70"
        fill="none"
        stroke="#2600FF"
        strokeWidth="1"
        strokeOpacity="0.1"
        strokeDasharray="6 4"
        rx="14"
        ry="14"
      />

      {/* Processing nodes - elegant circles */}
      {['Parse', 'Match', 'Price'].map((label, i) => (
        <g
          key={label}
          className="transition-all duration-700 ease-out"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${0.8 + i * 0.2}s` }}
        >
          {/* Outer ring */}
          <circle
            cx={185 + i * 65}
            cy="105"
            r="22"
            fill="white"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeOpacity="0.2"
            filter="url(#nodeGlow)"
          />
          {/* Inner circle with pulse */}
          <circle
            cx={185 + i * 65}
            cy="105"
            r="14"
            fill="#2600FF"
            fillOpacity="0.08"
          >
            {isVisible && (
              <animate
                attributeName="fill-opacity"
                values="0.08;0.2;0.08"
                dur="2s"
                repeatCount="indefinite"
                begin={`${i * 0.4}s`}
                calcMode="spline"
                keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
              />
            )}
          </circle>
          {/* Center dot */}
          <circle
            cx={185 + i * 65}
            cy="105"
            r="5"
            fill="#2600FF"
            fillOpacity="0.5"
          >
            {isVisible && (
              <animate
                attributeName="fill-opacity"
                values="0.5;0.8;0.5"
                dur="2s"
                repeatCount="indefinite"
                begin={`${i * 0.4}s`}
                calcMode="spline"
                keySplines="0.4 0 0.2 1; 0.4 0 0.2 1"
              />
            )}
          </circle>
          {/* Label */}
          <text
            x={185 + i * 65}
            y="138"
            textAnchor="middle"
            className="fill-[#2600FF] text-[8px] font-semibold"
            style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '0.03em', opacity: 0.6 }}
          >
            {label}
          </text>
        </g>
      ))}

      {/* Connection lines between nodes - smooth curves */}
      <g className="transition-all duration-700" style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1.2s' }}>
        <line x1="207" y1="105" x2="228" y2="105" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.15" strokeLinecap="round" />
        <line x1="272" y1="105" x2="293" y2="105" stroke="#2600FF" strokeWidth="2" strokeOpacity="0.15" strokeLinecap="round" />

        {/* Animated dots on connection lines */}
        {isVisible && (
          <>
            <circle cx="207" cy="105" r="3" fill="#2600FF" fillOpacity="0.5">
              <animateMotion dur="1.5s" repeatCount="indefinite" path="M0 0 L21 0" />
            </circle>
            <circle cx="272" cy="105" r="3" fill="#2600FF" fillOpacity="0.5">
              <animateMotion dur="1.5s" repeatCount="indefinite" path="M0 0 L21 0" begin="0.3s" />
            </circle>
          </>
        )}
      </g>

      {/* Label */}
      <text
        x="250"
        y="172"
        textAnchor="middle"
        className="fill-black text-[10px] font-medium opacity-35"
        style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '-0.01em' }}
      >
        AI Processing
      </text>
    </g>
  );

  // ERP system on the right - modern database visual
  const ERPSystem = () => (
    <g
      className="transition-all duration-1000 ease-out"
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateX(0)' : 'translateX(10px)',
        transitionDelay: '0.8s'
      }}
    >
      {/* Soft glow */}
      <ellipse cx="435" cy="105" rx="50" ry="40" fill="url(#erpGlow)" />

      {/* Database container - smooth rounded */}
      <rect
        x="390"
        y="55"
        width="90"
        height="100"
        fill="white"
        stroke="url(#borderGradient)"
        strokeWidth="1.5"
        rx="16"
        ry="16"
        filter="url(#softShadow)"
      />

      {/* Database cylinder visual */}
      <g className="transition-all duration-700" style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1s' }}>
        {/* Top ellipse */}
        <ellipse
          cx="435"
          cy="75"
          rx="30"
          ry="8"
          fill="#2600FF"
          fillOpacity="0.06"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.2"
        />

        {/* Cylinder body */}
        <path
          d="M405 75 L405 125 C405 130 418 135 435 135 C452 135 465 130 465 125 L465 75"
          fill="#2600FF"
          fillOpacity="0.03"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.2"
        />

        {/* Bottom ellipse */}
        <ellipse
          cx="435"
          cy="125"
          rx="30"
          ry="8"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.2"
        />

        {/* Data rows */}
        {[0, 1, 2].map((i) => (
          <ellipse
            key={`data-${i}`}
            cx="435"
            cy={88 + i * 14}
            rx="25"
            ry="5"
            fill="none"
            stroke="#2600FF"
            strokeWidth="0.75"
            strokeOpacity={0.15 - i * 0.03}
            className="transition-all duration-500"
            style={{ opacity: isVisible ? 1 : 0, transitionDelay: `${1.2 + i * 0.15}s` }}
          />
        ))}
      </g>

      {/* ERP badge */}
      <g
        className="transition-all duration-500"
        style={{ opacity: isVisible ? 1 : 0, transitionDelay: '1.4s' }}
      >
        <rect
          x="417"
          y="95"
          width="36"
          height="20"
          fill="#2600FF"
          fillOpacity="0.08"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.2"
          rx="10"
          ry="10"
        />
        <text
          x="435"
          y="109"
          textAnchor="middle"
          className="fill-[#2600FF] text-[9px] font-bold"
          style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '0.05em', opacity: 0.7 }}
        >
          ERP
        </text>
      </g>

      {/* Filing documents animation */}
      {isVisible && (
        <g>
          {[0, 1, 2].map((i) => (
            <g key={`doc-${i}`} transform="translate(365, 105)">
              <rect
                x="-7"
                y="-9"
                width="14"
                height="18"
                fill="white"
                stroke="#2600FF"
                strokeWidth="1"
                strokeOpacity="0.6"
                rx="3"
                ry="3"
                opacity="0"
              >
                <animateMotion
                  dur="2.5s"
                  repeatCount="indefinite"
                  begin={`${1.6 + i * 0.6}s`}
                  path="M0 0 Q35 -20 63 -35"
                  rotate="auto"
                />
                <animate
                  attributeName="opacity"
                  values="0;0.8;0.8;0"
                  keyTimes="0;0.1;0.8;1"
                  dur="2.5s"
                  repeatCount="indefinite"
                  begin={`${1.6 + i * 0.6}s`}
                />
              </rect>
            </g>
          ))}
        </g>
      )}

      {/* Label */}
      <text
        x="435"
        y="172"
        textAnchor="middle"
        className="fill-black text-[10px] font-medium opacity-35"
        style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '-0.01em' }}
      >
        Quote Database
      </text>
    </g>
  );

  // Animated data flow particles
  const DataFlow = () => {
    if (!isVisible) return null;

    return (
      <g className="data-flow">
        {/* Left connector line */}
        <path
          d="M110 105 L135 105"
          fill="none"
          stroke="#2600FF"
          strokeWidth="2"
          strokeOpacity="0.1"
          strokeLinecap="round"
        />

        {/* Right connector line */}
        <path
          d="M365 105 L390 105"
          fill="none"
          stroke="#2600FF"
          strokeWidth="2"
          strokeOpacity="0.1"
          strokeLinecap="round"
        />

        {/* Flowing particles - left side */}
        {[0, 1, 2].map((i) => (
          <g key={`flow-left-${i}`}>
            <circle cx="110" cy="105" r="4" fill="#2600FF" fillOpacity="0">
              <animateMotion
                dur="3.5s"
                repeatCount="indefinite"
                begin={`${i * 0.8}s`}
                path="M0 0 L25 0"
                calcMode="spline"
                keySplines="0.4 0 0.2 1"
              />
              <animate
                attributeName="fill-opacity"
                values="0;0.6;0.6;0"
                keyTimes="0;0.1;0.9;1"
                dur="3.5s"
                repeatCount="indefinite"
                begin={`${i * 0.8}s`}
              />
            </circle>
          </g>
        ))}

        {/* Flowing particles - right side */}
        {[0, 1, 2].map((i) => (
          <g key={`flow-right-${i}`}>
            <circle cx="365" cy="105" r="4" fill="#2600FF" fillOpacity="0">
              <animateMotion
                dur="3.5s"
                repeatCount="indefinite"
                begin={`${1.2 + i * 0.8}s`}
                path="M0 0 L25 0"
                calcMode="spline"
                keySplines="0.4 0 0.2 1"
              />
              <animate
                attributeName="fill-opacity"
                values="0;0.6;0.6;0"
                keyTimes="0;0.1;0.9;1"
                dur="3.5s"
                repeatCount="indefinite"
                begin={`${1.2 + i * 0.8}s`}
              />
            </circle>
          </g>
        ))}
      </g>
    );
  };

  // Smooth arrow indicators
  const Arrows = () => (
    <g
      className="transition-all duration-1000 ease-out"
      style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.5s' }}
    >
      {/* Left arrow */}
      <path
        d="M118 100 L128 105 L118 110"
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity="0.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Right arrow */}
      <path
        d="M373 100 L383 105 L373 110"
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        strokeOpacity="0.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </g>
  );

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 500 185"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
        style={{ overflow: 'visible' }}
      >
        {/* Definitions for gradients and filters */}
        <defs>
          {/* Border gradient */}
          <linearGradient id="borderGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0.08" />
          </linearGradient>

          {/* Soft shadow filter */}
          <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="8" floodColor="#2600FF" floodOpacity="0.06" />
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#000000" floodOpacity="0.04" />
          </filter>

          {/* Node glow */}
          <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#2600FF" floodOpacity="0.1" />
          </filter>

          {/* Badge glow */}
          <filter id="badgeGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#2600FF" floodOpacity="0.3" />
          </filter>

          {/* Glow gradients */}
          <radialGradient id="inboxGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0" />
          </radialGradient>

          <radialGradient id="bridgeGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.03" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0" />
          </radialGradient>

          <radialGradient id="erpGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#2600FF" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#2600FF" stopOpacity="0" />
          </radialGradient>
        </defs>

        <DataFlow />
        <Arrows />
        <EmailInbox />
        <Bridge />
        <ERPSystem />
      </svg>
    </div>
  );
}
