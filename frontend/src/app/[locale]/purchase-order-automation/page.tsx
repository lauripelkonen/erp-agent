import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Purchase Order Automation Software | AI-Powered PO Generation",
  description:
    "Automate purchase order creation with AI. Intelligent PO generation based on sales velocity, inventory levels, and supplier data. Save 20K+ hours yearly on purchasing.",
  keywords: [
    "purchase order automation",
    "PO automation software",
    "AI purchase orders",
    "automated purchasing",
    "procurement automation",
    "wholesale PO software",
  ],
  openGraph: {
    title: "Purchase Order Automation Software | AI-Powered PO Generation",
    description:
      "AI generates optimized purchase orders based on sales velocity, inventory, and supplier data. 50% faster PO processing.",
    url: "https://erp-agent.com/purchase-order-automation",
  },
  twitter: {
    card: "summary_large_image",
    title: "Purchase Order Automation - AI-Powered PO Generation",
    description:
      "AI generates optimized purchase orders automatically. 50% reduction in PO processing time.",
  },
  alternates: {
    canonical: "https://erp-agent.com/purchase-order-automation",
  },
};

export { default } from "@/page-components/PurchaseOrderAutomation";
