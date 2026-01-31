'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

const CaseStudy: React.FC = () => {
  const t = useTranslations('caseStudy');

  return (
    <section id="case-study" className="py-20 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left Side - Content */}
          <div className="content-stretch flex flex-col gap-8 items-start justify-start">
            {/* Header */}
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[1.1] text-[36px] lg:text-[40px] text-black tracking-[-1.6px]">
              <p className="leading-[normal]">
                {t('headline')}
              </p>
            </div>

            {/* Content Paragraphs */}
            <div className="space-y-6">
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  {t('intro')}
                </p>
              </div>

              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">{t('poTitle')}</strong> {t('poDesc')}
                </p>
              </div>

              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">{t('quoteTitle')}</strong> {t('quoteDesc')}
                </p>
              </div>

              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">{t('warehouseTitle')}</strong> {t('warehouseDesc')}
                </p>
              </div>
            </div>
          </div>

          {/* Right Side - Business Image */}
          <div className="relative">
            <div className="relative">
              {/* Business/Office Image */}
              <div className="bg-[rgba(0,0,0,0.05)] rounded-[25px] h-[500px] w-full flex items-center justify-center overflow-hidden">
                <img
                  src="/wbk.jpg"
                  alt={t('imageAlt')}
                  className="w-full h-full object-cover rounded-[25px]"
                />
              </div>

            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CaseStudy;
