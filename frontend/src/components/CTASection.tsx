'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

const CTASection: React.FC = () => {
  const t = useTranslations('ctaSection');
  return (
    <section id="cta" className="py-20 relative bg-gradient-to-b from-white to-[#f8f9fa]">
      <div className="max-w-7xl mx-auto px-8">
        <div className="relative bg-white border border-[#E6E6E6] rounded-[36px] p-12 lg:p-16 shadow-[0px_17px_37px_0px_rgba(0,0,0,0.04),0px_66px_66px_0px_rgba(0,0,0,0.03),0px_266px_106px_0px_rgba(0,0,0,0.01)]">
          
          {/* Background Gradient Elements */}
          <div className="absolute inset-0 overflow-hidden rounded-[36px]">
            <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-gradient-to-bl from-[#2600FF]/5 to-transparent rounded-full blur-3xl"></div>
            <div className="absolute bottom-0 left-0 w-[200px] h-[200px] bg-gradient-to-tr from-[#2600FF]/3 to-transparent rounded-full blur-2xl"></div>
          </div>

          <div className="relative grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            
            {/* Left Side - Content */}
            <div className="space-y-8">
              <div>
                <h2 className="font-['Inter:Regular',_sans-serif] font-normal text-[32px] lg:text-[42px] text-black tracking-[-1.3px] lg:tracking-[-1.7px] leading-[1.1] mb-6">
                  {t('title')}
                </h2>
                <p className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] lg:text-[18px] text-[#686E73] tracking-[-0.64px] lg:tracking-[-0.72px] leading-[1.5] mb-8">
                  {t('subtitle')}
                </p>
              </div>

              {/* Benefits List */}
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-[#2600FF] flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">
                    {t('benefit1')}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-[#2600FF] flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">
                    {t('benefit2')}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 rounded-full bg-[#2600FF] flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">
                    {t('benefit3')}
                  </span>
                </div>
              </div>

              {/* CTA Button */}
              <div className="pt-4">
                <a
                  href="https://cal.com/lauri-pelkonen"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-3 bg-gradient-to-b from-[#2600FF] to-[#1a00cc] text-white font-['Inter:Medium',_sans-serif] font-medium text-[16px] lg:text-[18px] tracking-[-0.64px] lg:tracking-[-0.72px] px-8 py-4 rounded-[36px] shadow-[0px_8px_32px_rgba(38,0,255,0.25),0px_4px_16px_rgba(38,0,255,0.15),0px_2px_8px_rgba(38,0,255,0.1)] hover:shadow-[0px_12px_40px_rgba(38,0,255,0.3),0px_6px_20px_rgba(38,0,255,0.2),0px_3px_10px_rgba(38,0,255,0.15)] hover:scale-105 transition-all duration-200 group"
                >
                  <span>{t('button')}</span>
                  <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Right Side - Founder Card */}
            <div className="flex justify-center lg:justify-end">
              <div className="bg-gradient-to-br from-white to-[#f8f9fa] border border-[#E6E6E6] rounded-[24px] p-8 shadow-[0px_8px_32px_rgba(0,0,0,0.08),0px_4px_16px_rgba(0,0,0,0.05),0px_2px_8px_rgba(0,0,0,0.03)] max-w-sm w-full">
                
                {/* Photo */}
                <div className="flex justify-center mb-6">
                  <div className="relative">
                    <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-white shadow-[0px_8px_32px_rgba(0,0,0,0.15)]">
                      <img 
                        src="/lauri.png" 
                        alt="Lauri Pelkonen, Founder & CEO of ERP Agent" 
                        className="w-full h-full object-cover"
                      />
                    </div>
                    {/* Verified Badge */}
                    <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-[#2600FF] rounded-full flex items-center justify-center shadow-lg">
                      <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Info */}
                <div className="text-center space-y-3">
                  <div>
                    <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[20px] text-black tracking-[-0.8px] mb-1">
                      {t('founderName')}
                    </h3>
                    <p className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#2600FF] tracking-[-0.56px]">
                      {t('founderTitle')}
                    </p>
                  </div>

                  <div className="pt-2 space-y-3">
                    <p className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-[#686E73] tracking-[-0.52px] leading-[1.4] italic">
                      &quot;{t('founderQuote')}&quot;
                    </p>
                    <div className="space-y-2">
                      <div className="flex items-center justify-center gap-2 text-[12px]">
                        <svg className="w-4 h-4 text-[#2600FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[#2600FF] tracking-[-0.48px]">
                          lauri (at) erp-agent.com
                        </span>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-[12px]">
                        <svg className="w-4 h-4 text-[#2600FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        <a href="tel:+358401234567" className="font-['Inter:Medium',_sans-serif] font-medium text-[#2600FF] tracking-[-0.48px] hover:opacity-80 transition-opacity">
                          +358 40 709 3234
                        </a>
                      </div>
                    </div>
                  </div>

                  {/* Quick Stats */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#F0F0F0]">
                    <div className="text-center">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-black tracking-[-0.72px]">
                        40K+
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[11px] text-[#686E73] tracking-[-0.44px]">
                        {t('hoursSaved')}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-black tracking-[-0.72px]">
                        100%
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[11px] text-[#686E73] tracking-[-0.44px]">
                        {t('successRate')}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Trust Indicators */}
          <div className="relative mt-12 pt-8 border-t border-[#F0F0F0]">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-[#00D084] rounded-full"></div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-[#686E73] tracking-[-0.52px]">
                    {t('responseTime')}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <svg key={i} className="w-4 h-4 text-[#FFD700]" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-[#686E73] tracking-[-0.52px] ml-1">
                    {t('rating')}
                  </span>
                </div>
              </div>

              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-[#686E73] tracking-[-0.52px]">
                {t('noCommitment')}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;
