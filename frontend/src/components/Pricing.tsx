'use client';

import React, { useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';

const Pricing: React.FC = () => {
  const t = useTranslations('pricing');
  const vantaRef = useRef<HTMLElement>(null);
  const vantaEffect = useRef<any>(null);

  useEffect(() => {
    const loadDependencies = async () => {
      // Load THREE.js first
      if (!(window as any).THREE) {
        const THREE = await import('three');
        (window as any).THREE = THREE;
      }

      // Load Vanta dots
      if (!(window as any).VANTA) {
        await import('vanta/dist/vanta.dots.min.js');
      }

      // Initialize the effect
      if (vantaRef.current && !vantaEffect.current && (window as any).VANTA) {
        try {
          vantaEffect.current = (window as any).VANTA.DOTS({
            el: vantaRef.current,
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.00,
            minWidth: 200.00,
            scale: 1.00,
            scaleMobile: 1.00,
            color: 0x000000,
            color2: 0x000000,
            backgroundColor: 0xffffff,
            size: 3.70,
            spacing: 24.00,
            showLines: false
          });
          console.log('Vanta dots effect loaded successfully');
        } catch (error) {
          console.error('Error initializing Vanta effect:', error);
        }
      }
    };

    // Add a small delay to ensure DOM is ready
    const timer = setTimeout(loadDependencies, 100);
    
    return () => {
      clearTimeout(timer);
      if (vantaEffect.current) {
        vantaEffect.current.destroy();
        vantaEffect.current = null;
      }
    };
  }, []);

  return (
    <section ref={vantaRef} id="pricing" className="py-20 relative">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
          
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full">
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
              <p>{t('title')}</p>
            </div>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
              <p className="leading-[normal]">{t('subtitle')}</p>
            </div>
          </div>

          {/* Pricing Structure */}
          <div className="w-full bg-white/2 border border-[rgba(0,0,0,0.08)] rounded-[25.5px] p-12 text-center backdrop-blur-sm">
            <div className="max-w-4xl mx-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* One-time Setup */}
                <div className="bg-white/2 overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 backdrop-blur-sm">
                  <div className="flex items-center justify-center mb-6">
                    <div className="w-12 h-12 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">1</span>
                    </div>
                  </div>
                  <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-0.96px] mb-4">
                    <p className="leading-[normal]">{t('setupTitle')}</p>
                  </h3>
                  <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-60 text-[15px] text-black tracking-[-0.6px] leading-[1.5] mb-6">
                    {t('setupDesc')}
                  </p>
                  <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                    <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('setupBadge')}
                    </span>
                  </div>
                </div>

                {/* Monthly SaaS */}
                <div className="bg-white/2 overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 backdrop-blur-sm">
                  <div className="flex items-center justify-center mb-6">
                    <div className="w-12 h-12 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">2</span>
                    </div>
                  </div>
                  <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-0.96px] mb-4">
                    <p className="leading-[normal]">{t('monthlyTitle')}</p>
                  </h3>
                  <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-60 text-[15px] text-black tracking-[-0.6px] leading-[1.5] mb-6">
                    {t('monthlyDesc')}
                  </p>
                  <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                    <div className="w-2 h-2 bg-[#00ff00] rounded-full"></div>
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('monthlyBadge')}
                    </span>
                  </div>
                </div>

              </div>

              {/* Contact Note */}
              <div className="mt-12 pt-8 border-t border-[rgba(0,0,0,0.08)]">
                <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-50 text-[14px] text-black tracking-[-0.56px] leading-[1.5]">
                  {t('contactNote')}
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

export default Pricing;