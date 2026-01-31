"use client";

import TermsOfService from "@/components/TermsOfService";
import Footer from "@/components/Footer";

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1">
        <TermsOfService />
      </div>
      <Footer />
    </div>
  );
}
