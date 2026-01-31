import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import "../globals.css";
import { Providers } from "../providers";
import { Toaster } from "@/components/ui/toaster";
import { locales, type Locale } from "@/i18n/config";

const inter = Inter({ subsets: ["latin"] });

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export const metadata: Metadata = {
  metadataBase: new URL("https://erp-agent.com"),
  title: {
    default: "ERP Agent - Email to ERP in Seconds | AI Offer & Order Automation",
    template: "%s | ERP Agent",
  },
  description:
    "Transform complex offer and order requests from email to ERP in seconds. AI agents convert 100+ row wholesale orders that take sales reps hours into instant ERP entries. 40K+ hours saved yearly.",
  keywords: [
    "ERP automation",
    "AI order processing",
    "email to ERP",
    "offer automation",
    "wholesale order automation",
    "sales quote automation",
    "purchase order automation",
    "AI agents for ERP",
    "wholesale distribution ERP",
    "B2B order processing",
    "RFQ automation",
    "sales order automation",
  ],
  authors: [{ name: "ERP Agent" }],
  creator: "ERP Agent",
  publisher: "ERP Agent",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://erp-agent.com",
    siteName: "ERP Agent",
    title: "ERP Agent - Email to ERP in Seconds | AI Offer & Order Automation",
    description:
      "Transform complex offer and order requests from email to ERP in seconds. AI agents convert 100+ row wholesale orders that take sales reps hours into instant ERP entries.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "ERP Agent - AI-Powered Offer and Order Automation",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "ERP Agent - Email to ERP in Seconds",
    description:
      "AI agents convert complex wholesale offers & orders from email to ERP in seconds. What takes sales reps hours, we do instantly.",
    images: ["/og-image.png"],
    creator: "@erp_agent",
  },
  alternates: {
    canonical: "https://erp-agent.com",
    languages: {
      "en-US": "https://erp-agent.com",
      "fi-FI": "https://erp-agent.com/fi",
      "sv-SE": "https://erp-agent.com/sv",
      "de-DE": "https://erp-agent.com/de",
    },
  },
  verification: {
    google: "nR3azBOFak9xM-NU_uoOfpcLQ4qC9egL3L_u2YR-eGg",
  },
  category: "Business Software",
};

// JSON-LD Structured Data
const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "ERP Agent",
  url: "https://erp-agent.com",
  logo: "https://erp-agent.com/ERP-Agent-logo-black.png",
  description:
    "AI-powered offer and order automation for wholesale distributors. Transform email requests into ERP entries in seconds.",
  contactPoint: {
    "@type": "ContactPoint",
    contactType: "sales",
    email: "contact@erp-agent.com",
  },
  sameAs: ["https://www.linkedin.com/company/erp-agent"],
};

const softwareSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "ERP Agent",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web-based",
  description:
    "AI agents that convert complex offer and order requests from email to ERP in seconds. Handles 100+ row wholesale orders instantly - what takes sales reps hours.",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "EUR",
    description: "Free consultation and demo available",
  },
  aggregateRating: {
    "@type": "AggregateRating",
    ratingValue: "4.9",
    ratingCount: "50",
    bestRating: "5",
  },
  featureList: [
    "Email to ERP conversion in seconds",
    "100+ row order processing",
    "Semantic product matching",
    "Customer-specific pricing",
    "Multi-format document parsing (Excel, PDF, email)",
    "Real-time inventory checking",
    "ERP integrations (Lemonsoft, NetSuite, SAP)",
  ],
};

const faqSchema = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "How does ERP Agent convert emails to ERP orders?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "ERP Agent uses AI to read offer/order requests from emails, Excel files, or PDFs. It semantically matches products to your catalog, applies customer-specific pricing, checks inventory, and creates the order in your ERP - all in seconds instead of hours.",
      },
    },
    {
      "@type": "Question",
      name: "How long does it take to process a complex wholesale order?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "What typically takes a sales rep 1-2 hours for a 100+ row order, ERP Agent completes in seconds. The AI handles product matching, pricing, and ERP entry automatically.",
      },
    },
    {
      "@type": "Question",
      name: "Which ERP systems does ERP Agent integrate with?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "ERP Agent integrates with leading wholesale distribution ERPs including Lemonsoft, NetSuite, SAP Business One, Microsoft Dynamics, and custom ERP systems via API.",
      },
    },
    {
      "@type": "Question",
      name: "How accurate is the AI product matching?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Our semantic AI matches products even when customer descriptions don't match your catalog exactly. It understands industry jargon, competitor part numbers, and vague descriptions to find the correct products.",
      },
    },
  ],
};

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Validate that the incoming locale is valid
  if (!locales.includes(locale as Locale)) {
    notFound();
  }

  // Enable static rendering
  setRequestLocale(locale);

  // Fetch messages for the locale
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(organizationSchema),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(softwareSchema),
          }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(faqSchema),
          }}
        />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <NextIntlClientProvider messages={messages}>
          <Providers>
            {children}
            <Toaster />
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
