// Demo data for the AI Offer Generation demo page
// All data is hardcoded for demonstration purposes

export interface DemoCustomer {
  id: string;
  customer_number: string;
  name: string;
  street: string;
  postal_code: string;
  city: string;
  email: string;
  contact_person: string;
  payment_terms: string;
}

export interface DemoOfferLine {
  id: string;
  product_code: string;
  product_name: string;
  original_customer_term: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  ai_confidence: number;
  ai_reasoning: string;
}

export interface DemoOffer {
  id: string;
  offer_number: string;
  customer: DemoCustomer;
  lines: DemoOfferLine[];
  total_amount: number;
  created_at: string;
}

export interface DemoToolCall {
  tool: string;
  displayName: string;
  icon: "Users" | "UserCheck" | "Search" | "Brain" | "Calculator" | "Package";
  color: string;
  duration: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
}

// Demo Customers
export const DEMO_CUSTOMERS: DemoCustomer[] = [
  {
    id: "demo-1",
    customer_number: "100001",
    name: "Rakennusliike Virtanen Oy",
    street: "Teollisuustie 15",
    postal_code: "00100",
    city: "Helsinki",
    email: "tilaukset@virtanen.fi",
    contact_person: "Matti Virtanen",
    payment_terms: "14 päivää netto",
  },
  {
    id: "demo-2",
    customer_number: "100002",
    name: "LVI-Asennus Korhonen",
    street: "Putkikuja 8",
    postal_code: "33100",
    city: "Tampere",
    email: "info@lvi-korhonen.fi",
    contact_person: "Juha Korhonen",
    payment_terms: "30 päivää netto",
  },
  {
    id: "demo-3",
    customer_number: "100003",
    name: "Teräspaja Nieminen",
    street: "Metallitie 22",
    postal_code: "20100",
    city: "Turku",
    email: "myynti@teraspaja.fi",
    contact_person: "Anna Nieminen",
    payment_terms: "7 päivää netto",
  },
];

// Demo Offer Result (Always the Same)
export const DEMO_OFFER: DemoOffer = {
  id: "demo-offer-001",
  offer_number: "DEMO-2025-001",
  customer: DEMO_CUSTOMERS[0],
  lines: [
    {
      id: "line-1",
      product_code: "HST-DN50-KAU",
      product_name: "DN50 Kaulus HST",
      original_customer_term: "dn50 kauluksia",
      quantity: 10,
      unit_price: 12.50,
      total_price: 125.00,
      ai_confidence: 95,
      ai_reasoning: "Exact match: 'DN50' + 'kaulus' found in product name",
    },
    {
      id: "line-2",
      product_code: "HST-DN65-KAU",
      product_name: "DN65 Kaulus HST",
      original_customer_term: "65mm kaulukset",
      quantity: 5,
      unit_price: 15.80,
      total_price: 79.00,
      ai_confidence: 88,
      ai_reasoning: "Semantic match: '65mm' → 'DN65', 'kaulukset' → 'kaulus'",
    },
    {
      id: "line-3",
      product_code: "HST-DN50-IRO",
      product_name: "DN50 Irtolaippa HST",
      original_customer_term: "irtolaippoja 50",
      quantity: 8,
      unit_price: 18.20,
      total_price: 145.60,
      ai_confidence: 82,
      ai_reasoning: "Pattern match: 'irtolaippa' + size '50' → DN50 Irtolaippa",
    },
    {
      id: "line-4",
      product_code: "TER-PUTKI-25",
      product_name: "Teräsputki 25mm",
      original_customer_term: "teräsputkea 25mm 3m",
      quantity: 3,
      unit_price: 45.00,
      total_price: 135.00,
      ai_confidence: 72,
      ai_reasoning: "Wildcard: 'teräsputk*' + dimension match. Note: length 3m not in system",
    },
  ],
  total_amount: 484.60,
  created_at: new Date().toISOString(),
};

// Tool Execution Sequence (Deterministic timing) - one search + match per product
export const DEMO_TOOL_SEQUENCE: DemoToolCall[] = [
  // Customer matching
  {
    tool: "search_customers",
    displayName: "Search Customers",
    icon: "Users",
    color: "blue",
    duration: 800,
    input: { query: "Virtanen" },
    output: { found: 3 },
  },
  {
    tool: "match_customer",
    displayName: "Match Customer",
    icon: "UserCheck",
    color: "green",
    duration: 1000,
    input: { company: "Rakennusliike Virtanen" },
    output: { match: "100001", confidence: 98 },
  },
  // Product 1: DN50 Kaulus
  {
    tool: "wildcard_search_1",
    displayName: "Wildcard Search",
    icon: "Search",
    color: "purple",
    duration: 600,
    input: { pattern: "dn50*kaulus*" },
    output: { results: 2 },
  },
  {
    tool: "match_product_1",
    displayName: "Match Product",
    icon: "Package",
    color: "teal",
    duration: 500,
    input: { term: "dn50 kauluksia", candidates: 2 },
    output: { match: "HST-DN50-KAU", confidence: 95 },
  },
  // Product 2: DN65 Kaulus
  {
    tool: "wildcard_search_2",
    displayName: "Wildcard Search",
    icon: "Search",
    color: "purple",
    duration: 550,
    input: { pattern: "dn65*kaulus*" },
    output: { results: 1 },
  },
  {
    tool: "match_product_2",
    displayName: "Match Product",
    icon: "Package",
    color: "teal",
    duration: 450,
    input: { term: "65mm kaulukset", candidates: 1 },
    output: { match: "HST-DN65-KAU", confidence: 88 },
  },
  // Product 3: Irtolaippa
  {
    tool: "semantic_search_3",
    displayName: "Semantic Search",
    icon: "Brain",
    color: "orange",
    duration: 1200,
    input: { query: "irtolaippoja 50" },
    output: { results: 3 },
  },
  {
    tool: "match_product_3",
    displayName: "Match Product",
    icon: "Package",
    color: "teal",
    duration: 600,
    input: { term: "irtolaippoja 50", candidates: 3 },
    output: { match: "HST-DN50-IRO", confidence: 82 },
  },
  // Product 4: Teräsputki
  {
    tool: "wildcard_search_4",
    displayName: "Wildcard Search",
    icon: "Search",
    color: "purple",
    duration: 700,
    input: { pattern: "teräsputk*25*" },
    output: { results: 2 },
  },
  {
    tool: "match_product_4",
    displayName: "Match Product",
    icon: "Package",
    color: "teal",
    duration: 550,
    input: { term: "teräsputkea 25mm", candidates: 2 },
    output: { match: "TER-PUTKI-25", confidence: 72 },
  },
  // Final pricing
  {
    tool: "calculate_pricing",
    displayName: "Calculate Pricing",
    icon: "Calculator",
    color: "green",
    duration: 400,
    input: { customer: "100001", lines: 4 },
    output: { total: 484.60 },
  },
];

// Pre-filled order text for demo
export const DEMO_ORDER_TEXT = `Hei,

Tarvitsemme seuraavia tuotteita:

- 10 kpl dn50 kauluksia
- 5 kpl 65mm kaulukset
- 8 kpl irtolaippoja 50
- 3 kpl teräsputkea 25mm 3m

Toimitusaika mahdollisimman pian.

Ystävällisin terveisin,
Matti Virtanen
Rakennusliike Virtanen Oy`;

// Product database for code lookups (cycles through these when user edits product codes)
export const DEMO_PRODUCTS: Record<string, { name: string; unit_price: number }> = {
  "HST-DN50-KAU": { name: "DN50 Kaulus HST", unit_price: 12.50 },
  "HST-DN65-KAU": { name: "DN65 Kaulus HST", unit_price: 15.80 },
  "HST-DN80-KAU": { name: "DN80 Kaulus HST", unit_price: 18.90 },
  "HST-DN100-KAU": { name: "DN100 Kaulus HST", unit_price: 24.50 },
  "HST-DN50-IRO": { name: "DN50 Irtolaippa HST", unit_price: 18.20 },
  "HST-DN65-IRO": { name: "DN65 Irtolaippa HST", unit_price: 22.40 },
  "HST-DN80-IRO": { name: "DN80 Irtolaippa HST", unit_price: 28.60 },
  "TER-PUTKI-25": { name: "Teräsputki 25mm", unit_price: 45.00 },
  "TER-PUTKI-32": { name: "Teräsputki 32mm", unit_price: 52.00 },
  "TER-PUTKI-40": { name: "Teräsputki 40mm", unit_price: 61.00 },
  "KUP-PUTKI-15": { name: "Kupariputki 15mm", unit_price: 28.00 },
  "KUP-PUTKI-22": { name: "Kupariputki 22mm", unit_price: 35.00 },
  "RST-LAIPPA-50": { name: "RST Laippa DN50", unit_price: 42.00 },
  "RST-LAIPPA-65": { name: "RST Laippa DN65", unit_price: 48.00 },
  "TIIV-DN50": { name: "Tiiviste DN50", unit_price: 3.50 },
  "TIIV-DN65": { name: "Tiiviste DN65", unit_price: 4.20 },
};

// Fallback products when unknown code is entered (cycles through these)
export const FALLBACK_PRODUCTS = [
  { code: "MISC-001", name: "Yleistuote A", unit_price: 15.00 },
  { code: "MISC-002", name: "Yleistuote B", unit_price: 22.50 },
  { code: "MISC-003", name: "Yleistuote C", unit_price: 18.75 },
  { code: "MISC-004", name: "Yleistuote D", unit_price: 31.00 },
];
