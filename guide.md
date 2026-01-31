# Landing Page Blueprint — AI Agents for Wholesale ERP Automation

This document is a complete content and UX blueprint for a high‑converting landing page. It includes copy, sections, components, images, icons, and analytics/SEO guidance.

Current product reality to reflect:
- ERP integrations: Lemonsoft (General Availability), NetSuite (Early Access — selling now; onboard early adopters).
- Live customer: first Lemonsoft customer with agents in production (purchasing + offer/quote automation).
- Vertical: wholesale/distribution (initial ICP).

---

## 1) Hero (Above the Fold)

Suggested H1 options:
- “Cut purchasing workload by 50% and 2× quote throughput — AI agents for your ERP.”
- “AI agents that run purchasing and quotes directly in your ERP.”

Sub‑headline:
- “Deploy domain‑trained agents that create POs, compare vendors, and generate offers automatically — with approvals and full audit trails.”

Primary CTAs:
- Button (Primary): “Book a 20‑min demo”
- Button (Secondary): “Calculate your ROI” (opens calculator modal)

Trust strip (under CTAs):
- “Built for wholesale & distribution” • “<30 days to first agent live” • “Human‑in‑the‑loop approvals” • “SOC 2 (in progress)”

Hero visuals (choose one):
- Option A: Dashboard mock (agents queue + approval modal) on laptop + mobile side‑by‑side
- Option B: Three card illustration for Purchase Agent, Quote Agent, AP Agent with small agent avatars

Image assets to include:
- hero-dashboard.png (UI mock of agents working + approval card)
- agent-avatars.svg (neutral assistant icons)
- logos-placeholder.png (placeholder for future logo bar)

---

## 2) Quantified ROI Band

Large metric tiles (4):
- “50% fewer purchasing hours”
- “2× faster quote/offer turnaround”
- “< 30 days to first deployment”
- “99.9% agent uptime”

Subtext: “Measured with our first Lemonsoft customer; results vary by SKU count, vendor mix, and approval policy.”

---

## 3) How It Works (3 Steps)

Step cards with icons:
1. Connect your ERP  
   Lemonsoft (GA) • NetSuite (Early Access)  
   Icon: plug-in.svg
2. Pick your agents  
   Purchasing, Quote/Offer, Accounts Payable (roadmap), Inventory Replenishment (roadmap)  
   Icon: magic-wand.svg
3. Approve & monitor  
   Human‑in‑the‑loop, role‑based approvals, full audit trails  
   Icon: shield-check.svg

Diagram (optional): data-flow.png showing: ERP ↔ Agents ↔ Approvals/Inbox ↔ Vendors/Customers.

---

## 4) Product Sections (Feature Deep Dives)

### 4.1 Purchasing Automation Agent (Live)
- Auto‑creates POs from reorder signals, vendor SLAs, and price lists.
- Vendor selection with multi‑criteria scoring (price, lead time, historic reliability).
- Exception handling and approval routing by category/value thresholds.
- EDI/email order sending and confirmation parsing.
Visuals: purchasing-agent-screen.png (queue of suggested POs + scoring table), vendor-compare.png.

### 4.2 Quote & Offer Agent (Live)
- Generates customer‑ready quotes from requests/emails/CRM notes.
- Applies pricing rules, discounts, and availability checks from ERP.
- Sends offers with tracked follow‑ups; logs all actions back to ERP/CRM.
Visual: quote-agent-screen.png (quote composer + approval bar).

### 4.3 Transfers
- Execute daily stock transfers 


Component: tabbed feature switcher with “Purchasing / Quotes / Transfers.

---

## 5) Integrations

Integration badges:
- Lemonsoft — Available Now (GA)
- NetSuite — Early Access (onboarding pilot customers now)

Copy (bold key line):
- **Works inside your ERP:** agents read/write via your tenant’s API credentials. No data duplication; full audit trails.
- Email/EDI connectors for vendor comms; SSO and role mapping supported.

Visuals: integration-badges.svg, netsuite-badge.svg, lemonsoft-badge.svg.

---

## 6) Proof & Case Study

Mini‑case (from first Lemonsoft customer):
- 10k+ SKUs; 500+ monthly POs; 100+ monthly quotes.
- Results (first 60 days):
  - 50% reduction in purchasing hours.
  - 2× increase in quote throughput.
  - 0 compliance incidents; all actions auditable.

CTA: “See the full case study” (downloads PDF or opens modal).  
Visual: before-after-graph.png.

---

## 7) Security & Compliance

Bullets with icons:
- Customer‑owned credentials; least‑privilege scopes (key.svg)
- Encrypted in transit and at rest (lock.svg)
- Audit logging for every agent action (clipboard-list.svg)
- VPC / private deploy options (cloud-shield.svg)
- SOC 2 Type I/II: In progress — target date listed (badge-soc2.svg)

Trust badges row (placeholders): soc2-badge.svg, gdpr-badge.svg, sso-badge.svg.

---

## 8) Pricing (Value‑Based with Pilot)

Suggested structure:
- “Pilot” (fixed‑fee; 6–8 weeks): Outcomes + clear success criteria
- “Production” (value‑based): tiered by agents deployed and volume
- Enterprise: multi‑site rollouts, SSO/SLA, private deploy

CTAs in pricing section:
- “Request pilot proposal” (primary)
- “See ROI calculator” (secondary)

Note: Do not publish numerical pricing until case studies are live; use ROI framing.

---

## 9) Conversion CTAs (Placement Map)

- Sticky header CTA: “Book Demo”
- Hero buttons: “Book Demo” + “Calculate ROI”
- Mid‑page band after ROI: “See a 6‑minute demo video”
- End of each product section: “Talk to an expert”
- Footer: “Join Early Access for NetSuite” (small badge + form)

---

## 10) Social Proof

Elements:
- Customer logos (when available)
- Testimonial cards (quote + role + company)
- Analyst/association quotes (if any)
- “Used by teams in Purchasing, Sales Ops, and Finance” row

Placeholders: testimonial-1.png, testimonial-2.png.

---

## 11) FAQ (Expandable)

Q: Do the agents work inside Lemonsoft and NetSuite?  
A: Yes. Lemonsoft is available now. NetSuite is in Early Access — we’re onboarding pilot customers today.

Q: Who approves what agents do?  
A: You define policies and thresholds; every action can require user approval, with full audit logs.

Q: How fast can we go live?  
A: Most teams deploy the first agent in under 30 days.

Q: What about data security?  
A: Customer‑owned credentials, least privilege scopes, encryption, and audit trails. SOC 2 in progress.

Q: How is this priced?  
A: Pilot with success criteria, then value‑based production pricing aligned to savings and throughput.

---

## 12) Visual/Asset Checklist

Icons (simple line icons, monochrome): plug-in.svg, magic-wand.svg, shield-check.svg, lock.svg, key.svg, cloud-shield.svg, clipboard-list.svg, graph-up.svg.

Images/Illustrations to design:
- hero-dashboard.png (hero UI)
- purchasing-agent-screen.png (table + approval)
- vendor-compare.png (scoring)
- quote-agent-screen.png (offer builder)
- data-flow.png (ERP ↔ Agents ↔ Approvals)
- before-after-graph.png (ROI)
- integration-badges.svg (Lemonsoft, NetSuite)
- badges: soc2-badge.svg, gdpr-badge.svg, sso-badge.svg

Video:
- 90‑second explainer (mp4 + poster image: video-thumb.png)
- Secondary 6‑minute product walkthrough

---

## 13) Components & UX

- Responsive hero with split visual + CTAs
- Sticky header with CTA
- Metrics band (4 KPIs)
- Feature tabs (agents)
- Testimonial carousel
- Integration badges (Lemonsoft GA, NetSuite Early Access)
- ROI calculator modal (inputs: buyers, quotes/month, average PO value; outputs: hours saved, payback)
- FAQ accordion
- Exit‑intent modal: “Get the pilot checklist”

---

## 14) Copy Blocks (Ready to Use)

Short value prop:  
“AI agents that run purchasing and quoting inside your ERP — cut purchasing hours by 50% and 2× quote throughput.”

Integration ribbon copy:  
“Works with Lemonsoft today; NetSuite Early Access — pilots onboarding now.”

Pilot CTA copy:  
“Run a 6–8 week pilot with defined success targets. If we don’t hit them, you don’t pay.”

Security copy:  
“Customer‑owned credentials, least‑privilege access, end‑to‑end audit trails. SOC 2 underway.”

Early Access (NetSuite) copy:  
“NetSuite teams: join our Early Access and be first to deploy Purchasing and Quote agents.”

---

## 15) SEO & Analytics

Meta title:  
“AI Purchasing & Quote Agents for ERP (Lemonsoft & NetSuite) — Cut Work by 50%”

Meta description:  
“Deploy domain‑trained AI agents that automate purchasing and quotes inside your ERP. Lemonsoft (GA) and NetSuite (Early Access). 30‑day go‑live.”

Schema:  
- Organization, Product, FAQPage
- Event (if hosting webinars)

Tracking:
- GA4 + GTM; track: demo clicks, ROI modal opens, video plays (25/50/75/100%), form submits, scroll depth.

---

## 16) Sections Order (Wireframe Outline)

1. Hero (H1, subhead, CTAs, hero visual, trust strip)
2. ROI metrics band
3. How it works (3 steps)
4. Product tabs (agents)
5. Integrations (Lemonsoft GA, NetSuite Early Access)
6. Proof / Case study
7. Security & compliance
8. Pricing (pilot → production)
9. Testimonials / logos
10. FAQ
11. Final CTA band (Demo + Early Access)

---

## 17) Messaging for Current State vs. Future State

What to say now:
- “Supports Lemonsoft today; NetSuite Early Access onboarding now.”
- “First customer live on Lemonsoft: 50% fewer purchasing hours, 2× quote throughput.”

What to say as we scale:
- “Certified partner badges” (when applicable)
- “Customer logos and multi‑site case studies”

---

## 18) Experiments Backlog (CRO)

- A/B test hero headline variants (metrics vs. speed).
- Add sticky ‘Chat to an agent’ widget vs. simple contact button.
- ROI calculator gated vs. ungated PDF.
- Early Access form length (4 fields vs. 8 fields).
- Social proof order (logos first vs. quote first).

---

## 19) Legal & Claims

Small print beneath ROI claims:  
“Results are based on early customer deployments and depend on SKU count, vendor base, approval thresholds, and data quality.”

Privacy/footer: link to DPA, security overview, and terms.

---

## 20) Final CTAs (Copy Snippets)

- “Book a 20‑min demo”
- “Run a pilot”
- “Join NetSuite Early Access”
- “Calculate ROI”
