import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="relative bg-white overflow-hidden">
      <div className="max-w-7xl mx-auto px-8 relative py-20">
        
        {/* Main Content Container */}
        <div className="relative bg-white border border-[#E6E6E6] rounded-[36px] p-16 shadow-[0px_17px_37px_0px_rgba(0,0,0,0.04),0px_66px_66px_0px_rgba(0,0,0,0.03),0px_266px_106px_0px_rgba(0,0,0,0.01)] z-10 mb-8">
          
          {/* ERP Agent Logo */}
          <div className="mb-12">
            <a href="/" className="inline-block hover:opacity-80 transition-opacity">
              <img 
                src="/ERP-Agent-logo-black.png" 
                alt="ERP Agent" 
                className="h-8 w-auto"
              />
            </a>
          </div>
          
          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
            
            {/* Left Side - Description & Sales Contact */}
            <div className="max-w-md">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] mb-8">
                ERP Agent helps teams automate complex business processes with AI-powered agents — everything you need for intelligent automation in one place
              </p>
              
              {/* Sales Contact */}
              <div>
                <h4 className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-black mb-3">
                  Sales Inquiries
                </h4>
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-[#686E73]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <span className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] leading-[1.4em] tracking-[-0.56px] text-[#686E73]">
                    sales (at) datafigured.com
                  </span>
                </div>
              </div>
            </div>
            
            {/* Right Side - Navigation Links */}
            <div className="flex gap-16 justify-start">
              
              {/* Product Column */}
              <div>
                <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] leading-[1.4em] tracking-[-0.6px] text-black mb-6">
                  Product
                </h3>
                <div className="flex flex-col gap-[14px]">
                  <a href="/#features" className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                    Features
                  </a>
                  <a href="/#integrations" className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                    Integrations
                  </a>
                </div>
              </div>
              
              {/* Company Column */}
              <div>
                <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] leading-[1.4em] tracking-[-0.6px] text-black mb-6">
                  Company
                </h3>
                <div className="flex flex-col gap-[14px]">
                  <a href="/" className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                    About
                  </a>
                  <a href="/careers" className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                    Careers
                  </a>
                </div>
              </div>
            </div>
          </div>
          
          {/* Divider Line */}
          <div className="w-full h-0 border-t border-[#F0F0F0] shadow-[0px_0.25px_0px_0px_rgba(0,0,0,0.07)] mb-8"></div>
          
          {/* Bottom Footer Links */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex flex-col md:flex-row items-center gap-4">
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] leading-[1.4em] tracking-[-0.6px] text-[#686E73]">
                © 2025 DataFigured Oy. All rights reserved
              </div>
              
              {/* Social Links */}
              <div className="flex items-center gap-3">
                <span className="font-['Inter:Medium',_sans-serif] font-medium text-[12px] leading-[1.4em] tracking-[-0.48px] text-[#686E73]">
                  Follow us:
                </span>
                <a 
                  href="https://www.linkedin.com/company/erp-agent" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center justify-center w-8 h-8 rounded-full bg-[#686E73] hover:bg-[#0077B5] transition-colors group"
                  aria-label="Follow ERP Agent on LinkedIn"
                >
                  <svg 
                    className="w-4 h-4 text-white" 
                    fill="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
              </div>
            </div>
            
            <div className="flex gap-6">
              <a href="/terms-of-service" className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                Terms of Service
              </a>
              <a href="/privacy-policy" className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] leading-[1.4em] tracking-[-0.6px] text-[#686E73] hover:text-black transition-colors">
                Privacy Policy
              </a>
            </div>
          </div>
        </div>
      </div>
      
      {/* Large Background ERP Agent Text */}
      <div className="relative w-full h-[120px] sm:h-[160px] md:h-[200px] lg:h-[240px] bg-white overflow-hidden">
        <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full flex justify-center">
          <h1 className="font-['PP_Mondwest'] font-normal text-[80px] sm:text-[120px] md:text-[200px] lg:text-[280px] xl:text-[310px] leading-[1em] text-[#EAECEB] text-center whitespace-nowrap">
            ERP Agent
          </h1>
        </div>
        
        {/* White gradient overlay */}
        <div className="absolute bottom-0 left-0 w-full h-[60px] sm:h-[80px] md:h-[100px] lg:h-[120px] bg-gradient-to-t from-white via-white/80 to-transparent pointer-events-none"></div>
      </div>
    </footer>
  );
};

export default Footer;
