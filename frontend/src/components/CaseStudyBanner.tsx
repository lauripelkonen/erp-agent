import React from 'react';

const CaseStudyBanner: React.FC = () => {
  const scrollToCaseStudy = () => {
    const caseStudyElement = document.getElementById('case-study');
    if (caseStudyElement) {
      caseStudyElement.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="py-16 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col lg:flex-row items-center justify-center lg:justify-between w-full max-w-4xl mx-auto">
          {/* Banner Content */}
          <div className="text-center lg:text-left mb-6 lg:mb-0">
            <div className="font-['Inter:Medium',_sans-serif] font-medium text-[28px] text-black tracking-[-1.2px]">
              <p className="leading-[normal]">Read about our customer use-case</p>
            </div>
          </div>
          
          {/* Button */}
          <button 
            onClick={scrollToCaseStudy}
            className="bg-gradient-to-b border-none box-border content-stretch cursor-pointer flex from-[#4d4d4d] gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0 to-[#0a0a0a] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200"
          >
            <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-center text-nowrap text-white tracking-[-0.6px] z-10">
              <p className="leading-[normal] whitespace-pre">Read Case Study</p>
            </div>
          </button>
        </div>
      </div>
    </section>
  );
};

export default CaseStudyBanner;
