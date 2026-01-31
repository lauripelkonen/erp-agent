'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

const Security: React.FC = () => {
  const t = useTranslations('security');

  const features = [
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
        </svg>
      ),
      title: t('euHostedTitle'),
      description: t('euHostedDesc'),
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z" />
        </svg>
      ),
      title: t('zeroRetentionTitle'),
      description: t('zeroRetentionDesc'),
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
      ),
      title: t('noTrainingTitle'),
      description: t('noTrainingDesc'),
    },
    {
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
        </svg>
      ),
      title: t('dataControlTitle'),
      description: t('dataControlDesc'),
    },
  ];

  return (
    <section id="security" className="py-20 relative">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full">
            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(38,0,255,0.02)] to-[rgba(38,0,255,0.05)] border border-[rgba(38,0,255,0.15)] rounded-[18px] px-4 py-2 mb-4">
              <svg className="w-4 h-4 text-[#2600FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-[#2600FF] tracking-[-0.52px]">
                {t('badge')}
              </span>
            </div>
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
              <h2 id="security-heading">{t('title')}</h2>
            </div>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
              <p className="leading-[normal]">{t('subtitle')}</p>
            </div>
          </div>

          {/* Security Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-6 flex flex-col"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-[rgba(38,0,255,0.08)] to-[rgba(38,0,255,0.15)] rounded-[14px] flex items-center justify-center mb-4 text-[#2600FF]">
                  {feature.icon}
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-black tracking-[-0.72px] mb-2">
                  <p className="leading-[normal]">{feature.title}</p>
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] text-black tracking-[-0.56px]">
                  <p className="leading-[1.5]">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>

          {/* On-Premise Option Banner */}
          <div className="w-full bg-gradient-to-br from-[rgba(38,0,255,0.03)] to-[rgba(38,0,255,0.08)] border border-[rgba(38,0,255,0.12)] rounded-[25.5px] p-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-[#2600FF] to-[#1a00cc] rounded-[12px] flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
                    </svg>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[22px] text-black tracking-[-0.88px]">
                    {t('onPremiseTitle')}
                  </div>
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-50 text-[15px] text-black tracking-[-0.6px] max-w-[600px]">
                  <p className="leading-[1.6]">{t('onPremiseDesc')}</p>
                </div>
              </div>
              <a
                href="/#cta"
                className="bg-gradient-to-b from-[#4d4d4d] to-[#0a0a0a] border-none box-border cursor-pointer flex gap-2.5 items-center justify-center px-6 py-3 rounded-[36px] shrink-0 shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200"
              >
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-white tracking-[-0.6px] whitespace-nowrap">
                  {t('onPremiseCta')}
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Security;
