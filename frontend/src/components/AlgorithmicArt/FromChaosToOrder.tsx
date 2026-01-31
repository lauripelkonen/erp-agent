import { useEffect, useRef, useState } from 'react';

interface FromChaosToOrderProps {
  className?: string;
}

interface Particle {
  id: number;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  size: number;
  shape: 'circle' | 'square' | 'triangle' | 'line';
  rotation: number;
  delay: number;
}

export default function FromChaosToOrder({ className = '' }: FromChaosToOrderProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [particles] = useState<Particle[]>(() => generateParticles());

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

  function generateParticles(): Particle[] {
    const particles: Particle[] = [];
    const gridSize = 5;
    const cellSize = 40;
    const startOffset = 60;
    const shapes: Particle['shape'][] = ['circle', 'square', 'triangle', 'line'];

    // Seeded random for consistent chaos positions
    const seededRandom = (seed: number) => {
      const x = Math.sin(seed * 9999) * 10000;
      return x - Math.floor(x);
    };

    let id = 0;
    for (let row = 0; row < gridSize; row++) {
      for (let col = 0; col < gridSize; col++) {
        const seed = row * gridSize + col;

        // Chaotic starting positions (scattered around the canvas)
        const chaosX = 50 + seededRandom(seed * 1.1) * 200;
        const chaosY = 50 + seededRandom(seed * 2.2) * 200;

        // Ordered ending positions (clean grid)
        const orderX = startOffset + col * cellSize;
        const orderY = startOffset + row * cellSize;

        particles.push({
          id: id++,
          startX: chaosX,
          startY: chaosY,
          endX: orderX,
          endY: orderY,
          size: 6 + seededRandom(seed * 3.3) * 6,
          shape: shapes[Math.floor(seededRandom(seed * 4.4) * shapes.length)],
          rotation: seededRandom(seed * 5.5) * 360,
          delay: seededRandom(seed * 6.6) * 0.8
        });
      }
    }
    return particles;
  }

  const renderShape = (particle: Particle, x: number, y: number, opacity: number) => {
    const { id, size, shape, rotation } = particle;
    const transform = `rotate(${isVisible ? 0 : rotation} ${x} ${y})`;

    switch (shape) {
      case 'circle':
        return (
          <circle
            key={id}
            cx={x}
            cy={y}
            r={size / 2}
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeOpacity={opacity}
            transform={transform}
            className="transition-all duration-[2000ms] ease-out"
            style={{ transitionDelay: `${particle.delay}s` }}
          />
        );
      case 'square':
        return (
          <rect
            key={id}
            x={x - size / 2}
            y={y - size / 2}
            width={size}
            height={size}
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeOpacity={opacity}
            transform={transform}
            className="transition-all duration-[2000ms] ease-out"
            style={{ transitionDelay: `${particle.delay}s` }}
          />
        );
      case 'triangle':
        const h = size * 0.866;
        return (
          <path
            key={id}
            d={`M${x} ${y - h/2} L${x + size/2} ${y + h/2} L${x - size/2} ${y + h/2} Z`}
            fill="none"
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeOpacity={opacity}
            transform={transform}
            className="transition-all duration-[2000ms] ease-out"
            style={{ transitionDelay: `${particle.delay}s` }}
          />
        );
      case 'line':
        return (
          <line
            key={id}
            x1={x - size / 2}
            y1={y}
            x2={x + size / 2}
            y2={y}
            stroke="#2600FF"
            strokeWidth="2"
            strokeOpacity={opacity}
            strokeLinecap="round"
            transform={transform}
            className="transition-all duration-[2000ms] ease-out"
            style={{ transitionDelay: `${particle.delay}s` }}
          />
        );
    }
  };

  // Grid lines that fade in when organized
  const renderGridLines = () => {
    const lines = [];
    const gridSize = 5;
    const cellSize = 40;
    const startOffset = 60;
    const endOffset = startOffset + (gridSize - 1) * cellSize;

    // Vertical lines
    for (let i = 0; i < gridSize; i++) {
      const x = startOffset + i * cellSize;
      lines.push(
        <line
          key={`v-${i}`}
          x1={x}
          y1={startOffset - 10}
          x2={x}
          y2={endOffset + 10}
          stroke="#2600FF"
          strokeWidth="0.5"
          strokeOpacity={isVisible ? 0.1 : 0}
          strokeDasharray="4 4"
          className="transition-all duration-1000"
          style={{ transitionDelay: '1.5s' }}
        />
      );
    }

    // Horizontal lines
    for (let i = 0; i < gridSize; i++) {
      const y = startOffset + i * cellSize;
      lines.push(
        <line
          key={`h-${i}`}
          x1={startOffset - 10}
          y1={y}
          x2={endOffset + 10}
          y2={y}
          stroke="#2600FF"
          strokeWidth="0.5"
          strokeOpacity={isVisible ? 0.1 : 0}
          strokeDasharray="4 4"
          className="transition-all duration-1000"
          style={{ transitionDelay: '1.5s' }}
        />
      );
    }

    return lines;
  };

  // Outer frame that appears when organized
  const renderFrame = () => {
    const padding = 25;
    const startOffset = 60 - padding;
    const size = 4 * 40 + 2 * padding;

    return (
      <rect
        x={startOffset}
        y={startOffset}
        width={size}
        height={size}
        fill="none"
        stroke="#2600FF"
        strokeWidth="2"
        rx="8"
        className="transition-all duration-1000"
        style={{
          strokeDasharray: size * 4,
          strokeDashoffset: isVisible ? 0 : size * 4,
          transitionDelay: '1.8s',
          opacity: isVisible ? 0.3 : 0
        }}
      />
    );
  };

  // Corner brackets
  const renderCornerBrackets = () => {
    const corners = [
      { x: 35, y: 35, rotate: 0 },
      { x: 265, y: 35, rotate: 90 },
      { x: 265, y: 265, rotate: 180 },
      { x: 35, y: 265, rotate: 270 }
    ];

    return corners.map((corner, i) => (
      <g
        key={`corner-${i}`}
        transform={`translate(${corner.x}, ${corner.y}) rotate(${corner.rotate})`}
        className="transition-all duration-700"
        style={{
          opacity: isVisible ? 0.4 : 0,
          transitionDelay: `${2.2 + i * 0.1}s`
        }}
      >
        <path
          d="M0 15 L0 0 L15 0"
          stroke="#2600FF"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
      </g>
    ));
  };

  // Scanning line effect
  const ScanLine = () => {
    if (!isVisible) return null;

    return (
      <g>
        <line
          x1="35"
          y1="150"
          x2="265"
          y2="150"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.3"
        >
          <animate
            attributeName="y1"
            values="35;265;35"
            dur="4s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="y2"
            values="35;265;35"
            dur="4s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="stroke-opacity"
            values="0.3;0.1;0.3"
            dur="4s"
            repeatCount="indefinite"
          />
        </line>
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
          <filter id="chaosGlow">
            <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Background subtle pattern */}
        <rect
          width="300"
          height="300"
          fill="none"
          className="transition-opacity duration-1000"
          style={{ opacity: isVisible ? 1 : 0 }}
        />

        {/* Grid lines (appear when organized) */}
        {renderGridLines()}

        {/* Outer frame */}
        {renderFrame()}

        {/* Corner brackets */}
        {renderCornerBrackets()}

        {/* Particles that transition from chaos to order */}
        <g filter="url(#chaosGlow)">
          {particles.map((particle) => {
            const x = isVisible ? particle.endX : particle.startX;
            const y = isVisible ? particle.endY : particle.startY;
            const opacity = isVisible ? 0.7 : 0.4;
            return renderShape(particle, x, y, opacity);
          })}
        </g>

        {/* Scanning line */}
        <ScanLine />


        {/* Connection lines between adjacent particles when organized */}
        {isVisible && (
          <g className="connection-lines">
            {[0, 1, 2, 3].map((row) =>
              [0, 1, 2, 3].map((col) => {
                const idx = row * 5 + col;
                const particle = particles[idx];
                const nextParticle = particles[idx + 1];
                if (!particle || !nextParticle || col === 4) return null;

                return (
                  <line
                    key={`conn-h-${row}-${col}`}
                    x1={particle.endX}
                    y1={particle.endY}
                    x2={nextParticle.endX}
                    y2={nextParticle.endY}
                    stroke="#2600FF"
                    strokeWidth="0.5"
                    strokeOpacity="0.15"
                    className="transition-all duration-1000"
                    style={{
                      strokeDasharray: 40,
                      strokeDashoffset: isVisible ? 0 : 40,
                      transitionDelay: `${2 + (row * 4 + col) * 0.05}s`
                    }}
                  />
                );
              })
            )}
          </g>
        )}
      </svg>
    </div>
  );
}
