import React from 'react';

const PrivacyPolicy: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-8 py-20">
        <div className="prose prose-lg max-w-none">
          
          {/* Header */}
          <div className="mb-12 text-center">
            <h1 className="font-['Inter:Regular',_sans-serif] font-normal text-[48px] text-black tracking-[-1.9px] mb-4">
              Privacy Policy
            </h1>
            <div className="font-['Inter:Medium',_sans-serif] font-medium opacity-60 text-[16px] text-black tracking-[-0.64px]">
              <p className="leading-[normal]">Last updated 28.03.2025</p>
            </div>
          </div>

          {/* Introduction */}
          <div className="mb-12">
            <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] space-y-4">
              <p>DataFigured Oy ("we," "us," or "our") respects your privacy and is committed to protecting your personal data. This privacy notice outlines how we collect, process, and share your personal data and informs you about your privacy rights.</p>
              
              <p>As a registered company, DataFigured Oy is fully committed to operating under GDPR compliance and takes full responsibility for protecting your privacy and data.</p>
              
              <p>This Privacy Notice applies to our web application, which provides search functionality powered by language models (LLMs) through third-party service providers. While your personal data is securely stored within the EU, some of the query data you submit may be processed outside the EU, including in the United States, by our LLM service providers.</p>
            </div>
          </div>

          {/* Table of Contents */}
          <div className="mb-12 bg-[rgba(0,0,0,0.02)] border border-[rgba(0,0,0,0.08)] rounded-[25.5px] p-8">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[24px] text-black tracking-[-0.96px] mb-4">
              Contents of this Privacy Notice
            </h2>
            <div className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.8]">
              <ol className="list-decimal ml-6 space-y-1">
                <li>Who is the Data Controller?</li>
                <li>Information We Collect and How We Collect It</li>
                <li>The Purposes and the Lawful Basis for Processing</li>
                <li>Sharing of Information</li>
                <li>Data Transfers to Third Countries</li>
                <li>Data Retention</li>
                <li>How to Exercise Your Data Protection Rights</li>
                <li>Changes to this Privacy Notice</li>
              </ol>
            </div>
          </div>

          {/* Section 1 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              1. Who is the Data Controller?
            </h2>
            
            <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
              DataFigured Oy is the official data controller for this application. If you have questions regarding this privacy notice, please contact us by email at <a href="mailto:info@datafigured.com" className="text-[#2600FF] hover:opacity-80">info@datafigured.com</a>.
            </p>
          </section>

          {/* Section 2 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              2. Information We Collect and How We Collect It
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                We may collect, use, store, and transfer different types of personal and query data, which we categorize as follows:
              </p>
              
              <ul className="list-disc ml-6 space-y-2 font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                <li><strong>Personal Identification Information:</strong> Full name.</li>
                <li><strong>Contact Data:</strong> Email address.</li>
                <li><strong>Technical Data:</strong> IP address, login data, browser type and version, time zone, and other technical details about your device.</li>
                <li><strong>Usage Data:</strong> How you interact with the app, including query submissions.</li>
                <li><strong>Communication Data:</strong> Any messages or interactions with our support team.</li>
              </ul>
              
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                Information is collected directly from you when you use the Service.
              </p>
            </div>
          </section>

          {/* Section 3 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              3. The Purposes and the Lawful Basis for Processing
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                We will only process your data when allowed by law. Our processing bases include:
              </p>
              
              <ul className="list-disc ml-6 space-y-2 font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                <li><strong>Legitimate Interest:</strong> We process data to understand and improve the service, enhance user experience, monitor performance, and ensure security.</li>
                <li><strong>Consent:</strong> In cases where explicit consent is required, such as the use of cookies (other than strictly necessary technical cookies), we will seek your consent.</li>
              </ul>
            </div>
          </section>

          {/* Section 4 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              4. Sharing of Information
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                We may share your data with:
              </p>
              
              <ul className="list-disc ml-6 space-y-2 font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                <li><strong>Third-Party Service Providers:</strong> To provide our search functionality, we work with third-party providers who offer LLM capabilities and may process query data submitted through the app. These providers may process data in the United States and other locations outside the EU.</li>
                <li><strong>Legal Obligations:</strong> We may disclose data when required by law or to protect rights, safety, or to comply with legal claims.</li>
              </ul>
              
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                All third parties that process data on our behalf are bound by data processing agreements to comply with GDPR and protect your privacy.
              </p>
            </div>
          </section>

          {/* Section 5 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              5. Data Transfers to Third Countries
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                Your personal data is securely stored within the EU. However, the query data you submit may be transferred outside the EU, including to the United States, where some of our third-party LLM providers operate. We ensure that all necessary safeguards are in place, such as Standard Contractual Clauses (SCCs), to protect your query data when transferred outside the EU.
              </p>
              
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                If you would like more information on the safety measures in place for data transfers outside the EU, please contact us by email at <a href="mailto:info@datafigured.com" className="text-[#2600FF] hover:opacity-80">info@datafigured.com</a>.
              </p>
            </div>
          </section>

          {/* Section 6 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              6. Data Retention
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                We retain personal data only as long as necessary to fulfill the purposes outlined in Section 3. If you stop using the Service, we will either delete or anonymize your personal data after:
              </p>
              
              <ul className="list-disc ml-6 space-y-2 font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                <li><strong>Personal Identification and Contact Data:</strong> 12 months</li>
                <li><strong>Technical and Usage Data:</strong> 12 months</li>
                <li><strong>Communication Data:</strong> 12 months</li>
              </ul>
              
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                Data may be retained longer if legally required or if necessary for legal claims.
              </p>
            </div>
          </section>

          {/* Section 7 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              7. How to Exercise Your Data Protection Rights
            </h2>
            
            <div className="space-y-4">
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                You have certain rights under GDPR, including:
              </p>
              
              <ul className="list-disc ml-6 space-y-2 font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                <li><strong>Access:</strong> Request a copy of your data.</li>
                <li><strong>Correction:</strong> Correct inaccurate or incomplete data.</li>
                <li><strong>Erasure:</strong> Request deletion of your data when appropriate.</li>
                <li><strong>Objection:</strong> Object to processing based on legitimate interest.</li>
                <li><strong>Restriction:</strong> Temporarily limit processing of your data.</li>
                <li><strong>Data Portability:</strong> Transfer your data to another party.</li>
                <li><strong>Withdraw Consent:</strong> Revoke consent for specific processing activities.</li>
              </ul>
              
              <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
                To exercise any of these rights, contact us at <a href="mailto:info@datafigured.com" className="text-[#2600FF] hover:opacity-80">info@datafigured.com</a>. We will respond in accordance with GDPR and applicable laws. You may also contact your local data protection authority with any concerns.
              </p>
            </div>
          </section>

          {/* Section 8 */}
          <section className="space-y-6 mb-12">
            <h2 className="font-['Inter:Medium',_sans-serif] font-medium text-[32px] text-black tracking-[-1.28px] mb-4">
              8. Changes to this Privacy Notice
            </h2>
            
            <p className="font-['Inter:Medium',_sans-serif] font-medium text-[15px] text-black tracking-[-0.6px] leading-[1.6] opacity-80">
              We may update this Privacy Notice periodically to reflect changes in legal requirements or operational needs. We encourage you to review this notice regularly on our website to stay informed about our data privacy practices.
            </p>
          </section>

        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
