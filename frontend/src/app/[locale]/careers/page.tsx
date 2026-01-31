"use client";

import Careers from "@/components/Careers";
import Footer from "@/components/Footer";

export default function CareersPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1">
        <Careers />
      </div>
      <Footer />
    </div>
  );
}
