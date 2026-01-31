import React from 'react';

const Integrations: React.FC = () => {
  const integrationCategories = [
    {
      title: "Email & Communication",
      description: "Seamlessly connect with your existing email workflow",
      items: [
        { name: "Microsoft Outlook", description: "Auto-process purchase requests and approvals via email" },
        { name: "Gmail", description: "Smart email parsing for order management and vendor communication" }
      ]
    },
    {
      title: "ERP Systems",
      description: "Deep integration with your core business systems",
      items: [
        { name: "NetSuite", description: "Complete automation for purchase orders, inventory, and financial workflows" },
        { name: "Lemonsoft", description: "Streamlined operations for Nordic businesses with full system integration" }
      ]
    },
    {
      title: "AI Language Models",
      description: "Powered by industry-leading AI technology",
      items: [
        { name: "OpenAI GPT", description: "Advanced reasoning and natural language processing capabilities" },
        { name: "Google Gemini", description: "Multimodal AI for complex business logic and data analysis" },
        { name: "Anthropic Claude", description: "Reliable, ethical AI for sensitive business communications" }
      ]
    }
  ];

  return (
    <section id="integrations" className="py-20 relative bg-white">
      <div className="max-w-7xl mx-auto px-8">
        <div className="content-stretch flex flex-col gap-16 items-start justify-start relative">
          
          {/* Header Section */}
          <div className="content-stretch flex flex-col items-center justify-start w-full">
            <div className="font-['Inter:Regular',_sans-serif] font-normal leading-[normal] text-[40px] text-black tracking-[-1.6px] mb-4 text-center">
              <p>Integrations Tailored to Your Stack</p>
            </div>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[15px] text-black tracking-[-0.6px] text-center max-w-[700px]">
              <p className="leading-[normal]">Our AI agents are custom-built for your specific technology environment. Every integration is carefully configured to match your unique business processes and requirements.</p>
            </div>
          </div>

          {/* Integration Categories Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 w-full">
            {integrationCategories.map((category, categoryIndex) => (
              <div 
                key={categoryIndex}
                className="bg-[rgba(255,255,255,0.1)] overflow-clip rounded-[25.5px] border border-[rgba(0,0,0,0.08)] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.25)] p-8 h-full flex flex-col"
              >
                {/* Category Header */}
                <div className="mb-6">
                  <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-1px] mb-3">
                    <p className="leading-[normal]">{category.title}</p>
                  </h3>
                  <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-40 text-[14px] text-black tracking-[-0.56px] leading-[1.4]">
                    {category.description}
                  </p>
                </div>

                {/* Integration Items */}
                <div className="flex flex-col gap-6 flex-grow">
                  {category.items.map((item, itemIndex) => (
                    <div key={itemIndex} className="flex flex-col gap-2">
                      <div className="flex items-center gap-3">
                        {/* Integration Indicator */}
                        <div className="w-3 h-3 rounded-full bg-[#2600FF] flex-shrink-0"></div>
                        <h4 className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] text-black tracking-[-0.64px]">
                          {item.name}
                        </h4>
                      </div>
                      <p className="font-['Inter:Medium',_sans-serif] font-medium opacity-60 text-[13px] text-black tracking-[-0.52px] leading-[1.4] ml-6">
                        {item.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Integrations;
