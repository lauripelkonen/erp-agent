import React, { useState, useEffect } from 'react';
import { X, Cookie } from 'lucide-react';

interface CookieConsentProps {
  onAccept?: () => void;
  onDeny?: () => void;
}

export default function CookieConsent({ onAccept, onDeny }: CookieConsentProps) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookie-consent');
    if (!consent) {
      const timer = setTimeout(() => {
        setIsVisible(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookie-consent', 'accepted');
    setIsVisible(false);
    onAccept?.();
  };

  const handleDeny = () => {
    localStorage.setItem('cookie-consent', 'denied');
    setIsVisible(false);
    onDeny?.();
  };

  const handleClose = () => {
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-2 sm:p-4 pointer-events-none">
      <div className="max-w-7xl mx-auto pointer-events-auto">
        <div className="relative bg-white border border-black rounded-[20px] shadow-lg animate-in slide-in-from-bottom-4 duration-500">
          
          <div className="relative p-4 sm:p-6">
            <button
              onClick={handleClose}
              className="absolute top-3 right-3 sm:top-4 sm:right-4 text-black hover:text-gray-600 transition-colors z-10"
              aria-label="Close cookie consent"
            >
              <X className="h-4 w-4 sm:h-5 sm:w-5" />
            </button>

            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 sm:gap-6">
              <div className="flex items-start space-x-3 sm:space-x-4 flex-1">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 border border-black rounded-full bg-white shadow-lg flex items-center justify-center">
                    <Cookie className="h-4 w-4 sm:h-5 sm:w-5 text-black" />
                  </div>
                </div>
                <div className="flex-1 pr-8 sm:pr-0">
                  <h3 className="font-['Inter:Regular',_sans-serif] text-lg sm:text-xl font-normal text-black mb-2 tracking-[-0.8px]">
                    Cookie Preferences
                  </h3>
                  <p className="font-['Inter:Medium',_sans-serif] text-xs sm:text-sm text-black opacity-40 leading-relaxed max-w-2xl tracking-[-0.6px]">
                    We use cookies to enhance your browsing experience, provide personalized content, and analyze our traffic. 
                    Your privacy matters to us - choose your preferences below.
                  </p>
                  <div className="mt-2 sm:mt-3">
                    <a
                      href="/privacy-policy"
                      className="font-['Inter:Medium',_sans-serif] text-xs sm:text-sm text-black hover:opacity-60 underline font-medium tracking-[-0.6px]"
                    >
                      Learn more in our privacy policy →
                    </a>
                  </div>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 lg:flex-shrink-0 w-full sm:w-auto">
                <button
                  onClick={handleDeny}
                  className="bg-[rgba(0,0,0,0.02)] border-none box-border content-stretch cursor-pointer flex gap-2.5 items-center justify-center px-4 py-2 lg:px-6 lg:py-3 relative rounded-[36px] shrink-0 hover:bg-[rgba(0,0,0,0.04)] transition-colors duration-200"
                >
                  <div className="absolute border border-[rgba(0,0,0,0.1)] border-solid inset-0 pointer-events-none rounded-[36px]" />
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[14px] lg:text-[15px] text-[rgba(0,0,0,0.7)] text-center text-nowrap tracking-[-0.6px]">
                    <p className="leading-[normal] whitespace-pre">Decline</p>
                  </div>
                </button>
                <button
                  onClick={handleAccept}
                  className="bg-gradient-to-b border-none box-border content-stretch cursor-pointer flex from-[#4d4d4d] gap-2.5 items-center justify-center px-4 py-2 lg:px-6 lg:py-3 relative rounded-[36px] shrink-0 to-[#0a0a0a] shadow-[0px_8px_32px_rgba(0,0,0,0.12),0px_4px_16px_rgba(0,0,0,0.08),0px_2px_8px_rgba(0,0,0,0.06)] hover:shadow-[0px_12px_40px_rgba(0,0,0,0.15),0px_6px_20px_rgba(0,0,0,0.1),0px_3px_10px_rgba(0,0,0,0.08)] transition-shadow duration-200"
                >
                  <div className="font-['Inter:Medium',_sans-serif] font-medium leading-[0] not-italic relative shrink-0 text-[14px] lg:text-[15px] text-center text-nowrap text-white tracking-[-0.6px] z-10">
                    <p className="leading-[normal] whitespace-pre">Accept</p>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}