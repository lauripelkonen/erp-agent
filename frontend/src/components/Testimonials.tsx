'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

interface TestimonialCardProps {
  role: string;
  content: string;
  rating: number;
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-2 items-center">
      {Array.from({ length: 5 }, (_, i) => (
        <div
          key={i}
          className="w-4 h-4 relative"
        >
          <svg
            viewBox="0 0 24 24"
            fill={i < rating ? "#FFFFFF" : "rgba(255,255,255,0.3)"}
            className="w-full h-full"
          >
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </div>
      ))}
    </div>
  );
}

function TestimonialCard({ role, content, rating }: TestimonialCardProps) {
  return (
    <div className="relative bg-gradient-to-b from-[rgba(0,0,0,0.8)] to-[rgba(0,0,0,0.9)] border border-[rgba(255,255,255,0.1)] rounded-[22px] p-11 backdrop-blur-[89px] shadow-[inset_0px_0px_33px_0px_rgba(255,255,255,0.05)]">
      {/* Stars */}
      <div className="mb-11">
        <StarRating rating={rating} />
      </div>
      
      {/* Content */}
      <div className="mb-11">
        <p className="font-['Poppins'] font-light text-[15.5px] leading-[1.3] text-[#7D7E81]">
          {content}
        </p>
      </div>
      
      {/* Author Details */}
      <div className="flex items-center">
        <div className="font-['Poppins'] font-normal text-[15.5px] leading-[1.3] text-white">
          {role}
        </div>
      </div>
    </div>
  );
}



export default function Testimonials() {
  const t = useTranslations('testimonials');

  const testimonials = [
    {
      role: t('purchaserRole'),
      content: t('purchaserContent'),
      rating: 5
    },
    {
      role: t('ceoRole'),
      content: t('ceoContent'),
      rating: 5
    },
    {
      role: t('salesRole'),
      content: t('salesContent'),
      rating: 5
    }
  ];

  return (
    <section className="py-20 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
          
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full relative z-10">

            {/* Main Title */}
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
              <p>{t('title')}</p>
            </div>

            {/* Subtitle */}
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
              <p className="leading-[normal]">{t('subtitle')}</p>
            </div>
          </div>
          
          {/* Testimonials Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full relative z-10">
            {/* Single Row with 3 testimonials */}
            <TestimonialCard {...testimonials[0]} />
            <TestimonialCard {...testimonials[1]} />
            <TestimonialCard {...testimonials[2]} />
          </div>
        </div>
      </div>
    </section>
  );
}
