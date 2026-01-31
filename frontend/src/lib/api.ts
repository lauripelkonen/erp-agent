/**
 * API utility for making requests to the offer-agent backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Get the full API URL for an endpoint.
 * Backend API is at /offer-agent/api/...
 */
export function getApiUrl(endpoint: string): string {
  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}/offer-agent/api${normalizedEndpoint}`;
}

/**
 * Get the health check URL.
 */
export function getHealthUrl(): string {
  return `${API_BASE_URL}/offer-agent/health`;
}

/**
 * API client with common configuration.
 */
export const api = {
  /**
   * Fetch pending offers.
   */
  async getPendingOffers() {
    const response = await fetch(getApiUrl("/offers/pending"));
    if (!response.ok) {
      throw new Error("Failed to fetch pending offers");
    }
    return response.json();
  },

  /**
   * Fetch all offers with status.
   */
  async getOffersStatus() {
    const response = await fetch(getApiUrl("/offers/status"));
    if (!response.ok) {
      throw new Error("Failed to fetch offers status");
    }
    return response.json();
  },

  /**
   * Fetch a single offer by ID.
   */
  async getOffer(offerId: string) {
    const response = await fetch(getApiUrl(`/offers/${offerId}`));
    if (!response.ok) {
      throw new Error("Failed to fetch offer");
    }
    return response.json();
  },

  /**
   * Create a new offer.
   */
  async createOffer(data: {
    sender: string;
    subject: string;
    body: string;
    attachments?: Array<{ filename: string; data: string; mime_type?: string }>;
  }) {
    const response = await fetch(getApiUrl("/offers/create"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error("Failed to create offer");
    }
    return response.json();
  },

  /**
   * Send an offer to ERP.
   */
  async sendToERP(offerId: string, lineIds: string[]) {
    const response = await fetch(getApiUrl(`/offers/${offerId}/send`), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ line_ids: lineIds }),
    });
    if (!response.ok) {
      throw new Error("Failed to send offer to ERP");
    }
    return response.json();
  },

  /**
   * Delete an offer.
   */
  async deleteOffer(offerId: string) {
    const response = await fetch(getApiUrl(`/offers/${offerId}`), {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error("Failed to delete offer");
    }
    return response.json();
  },

  /**
   * Health check.
   */
  async healthCheck() {
    const response = await fetch(getHealthUrl());
    if (!response.ok) {
      throw new Error("Health check failed");
    }
    return response.json();
  },
};
