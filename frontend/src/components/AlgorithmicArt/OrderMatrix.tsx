import { useEffect, useRef, useState } from 'react';

interface OrderMatrixProps {
  className?: string;
}

export default function OrderMatrix({ className = '' }: OrderMatrixProps) {
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

  // Generate concentric rectangles with slight rotation
  const generateRectangles = () => {
    const rects = [];
    const center = 150;
    const baseSize = 20;
    const increment = 12;
    const count = 12;

    for (let i = 0; i < count; i++) {
      const size = baseSize + (i * increment);
      const rotation = i * 1.5; // Slight rotation per layer
      const opacity = 0.15 + (i * 0.05);
      const delay = i * 0.1;

      rects.push(
        <rect
          key={`rect-${i}`}
          x={center - size / 2}
          y={center - size / 2}
          width={size}
          height={size}
          fill="none"
          stroke="#2600FF"
          strokeWidth="1.5"
          strokeOpacity={opacity}
          transform={`rotate(${rotation} ${center} ${center})`}
          className={`matrix-rect transition-all duration-1000`}
          style={{
            strokeDasharray: size * 4,
            strokeDashoffset: isVisible ? 0 : size * 4,
            transitionDelay: `${delay}s`,
            opacity: isVisible ? 1 : 0
          }}
        />
      );
    }
    return rects;
  };

  // Generate inner geometric pattern
  const generateInnerPattern = () => {
    const center = 150;
    const elements = [];

    // Central diamond
    elements.push(
      <path
        key="diamond"
        d={`M${center} ${center - 15} L${center + 15} ${center} L${center} ${center + 15} L${center - 15} ${center} Z`}
        fill="none"
        stroke="#2600FF"
        strokeWidth="1.5"
        className="transition-all duration-700"
        style={{
          strokeDasharray: 85,
          strokeDashoffset: isVisible ? 0 : 85,
          transitionDelay: '1.5s'
        }}
      />
    );

    // Inner square
    elements.push(
      <rect
        key="inner-square"
        x={center - 8}
        y={center - 8}
        width={16}
        height={16}
        fill="none"
        stroke="#2600FF"
        strokeWidth="1"
        transform={`rotate(45 ${center} ${center})`}
        className="transition-all duration-700"
        style={{
          strokeDasharray: 64,
          strokeDashoffset: isVisible ? 0 : 64,
          transitionDelay: '1.7s'
        }}
      />
    );

    // Center dot
    elements.push(
      <circle
        key="center-dot"
        cx={center}
        cy={center}
        r={3}
        fill="#2600FF"
        className="transition-all duration-500"
        style={{
          opacity: isVisible ? 1 : 0,
          transitionDelay: '1.9s'
        }}
      />
    );

    return elements;
  };

  // Corner accent elements
  const generateCornerAccents = () => {
    const positions = [
      { x: 30, y: 30, rotate: 0 },
      { x: 270, y: 30, rotate: 90 },
      { x: 270, y: 270, rotate: 180 },
      { x: 30, y: 270, rotate: 270 }
    ];

    return positions.map((pos, i) => (
      <g
        key={`corner-${i}`}
        transform={`translate(${pos.x}, ${pos.y}) rotate(${pos.rotate})`}
        className="transition-all duration-700"
        style={{
          opacity: isVisible ? 0.3 : 0,
          transitionDelay: `${2 + i * 0.1}s`
        }}
      >
        <path
          d="M0 0 L20 0 M0 0 L0 20"
          stroke="#2600FF"
          strokeWidth="1.5"
          fill="none"
        />
        <circle cx="0" cy="0" r="2" fill="#2600FF" />
      </g>
    ));
  };

  // Floating data particles
  const generateParticles = () => {
    if (!isVisible) return null;

    const particles = [];
    const center = 150;
    const particleCount = 8;

    for (let i = 0; i < particleCount; i++) {
      const angle = (i / particleCount) * Math.PI * 2;
      const radius = 80;
      const x = center + Math.cos(angle) * radius;
      const y = center + Math.sin(angle) * radius;
      const duration = 3 + (i % 3) * 0.5;
      const delay = i * 0.3;

      particles.push(
        <circle
          key={`particle-${i}`}
          r="2"
          fill="#2600FF"
          fillOpacity="0.6"
        >
          <animateMotion
            dur={`${duration}s`}
            repeatCount="indefinite"
            begin={`${delay}s`}
            path={`M${x} ${y} Q${center + 30} ${center} ${center} ${center} Q${center - 30} ${center} ${x} ${y}`}
          />
          <animate
            attributeName="fill-opacity"
            values="0.6;1;0.6"
            dur={`${duration}s`}
            repeatCount="indefinite"
            begin={`${delay}s`}
          />
        </circle>
      );
    }

    return <g className="particles">{particles}</g>;
  };

  // Orbiting ring
  const OrbitingRing = () => {
    if (!isVisible) return null;

    return (
      <g>
        <circle
          cx="150"
          cy="150"
          r="95"
          fill="none"
          stroke="#2600FF"
          strokeWidth="0.5"
          strokeOpacity="0.2"
          strokeDasharray="4 4"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 150 150"
            to="360 150 150"
            dur="30s"
            repeatCount="indefinite"
          />
        </circle>
        {/* Orbiting dot */}
        <circle r="4" fill="#2600FF" fillOpacity="0.8">
          <animateMotion
            dur="8s"
            repeatCount="indefinite"
            path="M150 55 A95 95 0 1 1 149.99 55"
          />
        </circle>
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
        {/* Subtle background pattern */}
        <defs>
          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="10" cy="10" r="0.5" fill="rgba(38,0,255,0.1)" />
          </pattern>
          <filter id="matrixGlow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background */}
        <rect width="300" height="300" fill="url(#grid)" className="transition-opacity duration-1000" style={{ opacity: isVisible ? 1 : 0 }} />

        {/* Outer glow circle */}
        <circle
          cx="150"
          cy="150"
          r="120"
          fill="none"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.05"
          className="transition-all duration-1000"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: '0.2s'
          }}
        />

        {/* Concentric rectangles */}
        <g filter="url(#matrixGlow)">
          {generateRectangles()}
        </g>

        {/* Inner geometric pattern */}
        {generateInnerPattern()}

        {/* Corner accents */}
        {generateCornerAccents()}

        {/* Orbiting elements */}
        <OrbitingRing />

        {/* Floating particles */}
        {generateParticles()}

        {/* Pulsing center glow */}
        {isVisible && (
          <circle cx="150" cy="150" r="25" fill="none" stroke="#2600FF" strokeWidth="1" strokeOpacity="0.15">
            <animate attributeName="r" values="25;40;25" dur="3s" repeatCount="indefinite" />
            <animate attributeName="stroke-opacity" values="0.15;0;0.15" dur="3s" repeatCount="indefinite" />
          </circle>
        )}
      </svg>
    </div>
  );
}
