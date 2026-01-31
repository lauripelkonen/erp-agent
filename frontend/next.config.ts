import type { NextConfig } from "next";
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

const nextConfig: NextConfig = {
  // Enable standalone output for optimized Vercel deployment
  output: "standalone",

  // Environment variables that will be available on client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // Redirects from old PascalCase URLs to new kebab-case URLs (SEO)
  async redirects() {
    return [
      {
        source: "/WholesaleDistributionERP",
        destination: "/wholesale-distribution-erp",
        permanent: true,
      },
      {
        source: "/SalesQuoteSoftware",
        destination: "/sales-quote-software",
        permanent: true,
      },
      {
        source: "/PurchaseOrderAutomation",
        destination: "/purchase-order-automation",
        permanent: true,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
