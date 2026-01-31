import React from 'react';

const CaseStudy: React.FC = () => {
  return (
    <section id="case-study" className="py-20 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left Side - Content */}
          <div className="content-stretch flex flex-col gap-8 items-start justify-start">
            {/* Header */}
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[1.1] text-[36px] lg:text-[40px] text-black tracking-[-1.6px]">
              <p className="leading-[normal]">
                LVI-WaBeK managed to cut over 20K+ hours yearly only with ERP Agent's automations
              </p>
            </div>
            
            {/* Content Paragraphs */}
            <div className="space-y-6">
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  LVI-WaBeK, a leading building materials distributor, transformed their operations by implementing ERP Agent's intelligent automation system across their entire procurement and sales workflow.
                </p>
              </div>
              
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">Automated Purchase Orders:</strong> The system now handles 2000+ suppliers automatically, creating purchase orders based on sales velocity, inventory levels, and business rules - eliminating manual errors and saving 12+ hours daily.
                </p>
              </div>
              
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">Intelligent Quote Generation:</strong> Sales teams now generate complex quotes in minutes instead of hours. The agent identifies correct products, applies pricing rules, and creates professional offers directly in their ERP system.
                </p>
              </div>
              
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-70 text-[16px] text-black tracking-[-0.6px]">
                <p className="leading-[1.5]">
                  <strong className="opacity-100">Smart Warehouse Transfers:</strong> Daily stock transfers between locations happen automatically based on demand patterns and inventory optimization algorithms, reducing stockouts by 45%.
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
                  alt="LVI-WaBeK business operations" 
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
