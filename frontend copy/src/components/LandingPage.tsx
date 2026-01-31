import Hero from './Hero';
import HowItWorks from './HowItWorks';
import Bento from './Bento';
import Pricing from './Pricing';
import Integrations from './Integrations';
import CaseStudyBanner from './CaseStudyBanner';
import CaseStudy from './CaseStudy';
import Testimonials from './Testimonials';
import CTASection from './CTASection';
import Footer from './Footer';
import CookieConsent from './CookieConsent';
import { cookieManager } from '../utils/cookieManager';

export default function LandingPage() {
  const handleCookieAccept = () => {
    cookieManager.acceptAll();
  };

  const handleCookieDeny = () => {
    cookieManager.denyAll();
  };

  return (
    <>
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
    </>
  );
}
