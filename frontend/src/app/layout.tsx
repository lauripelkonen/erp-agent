import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ERP Agent",
};

// Root layout - minimal wrapper
// The actual layout with providers is in [locale]/layout.tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
