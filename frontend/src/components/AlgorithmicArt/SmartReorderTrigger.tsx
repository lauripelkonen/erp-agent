'use client';

import { useEffect, useRef, useState } from 'react';

interface SmartReorderTriggerProps {
  className?: string;
}

export default function SmartReorderTrigger({ className = '' }: SmartReorderTriggerProps) {
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

  // Chart dimensions
  const chartLeft = 60;
  const chartRight = 240;
  const chartTop = 50;
  const chartBottom = 180;
  const chartWidth = chartRight - chartLeft;
  const chartHeight = chartBottom - chartTop;

  // Reorder threshold line position (at 30% from bottom)
  const thresholdY = chartBottom - chartHeight * 0.3;

  // Inventory decline path (starts high, crosses threshold, triggers reorder)
  const inventoryPath = `
    M${chartLeft} ${chartTop + 20}
    L${chartLeft + chartWidth * 0.15} ${chartTop + 35}
    L${chartLeft + chartWidth * 0.3} ${chartTop + 55}
    L${chartLeft + chartWidth * 0.45} ${chartTop + 80}
    L${chartLeft + chartWidth * 0.55} ${thresholdY - 10}
    L${chartLeft + chartWidth * 0.65} ${thresholdY + 5}
    L${chartLeft + chartWidth * 0.7} ${thresholdY + 15}
  `;

  // After reorder, inventory jumps back up
  const reorderPath = `
    M${chartLeft + chartWidth * 0.7} ${thresholdY + 15}
    L${chartLeft + chartWidth * 0.72} ${chartTop + 30}
    L${chartLeft + chartWidth * 0.85} ${chartTop + 45}
    L${chartRight} ${chartTop + 60}
  `;

  // Trigger point (where inventory crosses threshold)
  const triggerX = chartLeft + chartWidth * 0.65;
  const triggerY = thresholdY + 5;

  return (
    <div className={`relative ${className}`}>
      <svg
        ref={svgRef}
        viewBox="0 0 300 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Chart background */}
        <rect
          x={chartLeft - 5}
          y={chartTop - 10}
          width={chartWidth + 10}
          height={chartHeight + 20}
          fill="white"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity="0.1"
          rx="4"
          className="transition-all duration-700"
          style={{ opacity: isVisible ? 1 : 0 }}
        />

        {/* Grid lines */}
        <g
          className="transition-all duration-700"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.2s' }}
        >
          {[0.25, 0.5, 0.75].map((ratio, i) => (
            <line
              key={`h-${i}`}
              x1={chartLeft}
              y1={chartTop + chartHeight * ratio}
              x2={chartRight}
              y2={chartTop + chartHeight * ratio}
              stroke="#2600FF"
              strokeWidth="0.5"
              strokeOpacity="0.1"
              strokeDasharray="4 4"
            />
          ))}
          {[0.25, 0.5, 0.75].map((ratio, i) => (
            <line
              key={`v-${i}`}
              x1={chartLeft + chartWidth * ratio}
              y1={chartTop}
              x2={chartLeft + chartWidth * ratio}
              y2={chartBottom}
              stroke="#2600FF"
              strokeWidth="0.5"
              strokeOpacity="0.1"
              strokeDasharray="4 4"
            />
          ))}
        </g>

        {/* Axes */}
        <g
          className="transition-all duration-700"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.3s' }}
        >
          {/* Y axis */}
          <line x1={chartLeft} y1={chartTop} x2={chartLeft} y2={chartBottom} stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.3" />
          {/* X axis */}
          <line x1={chartLeft} y1={chartBottom} x2={chartRight} y2={chartBottom} stroke="#2600FF" strokeWidth="1.5" strokeOpacity="0.3" />

          {/* Y axis label */}
          <text
            x="25"
            y={(chartTop + chartBottom) / 2}
            textAnchor="middle"
            className="fill-black text-[8px] font-medium opacity-30"
            style={{ fontFamily: 'Inter, sans-serif' }}
            transform={`rotate(-90, 25, ${(chartTop + chartBottom) / 2})`}
          >
            Stock Level
          </text>

          {/* X axis label */}
          <text
            x={(chartLeft + chartRight) / 2}
            y={chartBottom + 25}
            textAnchor="middle"
            className="fill-black text-[8px] font-medium opacity-30"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Time
          </text>
        </g>

        {/* Reorder threshold line */}
        <g
          className="transition-all duration-700"
          style={{ opacity: isVisible ? 1 : 0, transitionDelay: '0.5s' }}
        >
          <line
            x1={chartLeft}
            y1={thresholdY}
            x2={chartRight}
            y2={thresholdY}
            stroke="#2600FF"
            strokeWidth="2"
            strokeOpacity="0.4"
            strokeDasharray="8 4"
          />
          {/* Threshold label */}
          <rect x={chartRight - 55} y={thresholdY - 10} width="50" height="14" fill="white" rx="2" />
          <text
            x={chartRight - 30}
            y={thresholdY + 1}
            textAnchor="middle"
            className="fill-[#2600FF] text-[7px] font-medium"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Reorder Point
          </text>
        </g>

        {/* Inventory decline line */}
        <path
          d={inventoryPath}
          fill="none"
          stroke="#2600FF"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="250"
          strokeDashoffset={isVisible ? 0 : 250}
          className="transition-all duration-[2000ms] ease-out"
          style={{ transitionDelay: '0.8s' }}
        />

        {/* Trigger point indicator */}
        <g
          className="transition-all duration-500"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: '2s'
          }}
        >
          {/* Pulse ring */}
          <circle cx={triggerX} cy={triggerY} r="8" fill="none" stroke="#2600FF" strokeWidth="1">
            {isVisible && (
              <>
                <animate attributeName="r" values="8;20;8" dur="1.5s" repeatCount="indefinite" />
                <animate attributeName="stroke-opacity" values="0.5;0;0.5" dur="1.5s" repeatCount="indefinite" />
              </>
            )}
          </circle>
          {/* Trigger dot */}
          <circle cx={triggerX} cy={triggerY} r="5" fill="#2600FF" />

          {/* Alert icon */}
          <g transform={`translate(${triggerX + 15}, ${triggerY - 20})`}>
            <rect x="-12" y="-10" width="24" height="20" fill="white" stroke="#2600FF" strokeWidth="1" rx="3" />
            <text x="0" y="4" textAnchor="middle" className="fill-[#2600FF] text-[8px] font-bold" style={{ fontFamily: 'Inter, sans-serif' }}>
              PO!
            </text>
          </g>
        </g>

        {/* Stock replenishment line (after PO) */}
        <path
          d={reorderPath}
          fill="none"
          stroke="#2600FF"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="150"
          strokeDashoffset={isVisible ? 0 : 150}
          className="transition-all duration-[1500ms] ease-out"
          style={{ transitionDelay: '2.5s' }}
        />

        {/* Replenishment arrow indicator */}
        <g
          className="transition-all duration-500"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: '3s'
          }}
        >
          <path
            d={`M${chartLeft + chartWidth * 0.71} ${chartTop + 60} L${chartLeft + chartWidth * 0.71} ${chartTop + 30}`}
            stroke="#2600FF"
            strokeWidth="1.5"
            strokeOpacity="0.5"
            strokeDasharray="4 2"
          />
          <polygon
            points={`${chartLeft + chartWidth * 0.71 - 4},${chartTop + 38} ${chartLeft + chartWidth * 0.71},${chartTop + 30} ${chartLeft + chartWidth * 0.71 + 4},${chartTop + 38}`}
            fill="#2600FF"
            fillOpacity="0.5"
          />
          <text
            x={chartLeft + chartWidth * 0.71 + 15}
            y={chartTop + 45}
            className="fill-[#2600FF] text-[7px] font-medium opacity-60"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Stock
          </text>
          <text
            x={chartLeft + chartWidth * 0.71 + 15}
            y={chartTop + 53}
            className="fill-[#2600FF] text-[7px] font-medium opacity-60"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Received
          </text>
        </g>

        {/* Generated PO document (appears after trigger) */}
        <g
          className="transition-all duration-700"
          style={{
            opacity: isVisible ? 1 : 0,
            transitionDelay: '2.3s'
          }}
        >
          <rect x="100" y="210" width="100" height="55" fill="white" stroke="#2600FF" strokeWidth="1.5" rx="4" />

          {/* Document header */}
          <rect x="108" y="218" width="40" height="5" fill="#2600FF" fillOpacity="0.3" rx="1" />

          {/* Document lines */}
          {[0, 1, 2].map((i) => (
            <line
              key={i}
              x1="108"
              y1={232 + i * 8}
              x2={180 - i * 15}
              y2={232 + i * 8}
              stroke="#2600FF"
              strokeWidth="2"
              strokeOpacity="0.15"
              strokeLinecap="round"
            />
          ))}

          {/* Auto-generated badge */}
          <g transform="translate(160, 215)">
            <rect x="0" y="0" width="35" height="12" fill="#2600FF" fillOpacity="0.1" stroke="#2600FF" strokeWidth="0.75" rx="6" />
            <text x="17.5" y="8" textAnchor="middle" className="fill-[#2600FF] text-[6px] font-medium" style={{ fontFamily: 'Inter, sans-serif' }}>
              AUTO
            </text>
          </g>

          <text x="150" y="275" textAnchor="middle" className="fill-black text-[8px] font-medium opacity-40" style={{ fontFamily: 'Inter, sans-serif' }}>
            Purchase Order Generated
          </text>
        </g>

        {/* Connection from trigger to PO */}
        <path
          d={`M${triggerX} ${triggerY + 15} Q${triggerX} 200 150 210`}
          fill="none"
          stroke="#2600FF"
          strokeWidth="1"
          strokeOpacity={isVisible ? 0.3 : 0}
          strokeDasharray="4 4"
          className="transition-all duration-700"
          style={{ transitionDelay: '2.2s' }}
        />

        {/* Animated particle from trigger to PO */}
        {isVisible && (
          <circle r="3" fill="#2600FF" opacity="0">
            <animateMotion
              dur="1s"
              repeatCount="indefinite"
              begin="2.5s"
              path={`M${triggerX} ${triggerY + 15} Q${triggerX} 200 150 210`}
            />
            <animate attributeName="opacity" values="0;0.6;0.6;0.6" dur="1s" repeatCount="indefinite" begin="2.5s" />
          </circle>
        )}
      </svg>
    </div>
  );
}
