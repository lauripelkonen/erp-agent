"use client";

import { useEffect } from "react";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Bento from "@/components/Bento";
import Pricing from "@/components/Pricing";
import Integrations from "@/components/Integrations";
import CaseStudyBanner from "@/components/CaseStudyBanner";
import CaseStudy from "@/components/CaseStudy";
import Testimonials from "@/components/Testimonials";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";
import CookieConsent from "@/components/CookieConsent";
import { cookieManager } from "@/utils/cookieManager";

export default function LandingPage() {
  useEffect(() => {
    cookieManager.initialize();
  }, []);

  const handleCookieAccept = () => {
    cookieManager.acceptAll();
  };

  const handleCookieDeny = () => {
    cookieManager.denyAll();
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <header>
        <Hero />
      </header>

      {/* Main Content */}
      <main>
        {/* Case Study Banner */}
        <section id="case-study-banner">
          <CaseStudyBanner />
        </section>

        {/* Features/Bento Grid */}
        <section id="features" aria-labelledby="features-heading">
          <Bento />
        </section>

        {/* Integrations */}
        <section id="integrations" aria-labelledby="integrations-heading">
          <Integrations />
        </section>

        {/* How It Works */}
        <section id="how-it-works" aria-labelledby="how-it-works-heading">
          <HowItWorks />
        </section>

        {/* Testimonials */}
        <section id="testimonials" aria-labelledby="testimonials-heading">
          <Testimonials />
        </section>

        {/* Case Study */}
        <section id="case-study" aria-labelledby="case-study-heading">
          <CaseStudy />
        </section>

        {/* Pricing */}
        <section id="pricing" aria-labelledby="pricing-heading">
          <Pricing />
        </section>

        {/* Call to Action */}
        <section id="cta" aria-labelledby="cta-heading">
          <CTASection />
        </section>
      </main>

      {/* Footer */}
      <footer>
        <Footer />
      </footer>

      {/* Cookie Consent */}
      <CookieConsent
        onAccept={handleCookieAccept}
        onDeny={handleCookieDeny}
      />
    </div>
  );
}
