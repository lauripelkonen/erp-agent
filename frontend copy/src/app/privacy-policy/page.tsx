"use client";

import PrivacyPolicy from "@/components/PrivacyPolicy";
import Footer from "@/components/Footer";

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1">
        <PrivacyPolicy />
      </div>
      <Footer />
    </div>
  );
}
