import React from 'react';

const Careers: React.FC = () => {
  const openRoles = [
    {
      title: "Founding Engineer",
      type: "Full-time • Equity",
      location: "Finland / Remote",
      description: "Join as our first engineering hire and help build the future of ERP automation. You'll work directly with the founder to architect scalable AI agent solutions.",
      requirements: [
        "3+ years of experience in Python/TypeScript",
        "Experience with AI/LLM integrations",
        "Background in enterprise software or ERP systems",
        "Passion for automation and AI agents"
      ]
    },
    {
      title: "AI Agent Developer",
      type: "Full-time • Remote",
      location: "Europe",
      description: "Develop and optimize AI agents that automate complex ERP workflows. You'll be working with cutting-edge LLM technology and enterprise integrations.",
      requirements: [
        "Experience with LLM APIs (OpenAI, Anthropic, etc.)",
        "Knowledge of workflow automation",
        "Understanding of ERP systems (NetSuite, SAP, etc.)",
        "Strong problem-solving skills"
      ]
    },
    {
      title: "Sales Engineer",
      type: "Full-time • Commission",
      location: "Finland / Remote",
      description: "Bridge the gap between our technical solution and customer needs. Help prospects understand the value of AI-powered ERP automation.",
      requirements: [
        "Experience in B2B SaaS sales",
        "Technical background or willingness to learn",
        "Understanding of ERP systems and business processes",
        "Excellent communication skills"
      ]
    },
    {
      title: "Customer Success Engineer",
      type: "Full-time • Remote",
      location: "Europe",
      description: "Ensure our clients get maximum value from their AI agent implementations. You'll work closely with customers to optimize their automated workflows.",
      requirements: [
        "Experience in customer-facing technical roles",
        "Knowledge of business process automation",
        "Strong analytical and problem-solving skills",
        "Passion for helping customers succeed"
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-8 py-20">
        
        {/* Header */}
        <div className="mb-16 text-center">
          <h1 className="font-['Inter:Regular',_sans-serif] font-normal text-[48px] text-black tracking-[-1.9px] mb-6">
            Join Our Mission
          </h1>
          <p className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-[#686E73] tracking-[-0.72px] leading-[1.5] max-w-2xl mx-auto mb-8">
            We're building the future of ERP automation with AI agents. Join our team of innovators and help transform how businesses operate.
          </p>
          
          {/* Company Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-lg mx-auto">
            <div className="text-center">
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-2">
                40K+
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#686E73] tracking-[-0.56px]">
                Hours Automated
              </div>
            </div>
            <div className="text-center">
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-2">
                100%
              </div>
              <div className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#686E73] tracking-[-0.56px]">
                Success Rate
              </div>
            </div>
          </div>
        </div>

        {/* Open Positions  */}
        <div className="mb-16">
          <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-8 text-center">
            Open Positions
          </h2>
          
          <div className="space-y-6">
            {openRoles.map((role, index) => (
              <div key={index} className="border border-[rgba(0,0,0,0.08)] rounded-[20px] p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between mb-4">
                  <div>
                    <h3 className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-0.96px] mb-2">
                      {role.title}
                    </h3>
                    <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#2600FF] tracking-[-0.56px]">
                        {role.type}
                      </span>
                      <span className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#686E73] tracking-[-0.56px]">
                        {role.location}
                      </span>
                    </div>
                  </div>
                </div>
                
                <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-[#686E73] tracking-[-0.6px] leading-[1.5] mb-4">
                  {role.description}
                </p>
                
                <div className="mb-4">
                  <h4 className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] text-black tracking-[-0.64px] mb-3">
                    What we're looking for:
                  </h4>
                  <ul className="space-y-2">
                    {role.requirements.map((req, reqIndex) => (
                      <li key={reqIndex} className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-[#2600FF] rounded-full mt-2 flex-shrink-0"></div>
                        <span className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#686E73] tracking-[-0.56px] leading-[1.4]">
                          {req}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Application CTA */}
        <div className="text-center bg-gradient-to-r from-[rgba(38,0,255,0.05)] to-[rgba(38,0,255,0.02)] border border-[rgba(38,0,255,0.1)] rounded-[25.5px] p-12">
          <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[28px] text-black tracking-[-1.12px] mb-4">
            Ready to Join Us?
          </h2>
          <p className="font-['Inter:Medium',_sans-serif] font-medium text-[16px] text-[#686E73] tracking-[-0.64px] leading-[1.5] mb-8 max-w-2xl mx-auto">
            We're always looking for talented individuals who are passionate about AI and automation. Even if you don't see a perfect match above, we'd love to hear from you.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5 text-[#2600FF]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span className="font-['Inter:Medium',_sans-serif] font-medium text-[18px] text-[#2600FF] tracking-[-0.72px]">
                lauri (at) erp-agent.com
              </span>
            </div>
            <p className="font-['Inter:Medium',_sans-serif] font-medium text-[14px] text-[#686E73] tracking-[-0.56px]">
              Send your CV and a brief note about why you're interested in ERP automation
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Careers;
