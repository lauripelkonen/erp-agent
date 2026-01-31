"use client";

import { useState, useEffect } from "react";

// Column configuration for the review table
interface ColumnConfig {
  key: string;
  label: string;
  visible: boolean;
  required?: boolean;
}

// Client-specific configuration
interface ClientConfig {
  clientId: string;
  clientName: string;
  columnConfig: ColumnConfig[];
  showPricing: boolean;
  additionalFields?: string[];
}

// Default configuration
const defaultConfig: ClientConfig = {
  clientId: "default",
  clientName: "Default Client",
  showPricing: true,
  columnConfig: [
    { key: "selected", label: "", visible: true, required: true },
    { key: "product_code", label: "Product Code", visible: true },
    { key: "product_name", label: "Product Name", visible: true },
    { key: "description", label: "Description", visible: false },
    { key: "original_customer_term", label: "Original Request", visible: true },
    { key: "quantity", label: "Qty", visible: true },
    { key: "unit_price", label: "Unit Price", visible: true },
    { key: "total_price", label: "Total", visible: true },
    { key: "ai_confidence", label: "Match %", visible: true },
    { key: "ai_reasoning", label: "AI Reasoning", visible: false },
  ],
};

// Example configurations for different clients
const clientConfigs: Record<string, Partial<ClientConfig>> = {
  // Client that doesn't want to see prices
  "no-pricing-client": {
    clientName: "No Pricing Client",
    showPricing: false,
    columnConfig: [
      { key: "selected", label: "", visible: true, required: true },
      { key: "product_code", label: "Product Code", visible: true },
      { key: "product_name", label: "Product Name", visible: true },
      { key: "description", label: "Description", visible: true },
      { key: "original_customer_term", label: "Original Request", visible: true },
      { key: "quantity", label: "Qty", visible: true },
      { key: "ai_confidence", label: "Match %", visible: true },
      { key: "ai_reasoning", label: "AI Reasoning", visible: true },
    ],
  },
  // Client with extended product info
  "extended-info-client": {
    clientName: "Extended Info Client",
    showPricing: true,
    additionalFields: ["material", "weight", "dimensions"],
    columnConfig: [
      { key: "selected", label: "", visible: true, required: true },
      { key: "product_code", label: "Product Code", visible: true },
      { key: "product_name", label: "Product Name", visible: true },
      { key: "description", label: "Description", visible: true },
      { key: "material", label: "Material", visible: true },
      { key: "weight", label: "Weight", visible: true },
      { key: "dimensions", label: "Dimensions", visible: true },
      { key: "original_customer_term", label: "Original Request", visible: true },
      { key: "quantity", label: "Qty", visible: true },
      { key: "unit_price", label: "Unit Price", visible: true },
      { key: "total_price", label: "Total", visible: true },
      { key: "ai_confidence", label: "Match %", visible: true },
    ],
  },
};

export function useClientConfig() {
  const [config, setConfig] = useState<ClientConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchConfig() {
      try {
        // In a real app, this would fetch from an API based on the user's client
        // For now, we'll use localStorage or default config
        const savedClientId = localStorage.getItem("client_id");

        if (savedClientId && clientConfigs[savedClientId]) {
          setConfig({
            ...defaultConfig,
            ...clientConfigs[savedClientId],
            clientId: savedClientId,
          });
        } else {
          setConfig(defaultConfig);
        }
      } catch (error) {
        console.error("Failed to fetch client config:", error);
        setConfig(defaultConfig);
      } finally {
        setIsLoading(false);
      }
    }

    fetchConfig();
  }, []);

  const updateConfig = (updates: Partial<ClientConfig>) => {
    if (config) {
      const newConfig = { ...config, ...updates };
      setConfig(newConfig);
      // Optionally save to localStorage or API
    }
  };

  const setClientId = (clientId: string) => {
    localStorage.setItem("client_id", clientId);
    if (clientConfigs[clientId]) {
      setConfig({
        ...defaultConfig,
        ...clientConfigs[clientId],
        clientId,
      });
    } else {
      setConfig({ ...defaultConfig, clientId });
    }
  };

  return {
    config,
    isLoading,
    updateConfig,
    setClientId,
    availableClients: Object.keys(clientConfigs),
  };
}
