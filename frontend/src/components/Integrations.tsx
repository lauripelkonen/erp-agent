'use client';

import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';

const Integrations: React.FC = () => {
  const t = useTranslations('integrations');
  const [hoveredElement, setHoveredElement] = useState<string | null>(null);
  const [animationPhase, setAnimationPhase] = useState(0);

  // Animation cycle for the connections
  useEffect(() => {
    const interval = setInterval(() => {
      setAnimationPhase((prev) => (prev + 1) % 3);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Geometry based on Figma with increased spacing and precise line endpoints
  const canvas = { width: 563, height: 275 };

  const eRect = { x: 255, y: 100, w: 54.58, h: 76.52 };
  const center = { x: eRect.x + eRect.w / 2, y: eRect.y + eRect.h / 2 };

  // Move boxes outward for more spacing
  const appsRect = { x: 16, y: 186, w: 103, h: 34 };
  const erpRect = { x: 444, y: 16, w: 103, h: 34 };
  const llmRect = { x: 444, y: 224, w: 103, h: 34 };

  const getCenter = (r: { x: number; y: number; w: number; h: number }) => ({
    x: r.x + r.w / 2,
    y: r.y + r.h / 2,
  });

  const intersectRayWithRect = (
    origin: { x: number; y: number },
    dir: { x: number; y: number },
    rect: { x: number; y: number; w: number; h: number }
  ) => {
    const candidates: { t: number; x: number; y: number }[] = [];
    const xMin = rect.x;
    const xMax = rect.x + rect.w;
    const yMin = rect.y;
    const yMax = rect.y + rect.h;

    if (Math.abs(dir.x) > 1e-6) {
      const t1 = (xMin - origin.x) / dir.x;
      const y1 = origin.y + t1 * dir.y;
      if (t1 > 0 && y1 >= yMin && y1 <= yMax) candidates.push({ t: t1, x: xMin, y: y1 });

      const t2 = (xMax - origin.x) / dir.x;
      const y2 = origin.y + t2 * dir.y;
      if (t2 > 0 && y2 >= yMin && y2 <= yMax) candidates.push({ t: t2, x: xMax, y: y2 });
    }
    if (Math.abs(dir.y) > 1e-6) {
      const t3 = (yMin - origin.y) / dir.y;
      const x3 = origin.x + t3 * dir.x;
      if (t3 > 0 && x3 >= xMin && x3 <= xMax) candidates.push({ t: t3, x: x3, y: yMin });

      const t4 = (yMax - origin.y) / dir.y;
      const x4 = origin.x + t4 * dir.x;
      if (t4 > 0 && x4 >= xMin && x4 <= xMax) candidates.push({ t: t4, x: x4, y: yMax });
    }
    if (candidates.length === 0) return { x: origin.x, y: origin.y };
    candidates.sort((a, b) => a.t - b.t);
    return { x: candidates[0].x, y: candidates[0].y };
  };

  const computeLine = (targetRect: { x: number; y: number; w: number; h: number }) => {
    const targetCenter = getCenter(targetRect);
    const dirToTarget = { x: targetCenter.x - center.x, y: targetCenter.y - center.y };
    const end = intersectRayWithRect(center, dirToTarget, targetRect);
    const start = intersectRayWithRect(center, dirToTarget, eRect);
    return { x1: start.x, y1: start.y, x2: end.x, y2: end.y };
  };

  const lines = {
    apps: computeLine(appsRect),
    erp: computeLine(erpRect),
    llm: computeLine(llmRect),
  };

  // Icon positions relative to Apps box to avoid overlap
  const iconImage10 = { x: appsRect.x - 26, y: appsRect.y - 36, w: 30, h: 23 };
  const iconFrame = { x: appsRect.x + 67, y: appsRect.y + 48, w: 30, h: 29 };
  const icon583130 = { x: appsRect.x + 114, y: appsRect.y - 13, w: 30, h: 30 };
  const icon583132 = { x: appsRect.x - 30, y: appsRect.y + 34, w: 30, h: 30 };

  // Shared fade class for all icons/badges
  const fadeIconClass = 'opacity-60 hover:opacity-100 transition-opacity duration-300';

  // Responsive scale for mobile (keeps desktop 1:1)
  const containerRef = useRef<HTMLDivElement>(null);
  const [stageScale, setStageScale] = useState(1);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const baseW = canvas.width; // 563
    const baseH = canvas.height; // 275
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const cw = entry.contentRect.width;
        // Only scale down below base size; keep desktop identical
        const nextScale = Math.min(cw / baseW, 1);
        setStageScale(nextScale > 0 ? nextScale : 1);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [canvas.width]);

  return (
    <section id="integrations" className="py-20 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col gap-16 items-start justify-start relative">
          
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full">
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[28px] sm:text-[32px] md:text-[40px] text-black tracking-[-1.6px] mb-4 text-center px-4">
              <p>{t('title')}</p>
            </div>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] sm:text-[15px] text-black tracking-[-0.6px] text-center max-w-[700px] px-4">
              <p className="leading-[normal]">{t('subtitle')}</p>
            </div>
          </div>

          {/* Integration Diagram */}
          <div className="w-full flex justify-center px-4">
            <div ref={containerRef} className="relative w-full max-w-[563px] mx-auto" style={{ height: `${canvas.height * stageScale}px` }}>
              {/* Scaled stage maintains exact desktop layout while shrinking on mobile */}
              <div className="absolute top-0 left-0" style={{ width: `${canvas.width}px`, height: `${canvas.height}px`, transform: `scale(${stageScale})`, transformOrigin: 'top left' }}>
              
              {/* Central Glow Effect - positioned exactly like Figma */}
              <div 
                className="absolute rounded-full opacity-60 transition-all duration-1000"
                style={{
                  left: '242px',
                  top: '94px',
                  width: '90px',
                  height: '90px',
                  background: 'linear-gradient(180deg, rgba(38, 0, 255, 0.22) 0%, rgba(38, 0, 255, 0.8) 100%)',
                  filter: 'blur(35px)',
                  transform: `scale(${hoveredElement ? 1.2 : 1})`
                }}
              />

              {/* Central ERP Agent Logo - positioned exactly like Figma */}
              <div 
                className="absolute z-10 cursor-pointer transition-all duration-300 hover:scale-110"
                style={{
                  left: '255px',
                  top: '100px',
                  width: '54.58px',
                  height: '76.52px'
                }}
                onMouseEnter={() => setHoveredElement('center')}
                onMouseLeave={() => setHoveredElement(null)}
              >
                <img 
                  src="/figma/e-logo.png" 
                  alt="ERP Agent Logo" 
                  className="w-full h-full object-contain"
                />
              </div>

              {/* Connection Lines - using exact Figma coordinates */}
              <svg 
                className="absolute inset-0 w-full h-full pointer-events-none" 
                viewBox={`0 0 ${canvas.width} ${canvas.height}`}
                preserveAspectRatio="none"
              >
                {/* Line to Apps */}
                <line 
                  x1={lines.apps.x1} y1={lines.apps.y1} x2={lines.apps.x2} y2={lines.apps.y2}
                  stroke="#000000" 
                  strokeWidth="1.5"
                  className={`transition-all duration-500 ${
                    animationPhase === 0 || hoveredElement === 'apps' ? 'opacity-100' : 'opacity-40'
                  }`}
                  strokeDasharray={hoveredElement === 'apps' ? '5,5' : 'none'}
                  style={{ stroke: animationPhase === 0 || hoveredElement === 'apps' ? '#2600FF' : '#000000' }}
                />
                
                {/* Line to ERP */}
                <line 
                  x1={lines.erp.x1} y1={lines.erp.y1} x2={lines.erp.x2} y2={lines.erp.y2}
                  stroke="#000000" 
                  strokeWidth="1.5"
                  className={`transition-all duration-500 ${
                    animationPhase === 1 || hoveredElement === 'erp' ? 'opacity-100' : 'opacity-40'
                  }`}
                  strokeDasharray={hoveredElement === 'erp' ? '5,5' : 'none'}
                  style={{ stroke: animationPhase === 1 || hoveredElement === 'erp' ? '#2600FF' : '#000000' }}
                />
                
                {/* Line to LLM */}
                <line 
                  x1={lines.llm.x1} y1={lines.llm.y1} x2={lines.llm.x2} y2={lines.llm.y2}
                  stroke="#000000" 
                  strokeWidth="1.5"
                  className={`transition-all duration-500 ${
                    animationPhase === 2 || hoveredElement === 'llm' ? 'opacity-100' : 'opacity-40'
                  }`}
                  strokeDasharray={hoveredElement === 'llm' ? '5,5' : 'none'}
                  style={{ stroke: animationPhase === 2 || hoveredElement === 'llm' ? '#2600FF' : '#000000' }}
                />
              </svg>

              {/* ERP Box - positioned exactly like Figma */}
              <div 
                className="absolute cursor-pointer transition-all duration-300 hover:scale-105"
                style={{ left: `${erpRect.x}px`, top: `${erpRect.y}px`, width: `${erpRect.w}px`, height: `${erpRect.h}px` }}
                onMouseEnter={() => setHoveredElement('erp')}
                onMouseLeave={() => setHoveredElement(null)}
              >
                <div className="border border-black rounded-[20px] px-6 py-2 bg-white shadow-lg w-full h-full flex items-center justify-center">
                  <span className="font-mono text-[20px] font-normal text-center">ERP</span>
                </div>
              </div>

              {/* NetSuite Logo - positioned above ERP, faded until hover */}
              <div className="absolute" style={{ left: '269px', top: '4px', width: '120px', height: '30px' }}>
                <img 
                  src="/figma/image-583129.png" 
                  alt="NetSuite" 
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>

              {/* SAP Logo - positioned to the right of NetSuite */}
              <div className="absolute" style={{ left: '400px', top: '2px', width: '70px', height: '35px' }}>
                <img
                  src="/erp-logos/sap.svg"
                  alt="SAP"
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>

              {/* Visma Logo - positioned below ERP box */}
              <div className="absolute" style={{ left: '455px', top: '58px', width: '100px', height: '30px' }}>
                <img
                  src="/erp-logos/visma.svg"
                  alt="Visma"
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>

              {/* Lemonsoft Text */}
              <div
                className="absolute"
                style={{
                  left: '350px',
                  top: '65px',
                  width: '71px',
                  height: '15px'
                }}
              >
                <span className={`text-[14px] font-normal tracking-[-0.5px] ${fadeIconClass}`}>Lemonsoft</span>
              </div>

              {/* LLM Box - positioned exactly like Figma */}
              <div 
                className="absolute cursor-pointer transition-all duration-300 hover:scale-105"
                style={{ left: `${llmRect.x}px`, top: `${llmRect.y}px`, width: `${llmRect.w}px`, height: `${llmRect.h}px` }}
                onMouseEnter={() => setHoveredElement('llm')}
                onMouseLeave={() => setHoveredElement(null)}
              >
                <div className="border border-black rounded-[20px] px-6 py-2 bg-white shadow-lg w-full h-full flex items-center justify-center">
                  <span className="font-mono text-[20px] font-normal text-center">LLM</span>
                </div>
              </div>

              {/* LLM brand icons placed at Figma coordinates (relative to canvas) */}
              <img src="/figma/openai-logo.png" alt="OpenAI" className={`absolute ${fadeIconClass}`} style={{ left: '462px', top: '178px', width: '30px', height: '30px' }} />
              <img src="/figma/gemini-logo.png" alt="Gemini" className={`absolute ${fadeIconClass}`} style={{ left: '560px', top: '235px', width: '30px', height: '30px' }} />
              <img src="/figma/claude-logo.png" alt="Claude" className={`absolute ${fadeIconClass}`} style={{ left: '339px', top: '224px', width: '30px', height: '30px' }} />

              {/* Apps Box - positioned exactly like Figma */}
              <div 
                className="absolute cursor-pointer transition-all duration-300 hover:scale-105"
                style={{ left: `${appsRect.x}px`, top: `${appsRect.y}px`, width: `${appsRect.w}px`, height: `${appsRect.h}px` }}
                onMouseEnter={() => setHoveredElement('apps')}
                onMouseLeave={() => setHoveredElement(null)}
              >
                <div className="border border-black rounded-[20px] px-6 py-2 bg-white shadow-lg w-full h-full flex items-center justify-center">
                  <span className="font-mono text-[20px] font-normal text-center">Apps</span>
                </div>
              </div>
                
              {/* App Icons - positioned exactly like Figma to avoid overlap */}
              
              {/* Image 10 - top left of Apps */}
              <div className="absolute" style={{ left: `${iconImage10.x}px`, top: `${iconImage10.y}px`, width: `${iconImage10.w}px`, height: `${iconImage10.h}px` }}>
                <img 
                  src="/figma/image-10.png" 
                  alt="App Icon" 
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>
              
              {/* Image 2 - in frame */}
              <div 
                className="absolute bg-white rounded-[11.85px] flex items-center justify-center"
                style={{ left: `${iconFrame.x}px`, top: `${iconFrame.y}px`, width: `${iconFrame.w}px`, height: `${iconFrame.h}px` }}
              >
                <img 
                  src="/figma/image-2.png" 
                  alt="App Icon" 
                  className={`w-[30px] h-[28px] object-contain ${fadeIconClass}`}
                />
              </div>
              
              {/* Image 583130 - right of Apps */}
              <div className="absolute" style={{ left: `${icon583130.x}px`, top: `${icon583130.y}px`, width: `${icon583130.w}px`, height: `${icon583130.h}px` }}>
                <img 
                  src="/figma/image-583130.png" 
                  alt="App Icon" 
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>
              
              {/* Image 583132 - bottom left */}
              <div className="absolute" style={{ left: `${icon583132.x}px`, top: `${icon583132.y}px`, width: `${icon583132.w}px`, height: `${icon583132.h}px` }}>
                <img 
                  src="/figma/image-583132.png" 
                  alt="App Icon" 
                  className={`w-full h-full object-contain ${fadeIconClass}`}
                />
              </div>

              {/* Hover Information */}
              {hoveredElement && (
                <div className="absolute bottom-[-40px] left-1/2 transform -translate-x-1/2 bg-black text-white px-4 py-2 rounded-lg text-sm transition-all duration-300 z-20 max-w-xs text-center whitespace-nowrap">
                  {hoveredElement === 'center' && t('centerTooltip')}
                  {hoveredElement === 'erp' && t('erpTooltip')}
                  {hoveredElement === 'llm' && t('llmTooltip')}
                  {hoveredElement === 'apps' && t('appsTooltip')}
                </div>
              )}
              </div>
              
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Integrations;
