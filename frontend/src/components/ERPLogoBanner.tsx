'use client';

import React from 'react';
import { useTranslations } from 'next-intl';

interface ERPLogo {
  name: string;
  logo: string | null; // null means text-only
  width?: number;
}

const erpLogos: ERPLogo[] = [
  { name: 'SAP', logo: '/erp-logos/sap.svg', width: 80 },
  { name: 'Oracle NetSuite', logo: '/figma/image-583129.png', width: 120 },
  { name: 'Microsoft Dynamics', logo: '/erp-logos/dynamics.svg', width: 100 },
  { name: 'Sage', logo: null },
  { name: 'Odoo', logo: '/erp-logos/odoo.png', width: 80 },
  { name: 'Lemonsoft', logo: null },
  { name: 'Visma', logo: '/erp-logos/visma.svg', width: 100 },
  { name: 'Jeeves', logo: null },
];

const ERPLogoBanner: React.FC = () => {
  const t = useTranslations('erpBanner');
  // Duplicate logos for seamless infinite scroll
  const duplicatedLogos = [...erpLogos, ...erpLogos];

  return (
    <section className="py-12 bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-8 mb-8">
        <div className="text-center">
          <p className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-black/40 tracking-[-0.56px] uppercase">
            {t('title')}
          </p>
        </div>
      </div>

      {/* Scrolling container */}
      <div className="relative">
        {/* Gradient fade on left */}
        <div className="absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />

        {/* Gradient fade on right */}
        <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />

        {/* Scrolling track */}
        <div className="flex animate-scroll-logos">
          {duplicatedLogos.map((erp, index) => (
            <div
              key={`${erp.name}-${index}`}
              className="flex-shrink-0 flex items-center justify-center px-8 md:px-12 group"
            >
              {erp.logo ? (
                <img
                  src={erp.logo}
                  alt={erp.name}
                  className="h-8 md:h-10 w-auto object-contain grayscale opacity-40 group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-300"
                  style={{ width: erp.width ? `${erp.width}px` : 'auto' }}
                />
              ) : (
                <span className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] md:text-[18px] text-black/30 group-hover:text-black/70 transition-colors duration-300 whitespace-nowrap">
                  {erp.name}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Add keyframe animation via style tag */}
      <style jsx>{`
        @keyframes scroll-logos {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .animate-scroll-logos {
          animation: scroll-logos 30s linear infinite;
        }
        .animate-scroll-logos:hover {
          animation-play-state: paused;
        }
        @media (max-width: 768px) {
          .animate-scroll-logos {
            animation-duration: 20s;
          }
        }
      `}</style>
    </section>
  );
};

export default ERPLogoBanner;
