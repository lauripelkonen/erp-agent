'use client';

import Footer from '../components/Footer';
import CTASection from '../components/CTASection';
import POGenerationEngine from '../components/AlgorithmicArt/POGenerationEngine';
import SmartReorderTrigger from '../components/AlgorithmicArt/SmartReorderTrigger';
import { useTranslations } from 'next-intl';

export default function PurchaseOrderAutomation() {
  const t = useTranslations('purchaseOrderPage');
  const nav = useTranslations('nav');

  const problems = [
    t('problem1'),
    t('problem2'),
    t('problem3'),
    t('problem4')
  ];

  const solutions = [
    t('solution1'),
    t('solution2'),
    t('solution3'),
    t('solution4')
  ];

  const steps = [
    { number: 1, title: t('step1Title'), description: t('step1Desc') },
    { number: 2, title: t('step2Title'), description: t('step2Desc') },
    { number: 3, title: t('step3Title'), description: t('step3Desc') },
    { number: 4, title: t('step4Title'), description: t('step4Desc') }
  ];

  const features = [
    { title: t('feature1Title'), description: t('feature1Desc') },
    { title: t('feature2Title'), description: t('feature2Desc') },
    { title: t('feature3Title'), description: t('feature3Desc') },
    { title: t('feature4Title'), description: t('feature4Desc') },
    { title: t('feature5Title'), description: t('feature5Desc') },
    { title: t('feature6Title'), description: t('feature6Desc') }
  ];

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff]">
      {/* Navigation */}
      <nav className="absolute left-1/2 max-w-7xl top-10 transform -translate-x-1/2 w-full px-8 z-50">
        <div className="flex items-center justify-between">
          <a href="/" className="h-8 relative shrink-0 hover:opacity-80 transition-opacity">
            <img className="block max-w-none h-full w-auto" src="/ERP-Agent-logo-black.png" alt="ERP Agent - Purchase Order Automation Software" />
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
            {/* Algorithmic Art - PO Generation Engine */}
            <div className="hidden lg:flex items-center justify-center">
              <POGenerationEngine className="w-[320px] h-[320px]" />
            </div>
          </div>
        </div>
      </section>

      {/* Problem/Solution */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[32px] lg:text-[40px] text-black tracking-[-1.3px] lg:tracking-[-1.6px] mb-8">
                <h2>{t('problemTitle')}</h2>
              </div>
              <div className="space-y-4">
                {problems.map((problem, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-red-500 tracking-[-0.6px]">&#10007;</span>
                    <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{problem}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[24px] text-black tracking-[-1px] mb-6">
                <h3>{t('solutionTitle')}</h3>
              </div>
              <div className="space-y-4">
                {solutions.map((solution, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-green-500 tracking-[-0.6px]">&#10003;</span>
                    <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">{solution}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('howItWorksTitle')}</h2>
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
                <p className="leading-[normal]">{t('howItWorksSubtitle')}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 w-full">
              {steps.map((step) => (
                <div key={step.number} className="relative">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 h-full flex flex-col">
                    <div className="absolute -top-4 left-8">
                      <div className="w-10 h-10 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">{step.number}</span>
                      </div>
                    </div>
                    <div className="pt-6 flex-grow">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-black tracking-[-0.72px] mb-3">
                        <p className="leading-[normal]">{step.title}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] text-black tracking-[-0.56px]">
                        <p className="leading-[normal]">{step.description}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Key Features */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('featuresTitle')}</h2>
              </div>
            </div>

            {/* Smart Reorder Visualization */}
            <div className="w-full flex justify-center">
              <SmartReorderTrigger className="w-full max-w-[500px] h-[280px]" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
              {features.map((feature, index) => (
                <div key={index} className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-black tracking-[-0.72px] mb-3">
                    <p className="leading-[normal]">{feature.title}</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] text-black tracking-[-0.56px]">
                    <p className="leading-[normal]">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="py-20 relative bg-gradient-to-b from-[#1a1a1a] to-[#0a0a0a]">
        <div className="max-w-7xl mx-auto px-8 text-center">
          <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-white tracking-[-1.6px] mb-12">
            <h2>{t('resultsTitle')}</h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[48px] text-white tracking-[-1.9px] mb-2">{t('result1Value')}</div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white opacity-60 tracking-[-0.6px]">{t('result1Label')}</div>
            </div>
            <div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[48px] text-white tracking-[-1.9px] mb-2">{t('result2Value')}</div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white opacity-60 tracking-[-0.6px]">{t('result2Label')}</div>
            </div>
            <div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[48px] text-white tracking-[-1.9px] mb-2">{t('result3Value')}</div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white opacity-60 tracking-[-0.6px]">{t('result3Label')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <CTASection />

      {/* Footer */}
      <Footer />
    </div>
  );
}
