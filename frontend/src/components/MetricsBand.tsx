function MetricTile({ metric, description }: { metric: string; description: string }) {
  return (
    <div className="flex flex-col items-start justify-center gap-4">
      <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[normal] text-[40px] text-black tracking-[-1.6px]">
        <p className="leading-[normal]">{metric}</p>
      </div>
      <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[normal] opacity-40 text-[15px] text-black tracking-[-0.6px] w-[220px]">
        <p className="leading-[normal]">{description}</p>
      </div>
    </div>
  );
}

export default function MetricsBand() {
  return (
    <div className="bg-gradient-to-b from-[#ededed] to-[#ffffff] py-24 relative">
      <div className="absolute left-1/2 max-w-7xl transform -translate-x-1/2 w-full px-8">
        <div className="flex items-start justify-between w-full">
          <MetricTile 
            metric="50%" 
            description="Fewer purchasing hours" 
          />
          <MetricTile 
            metric="2×" 
            description="Faster quote/offer turnaround" 
          />
          <MetricTile 
            metric="<30" 
            description="Days to first deployment" 
          />
          <MetricTile 
            metric="99.9%" 
            description="Agent uptime" 
          />
        </div>
        
        <div className="mt-16 opacity-40">
          <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[normal] text-[13px] text-black tracking-[-0.52px] text-center max-w-4xl mx-auto">
            <p className="leading-[normal]">
              Results are based on early customer deployments and depend on SKU count, vendor base, approval thresholds, and data quality.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}