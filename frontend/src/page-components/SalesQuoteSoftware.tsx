'use client';

import Footer from '../components/Footer';
import CTASection from '../components/CTASection';
import OrderMatrix from '../components/AlgorithmicArt/OrderMatrix';
import EmailToERPBridge from '../components/AlgorithmicArt/EmailToERPBridge';
import { useTranslations } from 'next-intl';

export default function SalesQuoteSoftware() {
  const t = useTranslations('salesQuotePage');
  const nav = useTranslations('nav');

  const steps = [
    { number: 1, title: t('step1Title'), description: t('step1Desc') },
    { number: 2, title: t('step2Title'), description: t('step2Desc') },
    { number: 3, title: t('step3Title'), description: t('step3Desc') }
  ];

  const traditionalSteps = [
    { step: '1.', text: t('traditionalStep1') },
    { step: '2.', text: t('traditionalStep2') },
    { step: '3.', text: t('traditionalStep3') },
    { step: '4.', text: t('traditionalStep4') },
    { step: '5.', text: t('traditionalStep5') }
  ];

  const agentSteps = [
    { step: '1.', text: t('withAgentStep1') },
    { step: '2.', text: t('withAgentStep2') },
    { step: '3.', text: t('withAgentStep3') },
    { step: '4.', text: t('withAgentStep4') },
    { step: '5.', text: t('withAgentStep5') }
  ];

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff]">
      {/* Navigation */}
      <nav className="absolute left-1/2 max-w-7xl top-10 transform -translate-x-1/2 w-full px-8 z-50">
        <div className="flex items-center justify-between">
          <a href="/" className="h-8 relative shrink-0 hover:opacity-80 transition-opacity">
            <img className="block max-w-none h-full w-auto" src="/ERP-Agent-logo-black.png" alt="ERP Agent - Sales Quote Software" />
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
            {/* Algorithmic Art - Order Matrix */}
            <div className="hidden lg:flex items-center justify-center">
              <OrderMatrix className="w-[300px] h-[300px]" />
            </div>
          </div>
        </div>
      </section>

      {/* Key Metric Banner */}
      <section className="py-12 relative bg-gradient-to-b from-[#2600FF] to-[#1a00cc]">
        <div className="max-w-7xl mx-auto px-8 text-center">
          <div className="font-['Inter:Medium',_sans-serif] font-medium text-[64px] text-white tracking-[-2.5px] mb-2">{t('metricValue')}</div>
          <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-white opacity-90 tracking-[-0.72px]">{t('metricLabel')}</div>
        </div>
      </section>

      {/* How Quote Generation Works */}
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

            {/* Algorithmic Art - Email to ERP Bridge */}
            <div className="w-full flex justify-center">
              <EmailToERPBridge className="w-full max-w-[800px] h-[300px]" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
              {steps.map((step) => (
                <div key={step.number} className="relative">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 h-full flex flex-col">
                    <div className="absolute -top-4 left-8">
                      <div className="w-10 h-10 bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] rounded-full flex items-center justify-center shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)]">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px]">{step.number}</span>
                      </div>
                    </div>
                    <div className="pt-6 flex-grow">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[20px] text-black tracking-[-0.8px] mb-4">
                        <p className="leading-[normal]">{step.title}</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
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

      {/* Features */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('featuresTitle')}</h2>
              </div>
            </div>

            <div className="space-y-8 w-full">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">{t('feature1Title')}</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">{t('feature1Desc')}</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[13px] text-black tracking-[-0.52px] mb-2">
                      {t('feature1Example')}
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('feature1Result')}
                    </div>
                  </div>
                </div>
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">{t('feature2Title')}</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">{t('feature2Desc')}</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('feature2Result')}
                    </div>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">{t('feature3Title')}</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">{t('feature3Desc')}</p>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {['.xlsx', '.pdf', '.csv', 'email'].map((format) => (
                      <div key={format} className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">{format}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">{t('feature4Title')}</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">{t('feature4Desc')}</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      {t('feature4Result')}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>{t('comparisonTitle')}</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
              {/* Traditional Process */}
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-6">
                  <p className="leading-[normal]">{t('traditionalTitle')}</p>
                </div>
                <div className="space-y-4">
                  {traditionalSteps.map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{item.step}</span>
                      <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{item.text}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-6 border-t border-[rgba(0,0,0,0.1)]">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.3px]">{t('traditionalTime')}</div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{t('perQuote')}</div>
                </div>
              </div>

              {/* With ERP Agent */}
              <div className="bg-gradient-to-br from-[rgba(38,0,255,0.05)] to-[rgba(38,0,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(38,0,255,0.25)] p-8 border-2 border-[#2600FF]">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-6">
                  <p className="leading-[normal]">{t('withAgentTitle')}</p>
                </div>
                <div className="space-y-4">
                  {agentSteps.map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-[#2600FF] tracking-[-0.6px]">{item.step}</span>
                      <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">{item.text}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-6 border-t border-[rgba(38,0,255,0.2)]">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-[#2600FF] tracking-[-1.3px]">{t('withAgentTime')}</div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">{t('perQuote')}</div>
                </div>
              </div>
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
