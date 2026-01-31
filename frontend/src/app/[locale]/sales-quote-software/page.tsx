import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sales Quote Software | AI Offer Generation for Wholesale",
  description:
    "Generate sales quotes 10x faster with AI. Convert 100+ row customer RFQs to professional offers in seconds. Semantic product matching, customer pricing, ERP integration.",
  keywords: [
    "sales quote software",
    "quote generation software",
    "AI offer generation",
    "RFQ automation",
    "wholesale quote software",
    "B2B quote automation",
  ],
  openGraph: {
    title: "Sales Quote Software | AI Offer Generation for Wholesale",
    description:
      "Convert 100+ row RFQs to professional offers in seconds. AI handles product matching and customer pricing automatically.",
    url: "https://erp-agent.com/sales-quote-software",
  },
  twitter: {
    card: "summary_large_image",
    title: "Sales Quote Software - RFQ to Offer in Seconds",
    description:
      "AI converts complex RFQs with 100+ products to professional offers instantly.",
  },
  alternates: {
    canonical: "https://erp-agent.com/sales-quote-software",
  },
};

export { default } from "@/page-components/SalesQuoteSoftware";
