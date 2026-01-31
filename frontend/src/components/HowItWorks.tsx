'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import AutomationPulse from './AlgorithmicArt/AutomationPulse';

const HowItWorks: React.FC = () => {
  const t = useTranslations('howItWorks');
  const [activeStep, setActiveStep] = useState(0);
  const sectionRef = useRef<HTMLElement>(null);
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);

  const steps = [
    {
      number: 1,
      title: t('step1Title'),
      description: t('step1Desc'),
      timeline: t('step1Timeline')
    },
    {
      number: 2,
      title: t('step2Title'),
      description: t('step2Desc'),
      timeline: t('step2Timeline')
    },
    {
      number: 3,
      title: t('step3Title'),
      description: t('step3Desc'),
      timeline: t('step3Timeline')
    }
  ];

  useEffect(() => {
    const handleScroll = () => {
      if (!sectionRef.current) return;

      const section = sectionRef.current;
      const sectionRect = section.getBoundingClientRect();
      const sectionTop = sectionRect.top;
      const sectionHeight = sectionRect.height;
      const windowHeight = window.innerHeight;

      // Check if section is in view
      if (sectionTop <= windowHeight && sectionTop + sectionHeight >= 0) {
        // Calculate progress through the section
        const scrollProgress = Math.max(0, Math.min(1, (windowHeight - sectionTop) / (windowHeight + sectionHeight)));
        
        // Determine active step based on scroll progress
        const stepIndex = Math.min(Math.floor(scrollProgress * steps.length), steps.length - 1);
        setActiveStep(stepIndex);
      }
    };

    window.addEventListener('scroll', handleScroll);
    handleScroll(); // Initial call

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [steps.length]);

  return (
    <section
      ref={sectionRef}
      className="py-20 relative"
    >
      {/* Decorative AutomationPulse background - moved inside the content area to avoid overflow issues */}
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] opacity-[0.05] pointer-events-none hidden lg:block overflow-hidden">
        <AutomationPulse className="w-full h-full" />
      </div>

      {/* Desktop Layout */}
      <div className="hidden lg:block">
        <div className="max-w-7xl mx-auto px-8">
          <div className="grid grid-cols-2 gap-16 items-start">
            
            {/* Left Panel - Fixed Header */}
            <div className="sticky top-20 pt-8">
              <div className="content-stretch flex flex-col items-start justify-start">
                {/* Header Section */}
                <div className="mb-8">
                  <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4">
                    <h2 id="how-it-works-heading">{t('title')}</h2>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] max-w-[500px]">
                    <p className="leading-[normal]">{t('subtitle')}</p>
                  </div>
                </div>

                {/* Progress Indicator */}
                <div className="mb-8">
                  <div className="flex items-center gap-4 mb-4">
                    {steps.map((step, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className={`
                          w-3 h-3 rounded-full transition-all duration-500
                          ${index <= activeStep 
                            ? 'bg-[#2600FF]' 
                            : 'bg-[rgba(0,0,0,0.1)]'
                          }
                        `} />
                        {index < steps.length - 1 && (
                          <div className={`
                            w-8 h-0.5 transition-all duration-500
                            ${index < activeStep ? 'bg-[#2600FF]' : 'bg-[rgba(0,0,0,0.1)]'}
                          `} />
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[13px] text-black tracking-[-0.52px]">
                    Step {activeStep + 1} of {steps.length}: {steps[activeStep].title}
                  </p>
                </div>

                {/* Timeline Summary */}
                <div className="inline-flex items-center gap-4 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-6 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-[#00ff00] rounded-full"></div>
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('existingAgents')}
                    </span>
                  </div>
                  <div className="h-4 w-px bg-[rgba(0,0,0,0.1)]"></div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('customAgents')}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Panel - Cards */}
            <div className="relative pt-8">
              <div className="space-y-8">
                {steps.map((step, index) => (
                  <div 
                    key={step.number}
                    ref={(el) => { stepRefs.current[index] = el; }}
                    className={`
                      transition-all duration-700 ease-out transform
                      ${activeStep === index 
                        ? 'scale-100 opacity-100 translate-y-0' 
                        : 'scale-95 opacity-30 translate-y-4'
                      }
                    `}
                  >
                    <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 h-[340px] flex flex-col justify-between">
                      {/* Step Number */}
                      <div className="absolute -top-4 left-8">
                        <div className="w-10 h-10 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                          <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">{step.number}</span>
                        </div>
                      </div>
                      
                      <div className="pt-6 flex-grow">
                        <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                          <p className="leading-[normal]">{step.title}</p>
                        </div>
                        <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                          <p className="leading-[normal]">{step.description}</p>
                        </div>
                      </div>

                      {/* Timeline Badge */}
                      <div className="mt-4">
                        <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                          <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                          <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                            {step.timeline}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Mobile Layout - Original Design */}
      <div className="lg:hidden">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            {/* Header Section */}
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <p>{t('title')}</p>
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[500px]">
                <p className="leading-[normal]">{t('subtitle')}</p>
              </div>
            </div>

            {/* Steps Grid */}
            <div className="grid grid-cols-1 gap-8 w-full">
              {steps.map((step, index) => (
                <div key={step.number} className="relative">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 h-[340px] flex flex-col justify-between">
                    {/* Step Number */}
                    <div className="absolute -top-4 left-8">
                      <div className="w-10 h-10 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">{step.number}</span>
                      </div>
                    </div>
                    
                    <div className="pt-6 flex-grow">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">{step.title}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">{step.description}</p>
                      </div>
                    </div>

                    {/* Timeline Badge */}
                    <div className="mt-4">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                          {step.timeline}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Timeline Note */}
            <div className="w-full text-center">
              <div className="inline-flex items-center gap-4 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-6 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#00ff00] rounded-full"></div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                    {t('existingAgents')}
                  </span>
                </div>
                <div className="h-4 w-px bg-[rgba(0,0,0,0.1)]"></div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                    {t('customAgents')}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;