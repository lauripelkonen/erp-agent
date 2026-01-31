'use client';

import Footer from '../components/Footer';
import CTASection from '../components/CTASection';
import WarehouseNetworkFlow from '../components/AlgorithmicArt/WarehouseNetworkFlow';
import { useTranslations } from 'next-intl';

export default function WholesaleDistributionERP() {
  const t = useTranslations('wholesaleDistributionPage');
  const nav = useTranslations('nav');

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff]">
      {/* Navigation */}
      <nav className="absolute left-1/2 max-w-7xl top-10 transform -translate-x-1/2 w-full px-8 z-50">
        <div className="flex items-center justify-between">
          <a href="/" className="h-8 relative shrink-0 hover:opacity-80 transition-opacity">
            <img className="block max-w-none h-full w-auto" src="/ERP-Agent-logo-black.png" alt="ERP Agent - Wholesale Distribution ERP Software" />
          </a>
          <a href="/#cta" className="bg-black box-border content-stretch flex gap-2.5 items-center justify-center px-4 py-1.5 relative rounded-[36px] shrink-0 border-none cursor-pointer hover:bg-gray-800 transition-colors">
            <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[13px] text-center text-nowrap text-white tracking-[-0.52px]">
              <p className="leading-[normal] whitespace-pre">{nav('getStarted')}</p>
            </div>
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-28 lg:pt-40 pb-16 lg:pb-20 px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 mb-4 lg:mb-6">
                <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                  {t('badge')}
                </span>
              </div>
              <h1 className="font-['Inter:Regular',_sans-serif] font-normal leading-[1.1] text-[28px] lg:text-[48px] text-black tracking-[-1.1px] lg:tracking-[-1.9px] mb-4 lg:mb-6">
                <span className="block opacity-40">{t('title1')}</span>
                <span className="block">{t('title2')}</span>
              </h1>
              <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] lg:text-[17px] text-black tracking-[-0.6px] leading-[1.6] mb-6 lg:mb-8 max-w-[600px]">
                {t('description')}
              </p>
              <div className="content-stretch flex gap-6 items-start justify-start">
                <a href="/#cta" className="bg-gradient-to-b border-none box-border content-stretch cursor-pointer flex from-[#4d4d4d] gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0 to-[#0a0a0a] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-center text-nowrap text-white tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">{t('cta1')}</p>
                  </div>
                </a>
                <a href="/#case-study" className="bg-[rgba(0,0,0,0.02)] border-none box-border content-stretch cursor-pointer flex gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0">
                  <div aria-hidden="true" className="absolute border border-[rgba(0,0,0,0.1)] border-solid inset-0 pointer-events-none rounded-[36px]" />
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-[rgba(0,0,0,0.7)] text-center text-nowrap tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">{t('cta2')}</p>
                  </div>
                </a>
              </div>
            </div>
            {/* Algorithmic Art - Warehouse Network Flow */}
            <div className="hidden lg:flex items-center justify-center">
              <WarehouseNetworkFlow className="w-[300px] h-[300px]" />
            </div>
          </div>
        </div>
      </section>

      {/* Key Benefits */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('benefitsTitle')}</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  {t('benefit1Value')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  {t('benefit1Title')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">{t('benefit1Desc')}</p>
                </div>
              </div>
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  {t('benefit2Value')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  {t('benefit2Title')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">{t('benefit2Desc')}</p>
                </div>
              </div>
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  {t('benefit3Value')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  {t('benefit3Title')}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">{t('benefit3Desc')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('featuresTitle')}</h2>
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
                <p className="leading-[normal]">{t('featuresSubtitle')}</p>
              </div>
            </div>

            {/* Bento Grid */}
            <div className="space-y-8 w-full">
              {/* First Row */}
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-8 items-stretch">
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">{t('feature1Title')}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">{t('feature1Desc')}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature1Tag1')}</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature1Tag2')}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">{t('feature2Title')}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">{t('feature2Desc')}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature2Tag1')}</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature2Tag2')}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Second Row */}
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-8 items-stretch">
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">{t('feature3Title')}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">{t('feature3Desc')}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature3Tag1')}</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature3Tag2')}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">{t('feature4Title')}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">{t('feature4Desc')}</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature4Tag1')}</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{t('feature4Tag2')}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ERP Integrations */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8 text-center">
          <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4">
            <h2>{t('integrationsTitle')}</h2>
          </div>
          <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-8 max-w-[600px] mx-auto">
            <p className="leading-[normal]">{t('integrationsDesc')}</p>
          </div>
          <a href="/#integrations" className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-[#2600FF] tracking-[-0.6px] hover:opacity-80 transition-opacity">
            {t('integrationsLink')} &rarr;
          </a>
        </div>
      </section>

      {/* CTA Section */}
      <CTASection />

      {/* Footer */}
      <Footer />
    </div>
  );
}
