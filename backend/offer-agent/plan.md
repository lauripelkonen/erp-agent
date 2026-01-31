Multi-ERP Architecture Refactoring Plan

 Overview

 Refactor the 2,359-line main.py into a scalable multi-ERP architecture supporting Lemonsoft, Jeeves, Oscar, and future ERPs using a Modified Strangler Fig pattern that extracts and
 abstracts components simultaneously.

 Architecture Goals

 1. Break down main.py into logical, testable modules
 2. Abstract ERP operations behind interfaces for multi-ERP support
 3. Keep system working throughout migration (Strangler Fig)
 4. Maintain generic dataclasses (ProductMatch, Pricing models)
 5. Support optional database optimization per ERP

 ---
 Phase 1: Foundation & Structure (Week 1)

 1.1 Create New Directory Structure

 src/
 ├── domain/                    # NEW: ERP-agnostic models
 │   ├── customer.py           # Generic Customer entity
 │   ├── product.py            # Generic Product entity
 │   ├── offer.py              # Generic Offer, OfferLine entities
 │   ├── person.py             # Generic Person/Salesperson
 │   └── pricing.py            # Keep existing LineItemPricing, OfferPricing
 │
 ├── erp/                       # NEW: ERP abstraction layer
 │   ├── base/                 # Abstract interfaces
 │   │   ├── customer_repository.py
 │   │   ├── product_repository.py
 │   │   ├── offer_repository.py
 │   │   ├── pricing_service.py
 │   │   └── person_repository.py
 │   │
 │   ├── lemonsoft/            # Lemonsoft implementation
 │   │   ├── customer_adapter.py
 │   │   ├── product_adapter.py
 │   │   ├── offer_adapter.py
 │   │   ├── pricing_adapter.py
 │   │   ├── person_adapter.py
 │   │   └── field_mapper.py   # Maps generic ↔ Lemonsoft fields
 │   │
 │   └── factory.py            # ERP factory (selects implementation)
 │
 ├── extraction/                # NEW: AI extraction services (from main.py)
 │   ├── company_extractor.py  # Extract company info (lines 450-700)
 │   ├── contact_extractor.py  # Extract delivery contact
 │   └── reference_extractor.py # Extract customer reference
 │
 ├── core/                      # NEW: Business orchestration
 │   ├── orchestrator.py       # Slim orchestrator (NEW PATH)
 │   ├── workflow.py           # Workflow steps definition
 │   └── state.py              # Request state management
 │
 ├── lemonsoft/                 # Keep existing (used by adapters)
 │   ├── api_client.py         # Keep as-is
 │   └── database_connection.py # Keep as-is
 │
 ├── main.py                    # Keep OLD orchestrator (deprecate later)
 └── main_v2.py                 # NEW orchestrator entry point

 1.2 Define Generic Domain Models

 - Create domain/customer.py: Customer entity with erp_metadata dict
 - Create domain/offer.py: Offer, OfferLine entities
 - Create domain/product.py: Product entity
 - Create domain/person.py: Person/Salesperson entity
 - Keep pricing/calculator.py dataclasses as-is (already generic)

 1.3 Define Abstract ERP Interfaces

 - erp/base/customer_repository.py: find_by_name, find_by_number, get_payment_terms, get_invoicing_details
 - erp/base/offer_repository.py: create, add_line, get, verify
 - erp/base/pricing_service.py: calculate_pricing, get_customer_discount (with optional DB access)
 - erp/base/person_repository.py: find_by_email, find_by_number
 - erp/base/product_repository.py: search, get_by_code

 ---
 Phase 2: Extract AI Extraction Layer (Week 2)

 2.1 Extract from main.py → extraction/ module

 Move these methods (lines 450-885):
 - _extract_company_information() → extraction/company_extractor.py
 - _extract_company_and_contact_with_ai() → extraction/company_extractor.py
 - _retry_company_extraction_with_ai() → extraction/company_extractor.py
 - _fallback_combined_extraction() → extraction/company_extractor.py

 Create: CompanyExtractor class with:
 - extract_company_name(email_body) → str
 - extract_delivery_contact(email_body) → dict
 - extract_customer_reference(email_body) → str
 - All AI prompts and retry logic

 Why first? This layer has zero ERP coupling - pure AI/text processing.

 2.2 Add Tests

 - Test company extraction with sample emails
 - Test retry logic
 - Mock Gemini API calls

 ---
 Phase 3: Build Lemonsoft Adapter (Week 3-4)

 3.1 Implement Lemonsoft Field Mapper

 Create: erp/lemonsoft/field_mapper.py
 - to_customer(lemonsoft_data: dict) → Customer: Map Lemonsoft → generic
 - from_offer(offer: Offer) → dict: Map generic → Lemonsoft API format
 - Handle all 20+ Lemonsoft-specific field names
 - Map deny_credit → credit_allowed, delivery method codes, etc.

 3.2 Implement Customer Adapter

 Create: erp/lemonsoft/customer_adapter.py
 - Implements CustomerRepository interface
 - Wraps existing LemonsoftAPIClient
 - find_by_name(): Call /api/customers?filter.search=name
 - find_by_number(): Call /api/customers?filter.customer_number=X
 - Uses field_mapper to convert Lemonsoft data → Customer domain model
 - Reuse logic from customer/enhanced_lookup.py

 3.3 Implement Offer Adapter

 Create: erp/lemonsoft/offer_adapter.py
 - Implements OfferRepository interface
 - create(offer: Offer) → str: 3-step Lemonsoft process (POST /api/offers/6 → GET → PUT)
 - add_line(offer_id, line: OfferLine): POST /api/offers/{number}/offerrows
 - Uses field_mapper to convert Offer → Lemonsoft format
 - Extract logic from main.py lines 1260-1637

 3.4 Implement Pricing Adapter

 Create: erp/lemonsoft/pricing_adapter.py
 - Implements PricingService interface
 - Reuse existing pricing/calculator.py (already mostly generic)
 - Wrap database access for discounts
 - calculate_pricing(customer, products) → OfferPricing

 3.5 Implement Person Adapter

 Create: erp/lemonsoft/person_adapter.py
 - Implements PersonRepository interface
 - find_by_email(email) → Person: Call /api/persons?filter.search=email
 - Extract from main.py lines 896-982

 3.6 Create ERP Factory

 Create: erp/factory.py
 - Read erp_type from config (default: "lemonsoft")
 - create_customer_repository(): Return LemonsoftCustomerAdapter
 - create_offer_repository(): Return LemonsoftOfferAdapter
 - create_pricing_service(): Return LemonsoftPricingAdapter
 - create_person_repository(): Return LemonsoftPersonAdapter
 - Extensible for future ERPs (Jeeves, Oscar)

 ---
 Phase 4: Build New Orchestrator (Week 5) - Strangler Pattern Starts

 4.1 Create Workflow Definition

 Create: core/workflow.py
 - OfferWorkflow class with clear steps:
   a. extract_company_info(email) → uses CompanyExtractor
   b. lookup_customer(company_name) → uses CustomerRepository
   c. lookup_salesperson(email) → uses PersonRepository
   d. match_products(email, attachments) → uses existing ProductMatcher
   e. calculate_pricing(customer, products) → uses PricingService
   f. create_offer(offer_data) → uses OfferRepository
   g. send_notification(offer) → uses existing NotificationService
 - Clear separation: workflow logic vs ERP operations

 4.2 Create Slim Orchestrator

 Create: core/orchestrator.py
 - OfferAutomationOrchestrator (NEW VERSION)
 - Uses ERPFactory to get repositories/services
 - Uses CompanyExtractor for AI extraction
 - Uses OfferWorkflow to execute
 - ~200 lines instead of 2,359
 - All ERP operations go through abstract interfaces

 4.3 Create New Entry Point

 Create: main_v2.py
 - Instantiate new orchestrator
 - Same email processing loop as old main.py
 - Route requests through new workflow
 - Feature flag: USE_NEW_ORCHESTRATOR (default: False initially)

 4.4 Add Integration Tests

 - Test full workflow end-to-end with Lemonsoft
 - Compare outputs: old orchestrator vs new orchestrator
 - Verify field mappings are correct

 ---
 Phase 5: Gradual Migration (Week 6-7)

 5.1 A/B Testing Setup

 - Add feature flag in config: orchestrator_version: "v1" | "v2"
 - Route percentage of traffic to new orchestrator
 - Log both paths for comparison
 - Monitor for errors/discrepancies

 5.2 Expand Test Coverage

 - Add tests for edge cases
 - Test error handling, retries
 - Test all Lemonsoft-specific logic in adapters
 - Ensure parity with old system

 5.3 Full Migration

 - Once new orchestrator proven stable (e.g., 2 weeks in production)
 - Switch orchestrator_version: "v2" as default
 - Monitor for 1 week
 - Keep old main.py code for rollback safety

 5.4 Deprecate Old Code

 - After successful migration (e.g., 1 month stable)
 - Remove old main.py orchestrator methods
 - Keep only email loop and utility functions
 - Clean up unused imports

 ---
 Phase 6: Second ERP Support (Week 8-10)

 6.1 Research Jeeves/Oscar APIs

 - Study API documentation
 - Identify field mappings
 - Understand authentication
 - Document differences from Lemonsoft

 6.2 Implement Jeeves Adapter (Example)

 Create: erp/jeeves/
 - customer_adapter.py: Implement CustomerRepository for Jeeves API
 - offer_adapter.py: Implement OfferRepository for Jeeves API
 - pricing_adapter.py: Implement PricingService (API-only, no DB)
 - field_mapper.py: Map generic ↔ Jeeves fields
 - Update erp/factory.py to support erp_type: "jeeves"

 6.3 Configuration per ERP

 Update: config/settings.py
 erp_type: str = "lemonsoft"  # or "jeeves", "oscar"

 # Lemonsoft config (loaded only if erp_type == "lemonsoft")
 lemonsoft_username: Optional[str]
 lemonsoft_password: Optional[str]
 lemonsoft_database: Optional[str]

 # Jeeves config (loaded only if erp_type == "jeeves")
 jeeves_api_key: Optional[str]
 jeeves_company_id: Optional[str]

 6.4 Test New ERP

 - Deploy test instance with erp_type: "jeeves"
 - Run integration tests
 - Verify offer creation
 - Compare with Lemonsoft behavior

 ---
 Phase 7: Optimization & Hardening (Ongoing)

 7.1 Performance Optimization

 - Add caching layer for customer lookups
 - Optimize database queries in pricing adapter
 - Async/await optimization for API calls

 7.2 Monitoring & Logging

 - Add ERP-specific metrics (API call latency, error rates per ERP)
 - Log field mapping transformations for debugging
 - Alert on ERP adapter failures

 7.3 Documentation

 - Document how to add new ERP adapter
 - Document field mapping process
 - API documentation for each ERP

 ---
 Risk Mitigation

 Risks & Mitigations:

 1. Risk: New orchestrator behaves differently than old
   - Mitigation: A/B testing, extensive logging, gradual rollout
 2. Risk: Lemonsoft field mappings incorrect
   - Mitigation: Integration tests comparing old vs new outputs
 3. Risk: Performance regression (more abstraction layers)
   - Mitigation: Benchmark before/after, optimize hot paths
 4. Risk: Breaking existing production system
   - Mitigation: Strangler Fig keeps old code working, feature flags for rollback

 ---
 Success Criteria

 ✅ Phase 1-2: Extraction layer working, tests pass
 ✅ Phase 3-4: New orchestrator creates identical Lemonsoft offers as old code
 ✅ Phase 5: New orchestrator handling 100% of production traffic with <1% error rate
 ✅ Phase 6: Second ERP (Jeeves/Oscar) successfully creating offers
 ✅ Final: main.py reduced from 2,359 lines to <500 lines (just email loop + utils)

 ---
 Estimated Timeline

 - Phase 1-2: 2 weeks (Foundation + Extraction)
 - Phase 3-4: 3 weeks (Adapters + New Orchestrator)
 - Phase 5: 2-3 weeks (Migration + Testing)
 - Phase 6: 2-3 weeks (Second ERP)
 - Total: ~10-12 weeks for full multi-ERP architecture

 ---
 Key Principles

 1. No Big Bang: Old code keeps working throughout
 2. Extract + Abstract Together: Avoid double refactoring
 3. Generic Core: ProductMatch, Pricing models stay ERP-agnostic
 4. Optional Database: ERPs can use DB or API-only
 5. Test Everything: Add tests alongside refactoring
 6. One ERP per Deployment: Simpler config-based selection