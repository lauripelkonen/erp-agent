export interface CookiePreferences {
  necessary: boolean;
  analytics: boolean;
  marketing: boolean;
  functional: boolean;
}

export const defaultPreferences: CookiePreferences = {
  necessary: true, // Always true, can't be disabled
  analytics: false,
  marketing: false,
  functional: false,
};

export const cookieManager = {
  // Get current consent status
  getConsentStatus(): 'accepted' | 'denied' | null {
    return localStorage.getItem('cookie-consent') as 'accepted' | 'denied' | null;
  },

  // Get cookie preferences
  getPreferences(): CookiePreferences {
    const saved = localStorage.getItem('cookie-preferences');
    if (saved) {
      try {
        return { ...defaultPreferences, ...JSON.parse(saved) };
      } catch {
        return defaultPreferences;
      }
    }
    return defaultPreferences;
  },

  // Set cookie preferences
  setPreferences(preferences: Partial<CookiePreferences>): void {
    const current = this.getPreferences();
    const updated = { ...current, ...preferences, necessary: true };
    localStorage.setItem('cookie-preferences', JSON.stringify(updated));
  },

  // Accept all cookies
  acceptAll(): void {
    localStorage.setItem('cookie-consent', 'accepted');
    this.setPreferences({
      analytics: true,
      marketing: true,
      functional: true,
    });
    this.enableCookies();
  },

  // Deny all non-necessary cookies
  denyAll(): void {
    localStorage.setItem('cookie-consent', 'denied');
    this.setPreferences({
      analytics: false,
      marketing: false,
      functional: false,
    });
    this.disableCookies();
  },

  // Clear all consent data
  clearConsent(): void {
    localStorage.removeItem('cookie-consent');
    localStorage.removeItem('cookie-preferences');
  },

  // Enable cookies based on preferences
  enableCookies(): void {
    const preferences = this.getPreferences();
    
    // Enable analytics cookies (Google Analytics, etc.)
    if (preferences.analytics) {
      this.enableAnalytics();
    }

    // Enable marketing cookies
    if (preferences.marketing) {
      this.enableMarketing();
    }

    // Enable functional cookies
    if (preferences.functional) {
      this.enableFunctional();
    }
  },

  // Disable all non-necessary cookies
  disableCookies(): void {
    this.disableAnalytics();
    this.disableMarketing();
    this.disableFunctional();
  },

  // Analytics cookies management
  enableAnalytics(): void {
    // Add Google Analytics or other analytics scripts here
    console.log('Analytics cookies enabled');
    
    // Example: Enable Google Analytics
    // if (typeof gtag !== 'undefined') {
    //   gtag('consent', 'update', {
    //     'analytics_storage': 'granted'
    //   });
    // }
  },

  disableAnalytics(): void {
    console.log('Analytics cookies disabled');
    
    // Example: Disable Google Analytics
    // if (typeof gtag !== 'undefined') {
    //   gtag('consent', 'update', {
    //     'analytics_storage': 'denied'
    //   });
    // }
  },

  // Marketing cookies management
  enableMarketing(): void {
    console.log('Marketing cookies enabled');
    
    // Example: Enable marketing tracking
    // if (typeof gtag !== 'undefined') {
    //   gtag('consent', 'update', {
    //     'ad_storage': 'granted'
    //   });
    // }
  },

  disableMarketing(): void {
    console.log('Marketing cookies disabled');
    
    // Example: Disable marketing tracking
    // if (typeof gtag !== 'undefined') {
    //   gtag('consent', 'update', {
    //     'ad_storage': 'denied'
    //   });
    // }
  },

  // Functional cookies management
  enableFunctional(): void {
    console.log('Functional cookies enabled');
  },

  disableFunctional(): void {
    console.log('Functional cookies disabled');
  },

  // Check if a specific cookie type is allowed
  isAllowed(type: keyof CookiePreferences): boolean {
    const preferences = this.getPreferences();
    return preferences[type];
  },

  // Initialize cookie manager on app start
  initialize(): void {
    const consent = this.getConsentStatus();
    
    if (consent === 'accepted') {
      this.enableCookies();
    } else if (consent === 'denied') {
      this.disableCookies();
    }
    // If no consent, cookies remain disabled until user makes a choice
  }
};