'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import DataFlowNetwork from './AlgorithmicArt/DataFlowNetwork';

const Bento: React.FC = () => {
  const t = useTranslations('bento');
  const features = [
    {
      title: t('poTitle'),
      description: t('poDesc'),
    },
    {
      title: t('quoteTitle'),
      description: t('quoteDesc'),
    },
    {
      title: t('warehouseTitle'),
      description: t('warehouseDesc'),
    },
    {
      title: t('insightsTitle'),
      description: t('insightsDesc'),
    }
  ];

  return (
    <section id="features" className="py-20 relative overflow-hidden">
      {/* Decorative DataFlowNetwork background */}
      <div className="absolute top-0 right-0 w-[600px] h-[360px] opacity-[0.07] pointer-events-none hidden lg:block">
        <DataFlowNetwork className="w-full h-full" />
      </div>

      <div className="max-w-7xl mx-auto px-8 relative z-10">
        <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full">
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
              <h2 id="features-heading">{t('title')}</h2>
            </div>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
              <p className="leading-[normal]">{t('subtitle')}</p>
            </div>
          </div>

          {/* Bento Grid */}
          <div className="space-y-8 w-full">
            {/* First Row - Purchase Orders (2/5) and Quotes (3/5) */}
            <div className="grid grid-cols-1 lg:grid-cols-6 gap-8 items-stretch">
              {/* Purchase Order Automation - Smaller Card */}
              <div className="lg:col-span-2 flex">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">

                  {/* Content */}
                  <div className="mb-8">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                      <p className="leading-[normal]">{features[0].title}</p>
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                      <p className="leading-[normal]">{features[0].description}</p>
                    </div>
                  </div>

                  {/* Visual Element */}
                  <div className="bg-[rgba(0,0,0,0.05)] rounded-[15px] aspect-[2.85/1] flex items-center justify-center flex-grow">
                    <img src="/Purchase_order.png" alt="Purchase Order Interface" className="w-full h-full object-cover rounded-[15px]" />
                  </div>
                </div>
              </div>

              {/* Quote & Offer Generation - Larger Card */}
              <div className="lg:col-span-4 flex">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">

                  {/* Content */}
                  <div className="mb-8">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[28px] text-black tracking-[-1.2px] mb-4">
                      <p className="leading-[normal]">{features[1].title}</p>
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] max-w-[400px]">
                      <p className="leading-[normal]">{features[1].description}</p>
                    </div>
                  </div>

                  {/* Visual Element */}
                  <div className="bg-[rgba(0,0,0,0.05)] rounded-[15px] aspect-[2.85/1] flex items-center justify-center flex-grow">
                    <img src="/offer-automation.png" alt="Quote Generation Dashboard" className="w-full h-full object-cover rounded-[15px]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Second Row - Warehouse Transfers (3/5) and ERP Insights (2/5) */}
            <div className="grid grid-cols-1 lg:grid-cols-6 gap-8 items-stretch">
              {/* Warehouse Transfers - Larger Card */}
              <div className="lg:col-span-4 flex">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">

                  {/* Content */}
                  <div className="mb-8">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[28px] text-black tracking-[-1.2px] mb-4">
                      <p className="leading-[normal]">{features[2].title}</p>
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] max-w-[400px]">
                      <p className="leading-[normal]">{features[2].description}</p>
                    </div>
                  </div>

                  {/* Visual Element */}
                  <div className="bg-[rgba(0,0,0,0.05)] rounded-[15px] aspect-[2.85/1] flex items-center justify-center flex-grow">
                    <img src="/transfers-page.png" alt="Transfer Management" className="w-full h-full object-cover rounded-[15px]" />
                  </div>
                </div>
              </div>

              {/* ERP Insights & Analytics - Smaller Card */}
              <div className="lg:col-span-2 flex">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">

                  {/* Content */}
                  <div className="mb-8">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                      <p className="leading-[normal]">{features[3].title}</p>
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                      <p className="leading-[normal]">{features[3].description}</p>
                    </div>
                  </div>

                  {/* Visual Element */}
                  <div className="bg-[rgba(0,0,0,0.05)] rounded-[15px] aspect-[2.85/1] flex items-center justify-center flex-grow">
                    <img src="/business-chat.png" alt="Analytics & Insights Dashboard" className="w-full h-full object-cover rounded-[15px]" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Bento;