import WarehouseNetworkFlow from '../components/AlgorithmicArt/WarehouseNetworkFlow';
import DistributionPipeline from '../components/AlgorithmicArt/DistributionPipeline';
import POGenerationEngine from '../components/AlgorithmicArt/POGenerationEngine';
import SmartReorderTrigger from '../components/AlgorithmicArt/SmartReorderTrigger';
import DocumentExtractionFlow from '../components/AlgorithmicArt/DocumentExtractionFlow';
import EmailToERPBridge from '../components/AlgorithmicArt/EmailToERPBridge';

export default function ArtDemo() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#ededed] to-[#ffffff] py-20 px-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="font-['Inter:Regular',_sans-serif] text-[32px] text-black tracking-[-1.3px] mb-4 text-center">
          Algorithmic Art Demo
        </h1>
        <p className="font-['Inter:Medium',_sans-serif] text-[15px] text-black opacity-40 tracking-[-0.6px] mb-16 text-center">
          Scroll down to trigger animations. Pick the best ones for each page.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          {/* Wholesale Distribution ERP Options */}
          <div className="space-y-8">
            <h2 className="font-['Inter:Medium',_sans-serif] text-[20px] text-black tracking-[-0.8px] text-center border-b border-black/10 pb-4">
              For: Wholesale Distribution ERP
            </h2>

            {/* Option 1: Warehouse Network Flow */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                1. Warehouse Network Flow
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Shows multi-warehouse inventory optimization with packages flowing between locations
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <WarehouseNetworkFlow className="w-[300px] h-[280px]" />
              </div>
            </div>

            {/* Option 2: Distribution Pipeline */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                2. Distribution Pipeline
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Vertical supply chain: Suppliers → Warehouse → Customers (B2B & Retail)
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <DistributionPipeline className="w-[300px] h-[300px]" />
              </div>
            </div>
          </div>

          {/* Purchase Order Automation Options */}
          <div className="space-y-8">
            <h2 className="font-['Inter:Medium',_sans-serif] text-[20px] text-black tracking-[-0.8px] text-center border-b border-black/10 pb-4">
              For: Purchase Order Automation
            </h2>

            {/* Option 3: PO Generation Engine */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                3. PO Generation Engine
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Shows data inputs (inventory, sales, suppliers) feeding into AI to generate PO
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <POGenerationEngine className="w-[300px] h-[310px]" />
              </div>
            </div>

            {/* Option 4: Smart Reorder Trigger */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                4. Smart Reorder Trigger
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Inventory chart showing automatic PO trigger when stock hits reorder point
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <SmartReorderTrigger className="w-[300px] h-[280px]" />
              </div>
            </div>
          </div>
        </div>

        {/* Sales Quote Software Options */}
        <div className="mt-16">
          <h2 className="font-['Inter:Medium',_sans-serif] text-[20px] text-black tracking-[-0.8px] text-center border-b border-black/10 pb-4 mb-8">
            For: Sales Quote Software
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
            {/* Option 5: Document Extraction Flow */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                5. Document Extraction Flow
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Email with PDF/Excel attachments → AI funnel parser → Structured quote with 127 product lines
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <DocumentExtractionFlow className="w-[300px] h-[280px]" />
              </div>
            </div>

            {/* Option 6: Email to ERP Bridge */}
            <div className="bg-white rounded-[25px] shadow-[-1.5px_1.5px_22.2px_-9px_rgba(0,0,0,0.15)] p-8">
              <h3 className="font-['Inter:Medium',_sans-serif] text-[16px] text-black tracking-[-0.64px] mb-2">
                6. Email to ERP Bridge
              </h3>
              <p className="font-['Inter:Medium',_sans-serif] text-[13px] text-black opacity-40 tracking-[-0.52px] mb-6">
                Inbox with unread RFQs → Processing bridge (Parse → Match → Price) → ERP database
              </p>
              <div className="flex justify-center bg-[#f8f8f8] rounded-[15px] p-4">
                <EmailToERPBridge className="w-[300px] h-[280px]" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
