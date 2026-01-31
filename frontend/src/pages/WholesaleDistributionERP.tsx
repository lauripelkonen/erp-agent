import { useEffect } from 'react';
import Footer from '../components/Footer';
import CTASection from '../components/CTASection';
import WarehouseNetworkFlow from '../components/AlgorithmicArt/WarehouseNetworkFlow';

export default function WholesaleDistributionERP() {
  useEffect(() => {
    document.title = 'Wholesale Distribution ERP Software | AI-Powered Automation | ERP Agent';
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'Transform your wholesale distribution operations with AI-powered ERP automation. Automate purchase orders, inventory management, and supplier communications. Save 40K+ hours yearly.');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff]">
      {/* Navigation */}
      <nav className="absolute left-1/2 max-w-7xl top-10 transform -translate-x-1/2 w-full px-8 z-50">
        <div className="flex items-center justify-between">
          <a href="/" className="h-8 relative shrink-0 hover:opacity-80 transition-opacity">
            <img className="block max-w-none h-full w-auto" src="/ERP-Agent-logo-black.png" alt="ERP Agent - Wholesale Distribution ERP Software" />
          </a>
          <a href="/#cta" className="bg-black box-border content-stretch flex gap-2.5 items-center justify-center px-4 py-1.5 relative rounded-[36px] shrink-0 border-none cursor-pointer hover:bg-gray-800 transition-colors">
            <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[13px] text-center text-nowrap text-white tracking-[-0.52px]">
              <p className="leading-[normal] whitespace-pre">Get Started</p>
            </div>
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 mb-6">
                <div className="w-2 h-2 bg-[#2600FF] rounded-full"></div>
                <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                  Wholesale Distribution ERP
                </span>
              </div>
              <h1 className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[32px] lg:text-[48px] text-black tracking-[-1.3px] lg:tracking-[-1.9px] mb-6">
                <span className="block opacity-40">AI-Powered</span>
                <span className="block">Wholesale Distribution ERP Software</span>
              </h1>
              <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] lg:text-[17px] text-black tracking-[-0.6px] leading-[1.6] mb-8 max-w-[600px]">
                Automate your wholesale distribution operations with intelligent AI agents. From purchase order automation to inventory optimization, ERP Agent transforms how distributors manage their ERP systems.
              </p>
              <div className="content-stretch flex gap-6 items-start justify-start">
                <a href="/#cta" className="bg-gradient-to-b border-none box-border content-stretch cursor-pointer flex from-[#4d4d4d] gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0 to-[#0a0a0a] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-center text-nowrap text-white tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">Request Demo</p>
                  </div>
                </a>
                <a href="/#case-study" className="bg-[rgba(0,0,0,0.02)] border-none box-border content-stretch cursor-pointer flex gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0">
                  <div aria-hidden="true" className="absolute border border-[rgba(0,0,0,0.1)] border-solid inset-0 pointer-events-none rounded-[36px]" />
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-[rgba(0,0,0,0.7)] text-center text-nowrap tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">View Case Study</p>
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
                <h2>Why Distributors Choose ERP Agent</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  40K+
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  Hours Saved Yearly
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">Automate repetitive ERP tasks like purchase order creation, product matching, and supplier communication.</p>
                </div>
              </div>
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  10x
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  Faster Quote Turnaround
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">Generate accurate sales quotes in minutes instead of hours with AI-powered product matching and pricing.</p>
                </div>
              </div>
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[40px] text-black tracking-[-1.6px] mb-2">
                  50%
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] mb-4">
                  Reduction in Manual Work
                </div>
                <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                  <p className="leading-[normal]">Cut purchasing and order processing time in half with intelligent automation tailored to your workflows.</p>
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
                <h2>Built for Wholesale Distributors</h2>
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
                <p className="leading-[normal]">ERP Agent understands the unique challenges of wholesale distribution - from managing thousands of SKUs to coordinating with multiple suppliers.</p>
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
                        <p className="leading-[normal]">Purchase Order Automation</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">AI agents analyze sales velocity, inventory levels, and supplier lead times to automatically generate optimized purchase orders. Set your business rules and let the AI handle the rest.</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Intelligent reorder points</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Order value optimization</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">Sales Quote Generation</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">Upload customer RFQs in any format and get accurate quotes generated automatically. The AI matches products, applies customer-specific pricing, and formats professional quotes.</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Excel, PDF, email parsing</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Semantic product matching</span>
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
                        <p className="leading-[normal]">Warehouse Transfer Management</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">Optimize inventory across multiple warehouse locations. AI analyzes demand patterns and stock levels to suggest and execute inter-warehouse transfers.</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Multi-location optimization</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Demand-based transfers</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="lg:col-span-3 flex">
                  <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 flex flex-col relative w-full">
                    <div className="mb-8">
                      <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                        <p className="leading-[normal]">ERP Analytics & Insights</p>
                      </div>
                      <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">
                        <p className="leading-[normal]">Get real-time visibility into your distribution operations. AI-powered analytics surface actionable insights from your ERP data.</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Sales trend analysis</span>
                      </div>
                      <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[rgba(0,0,0,0.02)] to-[rgba(0,0,0,0.05)] border border-[rgba(0,0,0,0.08)] rounded-[18px] px-4 py-2 ml-2">
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">Supplier performance</span>
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
            <h2>Works With Your ERP System</h2>
          </div>
          <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-8 max-w-[600px] mx-auto">
            <p className="leading-[normal]">ERP Agent integrates with leading wholesale distribution ERP systems including Lemonsoft, NetSuite, SAP Business One, Microsoft Dynamics, and more.</p>
          </div>
          <a href="/#integrations" className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-[#2600FF] tracking-[-0.6px] hover:opacity-80 transition-opacity">
            View All Integrations &rarr;
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
