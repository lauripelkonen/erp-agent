import { useEffect } from 'react';
import Footer from '../components/Footer';
import CTASection from '../components/CTASection';
import OrderMatrix from '../components/AlgorithmicArt/OrderMatrix';
import EmailToERPBridge from '../components/AlgorithmicArt/EmailToERPBridge';

export default function SalesQuoteSoftware() {
  useEffect(() => {
    document.title = 'Sales Quote Software | AI Quote Generation for Distributors | ERP Agent';
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', 'Generate professional sales quotes 10x faster with AI. Upload RFQs in any format, get accurate quotes with automatic product matching and pricing. Perfect for wholesale distributors.');
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff]">
      {/* Navigation */}
      <nav className="absolute left-1/2 max-w-7xl top-10 transform -translate-x-1/2 w-full px-8 z-50">
        <div className="flex items-center justify-between">
          <a href="/" className="h-8 relative shrink-0 hover:opacity-80 transition-opacity">
            <img className="block max-w-none h-full w-auto" src="/ERP-Agent-logo-black.png" alt="ERP Agent - Sales Quote Software" />
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
                  Sales Quote Software
                </span>
              </div>
              <h1 className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[32px] lg:text-[48px] text-black tracking-[-1.3px] lg:tracking-[-1.9px] mb-6">
                <span className="block opacity-40">AI-Powered</span>
                <span className="block">Sales Quote Generation Software</span>
              </h1>
              <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] lg:text-[17px] text-black tracking-[-0.6px] leading-[1.6] mb-8 max-w-[600px]">
                Turn customer RFQs into professional quotes in minutes, not hours. ERP Agent's AI reads any document format, matches products semantically, and applies your pricing rules automatically.
              </p>
              <div className="content-stretch flex gap-6 items-start justify-start">
                <a href="/#cta" className="bg-gradient-to-b border-none box-border content-stretch cursor-pointer flex from-[#4d4d4d] gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0 to-[#0a0a0a] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-center text-nowrap text-white tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">Generate Quotes Faster</p>
                  </div>
                </a>
                <a href="/#case-study" className="bg-[rgba(0,0,0,0.02)] border-none box-border content-stretch cursor-pointer flex gap-2.5 items-center justify-center px-6 py-3 relative rounded-[36px] shrink-0">
                  <div aria-hidden="true" className="absolute border border-[rgba(0,0,0,0.1)] border-solid inset-0 pointer-events-none rounded-[36px]" />
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[15px] text-[rgba(0,0,0,0.7)] text-center text-nowrap tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">See Demo</p>
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
          <div className="font-['Inter:Medium',_sans-serif] font-medium text-[64px] text-white tracking-[-2.5px] mb-2">10x</div>
          <div className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-white opacity-90 tracking-[-0.72px]">Faster Quote Turnaround Time</div>
        </div>
      </section>

      {/* How Quote Generation Works */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-8">
          <div className="content-stretch flex flex-col gap-12 items-start justify-start relative">
            <div className="content-stretch flex flex-col items-center justify-start w-full">
              <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
                <h2>From RFQ to Quote in Minutes</h2>
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[600px]">
                <p className="leading-[normal]">No more manual product lookups, price calculations, or document formatting. Let AI handle the heavy lifting.</p>
              </div>
            </div>

            {/* Algorithmic Art - Email to ERP Bridge */}
            <div className="w-full flex justify-center">
              <EmailToERPBridge className="w-full max-w-[500px] h-[250px]" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
              {[
                { number: 1, title: 'Upload Customer Request', description: 'Drop in an RFQ document - Excel, PDF, email, or any format. The AI extracts product requirements automatically.' },
                { number: 2, title: 'AI Matches Products', description: 'Semantic search finds the right products from your catalog, even when customer descriptions don\'t match exactly.' },
                { number: 3, title: 'Review & Send Quote', description: 'Get a formatted quote with customer-specific pricing. Review, adjust if needed, and send directly from your ERP.' }
              ].map((step) => (
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
                <h2>Smart Quote Generation Features</h2>
              </div>
            </div>

            <div className="space-y-8 w-full">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">Semantic Product Matching</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">Customers rarely use your exact product names. Our AI understands context and finds the right products even with vague descriptions, part numbers from competitors, or industry jargon.</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[13px] text-black tracking-[-0.52px] mb-2">
                      Example: Customer requests "24AWG Cat6 cable, blue, 100m"
                    </div>
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      AI finds: "CAT6-UTP-BL-100 - Category 6 Network Cable Blue 100m"
                    </div>
                  </div>
                </div>
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">Customer-Specific Pricing</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">Automatically apply contract pricing, volume discounts, and customer-specific price lists. No more looking up prices manually or making calculation errors.</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      Applies: Contract prices, Volume discounts, Currency conversion
                    </div>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
                <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-4">
                    <p className="leading-[normal]">Multi-Format Document Parsing</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">Accept RFQs in any format your customers send them. Excel spreadsheets, PDF files, email bodies, or even images of handwritten lists.</p>
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
                    <p className="leading-[normal]">Availability & Lead Time</p>
                  </div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] mb-6">
                    <p className="leading-[normal]">Real-time inventory checks and supplier lead time estimates included in every quote. Customers get accurate delivery information upfront.</p>
                  </div>
                  <div className="bg-[rgba(0,0,0,0.03)] rounded-[15px] p-4">
                    <div className="font-['Inter:Medium',_sans-serif] font-medium text-[13px] text-black tracking-[-0.52px]">
                      Shows: In-stock qty, Expected delivery, Alternative products
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
                <h2>Manual vs. AI-Powered Quoting</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full">
              {/* Traditional Process */}
              <div className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-6">
                  <p className="leading-[normal]">Traditional Process</p>
                </div>
                <div className="space-y-4">
                  {[
                    { step: '1.', text: 'Receive RFQ via email (5 min)' },
                    { step: '2.', text: 'Manually search each product (30-60 min)' },
                    { step: '3.', text: 'Look up customer pricing (15 min)' },
                    { step: '4.', text: 'Check inventory availability (10 min)' },
                    { step: '5.', text: 'Format and send quote (15 min)' }
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{item.step}</span>
                      <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">{item.text}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-6 border-t border-[rgba(0,0,0,0.1)]">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.3px]">1-2 hours</div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px]">per quote</div>
                </div>
              </div>

              {/* With ERP Agent */}
              <div className="bg-gradient-to-br from-[rgba(38,0,255,0.05)] to-[rgba(38,0,255,0.1)] overflow-clip rounded-[25.5px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(38,0,255,0.25)] p-8 border-2 border-[#2600FF]">
                <div className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-6">
                  <p className="leading-[normal]">With ERP Agent</p>
                </div>
                <div className="space-y-4">
                  {[
                    { step: '1.', text: 'Upload RFQ document (30 sec)' },
                    { step: '2.', text: 'AI matches all products (1 min)' },
                    { step: '3.', text: 'Customer pricing applied auto (instant)' },
                    { step: '4.', text: 'Live inventory check (instant)' },
                    { step: '5.', text: 'Review and approve (5 min)' }
                  ].map((item, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-[#2600FF] tracking-[-0.6px]">{item.step}</span>
                      <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">{item.text}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 pt-6 border-t border-[rgba(38,0,255,0.2)]">
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-[#2600FF] tracking-[-1.3px]">5-10 minutes</div>
                  <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px]">per quote</div>
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
