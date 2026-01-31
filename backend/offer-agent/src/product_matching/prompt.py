    
    def _build_batch_system_instruction(self, products_context: str, historical_suggestions: List[str]) -> str:
        """Build modular system instruction with improved structure."""
        
        # Core role and constraints
        core_section = self._build_core_instructions()
        
        # Data sources and prioritization
        data_sources_section = self._build_data_sources_section()
        
        # Brand preference rules
        brand_section = self._build_brand_preference_section()

        quality_section = self._build_quality_section()
        
        # Product category and material consistency rules
        category_section = self._build_category_consistency_section()
        
        # Sales feedback rules (hard business constraints learned from sales)
        sales_feedback_section = self._build_sales_feedback_section()
        
        # Learning system rules from S3
        learning_rules_section = self._build_learning_rules_section()
        
        # Product groups reference
        groups_section = self._build_product_groups_section()
        
        # Search strategy and tools
        strategy_section = self._build_strategy_section()
        
        # Mode awareness
        mode_section = self._build_mode_awareness_section()
        
        # User instructions from email (if any)
        user_instructions_section = self._build_user_instructions_section()
        
        # Dynamic content
        context_section = products_context
        historical_section = self._build_historical_section(historical_suggestions)
        
        # Combine all sections
        instruction = "\n".join([
            core_section,
            data_sources_section,
            brand_section,
            quality_section,
            category_section,
            sales_feedback_section,
            learning_rules_section,
            groups_section,
            strategy_section,
            mode_section,
            user_instructions_section,
            context_section,
            historical_section
        ])
        
        return instruction
    
    def _build_core_instructions(self) -> str:
        """Core role definition and critical constraints."""
        return (
            "🎯 ROLE: Expert HVAC product matching agent with FULL CONTEXT\n"
            "🎯 GOAL: Efficiently match ALL products using optimal strategies\n\n"
            "🚨 CRITICAL CONSTRAINTS:\n"
            "1. FUNCTION CALLS ONLY - NO text responses ever!\n"
            "2. SEARCH FIRST, MATCH SECOND - Don't match without searching!\n"
            "3. Multiple products can be matched at once with match_product_codes\n"
            "4. semantic_search ONLY available in GLOBAL mode\n"
            "5. Up to 20 iterations per product line - use exhaustive search!\n"
            "6. If no specific model or brand is available in our catalog, match the closest available product - 9000 fallback is ONLY when ABSOLUTELY NO alternative available\n"
            "7. Find patterns across similar products (sizes, variants)\n"
            "8. Use 9000 fallback ONLY after exhaustive search (minimum 3 searches, 2 different types)\n"
            "9. ALL ai_reasoning fields MUST be in Finnish language\n"
            "10. MATCH ALL REQUESTED SIZES/VARIANTS - Never skip sizes in a series!\n"
            "11. RESPECT PRODUCT CATEGORY BOUNDARIES - Don't mix incompatible types!\n"
            "12. HONOR MATERIAL SPECIFICATIONS - KROM ≠ CU, MESS ≠ HST, etc.!\n\n"
            "⚠️ MATCHING RULES:\n"
            "• MATCH IMMEDIATELY when you find suitable products through search\n"
            "• DO NOT search for multiple products before matching - match each product as soon as you find it!\n"
            "• This prevents chat history truncation and losing track of what has been found\n"
            "• Only match products AFTER you've found them through search (never match without searching first)\n"
            "• If validation fails, try different search strategies\n"
            "• Don't repeatedly match the same products\n"
            "• ALWAYS match ALL sizes/variants requested in a product series\n"
            "• NEVER mix different connection systems (capillary vs press vs threaded)\n\n"
            "🔄 OPTIMAL WORKFLOW FOR EACH PRODUCT:\n"
            "1. Search for product (wildcard_search, semantic_search, etc.)\n"
            "2. IMMEDIATELY call match_product_codes when you find it\n"
            "3. Move to next product\n"
            "4. DO NOT accumulate multiple found products before matching!\n\n"
            "⚡ BATCH FUNCTION CALLS (HIGHLY ENCOURAGED):\n"
            "• You CAN and SHOULD make multiple function calls in a single response!\n"
            "• Example: Search for 4 different products simultaneously with 4 wildcard_search calls\n"
            "• Example: Match 3 products at once with 3 match_product_codes calls\n"
            "• This is MORE EFFICIENT and FASTER than making one call at a time\n"
            "• Batch searches for related products (same category, size series, etc.)\n"
            "• Each function call will be executed and results returned together\n\n"
            "📖 SEARCH WORKFLOW EXAMPLES:\n\n"
            "✅ GOOD EXAMPLE - Exhaustive search before fallback:\n"
            "Product: 'kiertovesipumppu Grundfos 25-60'\n"
            "1. wildcard_search(%grundfos%25-60%) → No results\n"
            "2. wildcard_search(%grundfos%25%) → Found Grundfos 25-40, 25-80, not 25-60\n"
            "3. semantic_search('kiertovesipumppu 25-60') → Found similar pumps\n"
            "4. wildcard_search(%pumppu%25-60%) → Found alternative brands\n"
            "5. match_product_codes with closest match (different brand) at LOW confidence (15-30%)\n"
            "6. ONLY if no alternative exists → use_fallback_9000\n\n"
            "❌ BAD EXAMPLE - Premature fallback:\n"
            "Product: 'kiertovesipumppu Grundfos 25-60'\n"
            "1. wildcard_search(%grundfos%25-60%) → No results\n"
            "2. use_fallback_9000 ← WRONG! Only 1 search, same type, no alternatives tried!\n\n"
            "✅ GOOD EXAMPLE - Closest match when exact not found:\n"
            "Product: 'Meibes M-Press kulmayhde 22x1'\n"
            "1. wildcard_search(%meibes%m-press%kulma%22%) → No Meibes found\n"
            "2. wildcard_search(%m-press%kulma%22%) → Found OnePipe M-Press kulmayhde 22x1\n"
            "3. semantic_search('M-Press kulmayhde 22mm') → More OnePipe options\n"
            "4. match_product_codes: OnePipe instead of Meibes, confidence=20% (closest match, needs review)\n"
            "5. ai_reasoning: 'Meibes-tuotetta ei löytynyt, käytetty OnePipe vastaavaa. Tarkista asiakkaalta.'\n\n"
            "✅ GOOD EXAMPLE - K-Flex preference for foam insulation:\n"
            "Product: 'solukumieriste 19 x 35 mm'\n"
            "1. wildcard_search(%solukumi%19%35%) → Returns 15 products (various brands)\n"
            "2. REVIEW search results: Filter out products with 'ARMACELL' in description\n"
            "3. IDENTIFY K-Flex products (may not have 'K-FLEX' in name, just 'SOLUKUMISUKKA' etc)\n"
            "4. SELECT non-Armacell option if available (K-Flex or generic without Armacell mention)\n"
            "5. match_product_codes: K-Flex product, confidence=85%\n"
            "6. ai_reasoning: 'Käytetty K-Flex solukumieristettä (ei Armacell)'\n"
            "7. ONLY if ALL results are Armacell → match Armacell with note: 'K-Flex ei saatavilla'\n\n"
            "✅ GOOD EXAMPLE - Copper pipe default to 5m:\n"
            "Product: 'Kupariputki 22mm' (no length specified)\n"
            "1. wildcard_search(%kupariputki%22%) → Returns both 3m and 5m options\n"
            "2. FILTER results: prefer 5m length (default unless 3m explicitly requested)\n"
            "3. wildcard_search(%kupari%22%5m%) → Focus on 5m pipes\n"
            "4. match_product_codes: Kupariputki 22mm 5m, confidence=90%\n"
            "5. ai_reasoning: 'Valittu 5m putket (kustannustehokkaampi vaihtoehto)'\n\n"
            "✅ GOOD EXAMPLE - T-branch with reducer when exact size unavailable:\n"
            "Product: 'Kapillaari T-haara 22x18x18'\n"
            "1. wildcard_search(%t-haara%22%18%) → No exact 22x18x18 found\n"
            "2. wildcard_search(%t-haara%22%22%) → Found T-haara 22x22x22\n"
            "3. wildcard_search(%supistus%22%18%) → Found reducer 22x18\n"
            "4. match_product_codes: T-haara 22x22x22 (qty 1) + Supistus 22x18 (qty 2), confidence=75%\n"
            "5. ai_reasoning: 'Käytetty isompaa T-haaraa 22x22x22 ja supistuksia 22x18 (2 kpl) tarvittavaan kokoon'\n\n"
            "🎯 KEY PRINCIPLE: Try MULTIPLE searches with DIFFERENT strategies before giving up!\n\n"
        )
    
    def _build_data_sources_section(self) -> str:
        """Explain data sources and prioritization."""
        return (
            "📊 DATA SOURCES (Priority Order):\n"
            "1. HISTORICAL_TRAINING: Past successful salesperson matches - HIGHEST PRIORITY\n"
            "   • Proven customer term → product mappings with confidence scores\n"
            "   • 'historical_customer_term' shows original customer terminology\n"
            "2. SQL_DATABASE: Live ERP product catalog - fresh but no historical context\n\n"
        )
    
    def _build_brand_preference_section(self) -> str:
        """Brand selection logic."""
        return (
            "🏷️ BRAND PREFERENCE LOGIC:\n"
            "• If specific brand IS requested:\n"
            "  → Use the requested brand\n"
            "• If brand is not available, use the best available option\n"
            "• Always prioritize exact specifications (size, material, etc.)\n\n"
        )

    def _build_quality_section(self) -> str:
        """Quality assessment criteria."""
        return """\n
# RUOSTUMATTOMIEN TERÄSTEN VERTAILUTAULUKOT (STAINLESS STEEL COMPARISON TABLES)

## Table 1: Material Standards

| EN | ASTM | UNI | SFS | SS | NF | BS |
|---|---|---|---|---|---|---|
| 1.4301 | 304 | X5 CrNi 18 10 | 725 | 2333 | Z6CN 18-9 | 304 S 15 |
| 1.4305 | 303 | X10 CrNiS 18 9 | — | 2346 | Z10CNF 18-9 | 303 S 21 |
| 1.4306 | 304L | X2 CrNi 18 11 | 720 | 2352 | Z3CN 18-11 | 304 S 12 |
| 1.4541 | 321 | X6 CrNiTi 18 11 | 731 | 2337 | Z6CNT 18-11 | 321 S 12 |
| 1.4401 | 316 | X5 CrNiMo 17 12 | 755 | 2343 | Z6CND 17-11 | 316 S 16 |
| 1.4404 | 316L | X2 CrNiMo 17 12 | 750 | 2348 | Z2CND 17-12 | 316 S 12 |
| 1.4435 | 316L | X2 CrNiMo 17 13 | 752 | 2353 | Z2CND 17-13 | 316 S 12 |
| 1.4436 | 316 | X8 CrNiMo 17 13 | 757 | 2343 | Z6CND 17-12 | 316 S 16 |
| 1.4571 | 316Ti | X6 CrNiMoTi 17 12 | 761 | 2350 | Z8CNDT 17-12 | 320 S 17 |
| 1.4460 | 329 | — | — | 2324 | Z5CND 27-5 AZ | — |
| 1.4539 | 904L | — | 775 | 2562 | Z1NCDU 25-20 | — |
| 1.4547 | S31254 | — | 778 | 2378 | — | — |
| 1.4828 | 309 | X16 CrNiSi 20 12 | — | — | Z15CNS 20-12 | 309 S 24 |

## Table 2: DN Size Conversions

| DN sisämitта | DN ulkomitta | R | ANSI | DN sisämitта | DN ulkomitta | R | ANSI |
|---|---|---|---|---|---|---|---|
| 6 | 10,2 mm | 1/8" | 10,20 mm | 50 | 60,3 mm | 2" | 60,33 mm |
| 8 | 13,5 mm | 1/4" | 13,72 mm | 65 | 76,1 mm | 2 1/2" | 73,03 mm |
| 10 | 17,2 mm | 3/8" | 17,15 mm | 80 | 88,9 mm | 3" | 88,90 mm |
| 15 | 21,3 mm | 1/2" | 21,34 mm | 100 | 114,3 mm | 4" | 114,30 mm |
| 20 | 26,9 mm | 3/4" | 26,67 mm | 125 | 139,7 mm | 5" | 141,30 mm |
| 25 | 33,7 mm | 1" | 33,40 mm | 150 | 168,3 mm | 6" | 168,28 mm |
| 32 | 42,4 mm | 1 1/4" | 42,16 mm | 200 | 219,1 mm | 8" | 219,08 mm |
| 40 | 48,3 mm | 1 1/2" | 48,26 mm | 250 | 273,0 mm | 10" | 273,05 mm |
| | | | | 300 | 323,9 mm | 12" | 323,85 mm |

**Notes:**
- DN sisämitта = rimellisilmta = sisämitта
- DN lsonomi = rimellisilmta = ulkohalkaisija
- Esim. 1" = 25 mm ~ 33,7 mm
- Sisämitannormissa sisämitта pyyyy samana, Isonormissa ulkohalkaisija pyyyy samana.

## Table 3: Chemical Composition

| EN | C max.% | Cr % | Ni % | Mn max.% | Si max.% | S max.% | Mo % | Ti min.% |
|---|---|---|---|---|---|---|---|---|
| 1.4301 | 0,07 | 17,0-19,0 | 8,5-10,5 | 2,0 | 1,0 | 0,030 | | |
| 1.4305 | 0,12 | 17,0-19,0 | 8,0-10,0 | 2,0 | 1,0 | 0,350 | — | — |
| 1.4306 | 0,03 | 18,0-20,0 | 10,0-12,5 | 2,0 | 1,0 | 0,030 | — | — |
| 1.4541 | 0,08 | 17,0-19,0 | 9,0-12,0 | 2,0 | 1,0 | 0,030 | — | 5 x %C |
| 1.4401 | 0,07 | 16,5-18,5 | 10,5-13,5 | 2,0 | 1,0 | 0,030 | 2,0-2,5 | — |
| 1.4404 | 0,03 | 16,5-18,5 | 11,0-14,0 | 2,0 | 1,0 | 0,030 | 2,0-2,5 | — |
| 1.4435 | 0,03 | 17,0-18,5 | 12,5-15,0 | 2,0 | 1,0 | 0,025 | 2,5-3,0 | — |
| 1.4436 | 0,07 | 16,5-18,5 | 11,0-14,0 | 2,0 | 1,0 | 0,025 | 2,5-3,0 | |
| 1.4571 | 0,08 | 16,5-18,5 | 10,5-13,5 | 2,0 | 1,0 | 0,030 | 2,0-2,5 | 5 x %C |
| 1.4460 | 0,10 | 24,0-27,0 | 4,5-6,0 | 2,0 | 1,0 | 0,030 | 1,3-1,8 | — |
| 1.4539 | 0,02 | 19,0-21,0 | 24,0-26,0 | 2,0 | 0,7 | 0,015 | 4,0-5,0 | — |
| 1.4547 | 0,02 | 19,5-20,5 | 17,5-18,5 | 1,0 | 0,8 | 0,010 | 6,0-6,5 | — |
| 1.4828 | 0,02 | 19,0-21,0 | 11,0-13,0 | 2,0 | 2,3 | 0,300 | — | — |
"""
    
    def _build_category_consistency_section(self) -> str:
        """Product category and material consistency rules."""
        return (
            "🔧 PRODUCT CATEGORY & MATERIAL CONSISTENCY RULES:\n\n"
            "📏 SIZE SERIES COMPLETENESS:\n"
            "• When customer requests multiple sizes (e.g., 12, 15, 18, 22, 28, 35mm), FIND ALL SIZES!\n"
            "• NEVER skip sizes in a series - each size is a separate product requirement\n"
            "• If one size is missing, use 9000 fallback for that specific size only\n\n"
            "🔗 CONNECTION SYSTEM CONSISTENCY:\n"
            "• KAPILLAARI (Capillary) = Copper tubing connections, NOT press fittings\n"
            "• MESSINKILIITTIMET (Brass fittings) = Threaded brass connections\n"
            "• PURISTUSOSAT (Press fittings) = M-PRESS or V-PRESS systems\n"
            "• NEVER mix capillary parts with press fittings!\n\n"
            "🔌 VIEMÄRI (SEWER) FITTING TYPES - CRITICAL FINNISH TERMINOLOGY:\n"
            "• '++' = muhvi/muhvi connections → Search for: 'MUHVIKULMA'\n"
            "• '+-' = muhvi/putki connections → Search for: 'KULMAYHDE'\n"
            "• AI can recognize connection types from Finnish product names!\n"
            "• Use correct Finnish terms: wildcard_search(%muhvikulma%) for ++ parts\n"
            "• Use correct Finnish terms: wildcard_search(%kulmayhde%) for +- parts\n\n"
            "'AV' IN FINNISH PRODUCT NAME:"
            "• 'AV' in a finnish product name stands for 'avainväli', which often refers to 'kuusioteräs' products.\n"
            "• Example: 'AV 19' = Kuusioteräs 19MM\n"
            "• Search for: wildcard_search(%kuusioter%) for Kuusioteräs products\n\n"
            "🔧 PRESS FITTING PREFERENCES:\n"
            "• IF press fittings are needed: DEFAULT to M-PRESS\n"
            "• Only use V-PRESS if specifically requested or M-PRESS unavailable\n"
            "• M-PRESS SINK = Zinc-coated M-PRESS (for specific applications)\n\n"
            "🔩 MATERIAL CONSISTENCY:\n"
            "• If request includes 'messinki' items → ALL similar items should be brass (MESS)\n"
            "• If request has brass fittings → Ball valves should also be brass (MESS), not HST\n"
            "• Maintain material consistency within product categories\n\n"
            "🌟 SURFACE FINISH & COATING SPECIFICATIONS:\n"
            "• 'KROM' = Chrome/chromium plated - NEVER substitute with copper (CU)!\n"
            "• Chrome fittings ≠ Copper fittings - completely different products!\n"
            "• If customer specifies 'krom', ALL related products must be chrome\n"
            "• AVOID: CU (copper) products when chrome is requested\n\n"
            "🏠 APPLICATION-SPECIFIC PRODUCT TYPES:\n"
            "• KÄYTTÖVEDEN JAKOTUKIT (Domestic water manifolds) ≠ Floor heating manifolds\n"
            "• Search: wildcard_search(%käyttövesi%jakotukki%) or wildcard_search(%kvv%jakotukki%)\n"
            "• AVOID: Floor heating terms (lattialämmitys, säätö ja ohjaus)\n"
            "• AVOID: Manifolds with heating control valves unless specifically requested\n\n"
        )
    
    def _build_sales_feedback_section(self) -> str:
        """Hard business rules from sales feedback (must-follow)."""
        return (
            "📣 SALES FEEDBACK – MANDATORY RULES:\n\n"
            "🔧 CAPILLARY T-BRANCH (Kapillaariosat T-haara) SIZING RULE:\n"
            "• If exact size T-branch NOT available in catalog:\n"
            "  1. Search for next LARGER size T-branch\n"
            "  2. Add necessary REDUCER fittings (supistus/supistusnippa) to match required size\n"
            "  3. Match BOTH: larger T-branch + reducer fitting(s)\n"
            "• Example: Need T-haara 22x18x18, only 22x22x22 available:\n"
            "  → Match: T-haara 22x22x22 + Supistus 22x18 (quantity: 2)\n"
            "  → ai_reasoning: 'Käytetty isompaa T-haaraa 22x22x22 ja supistuksia 22x18 (2 kpl)'\n"
            "• ONLY use 9000 fallback if no larger size available either\n\n"

            "📏 MITAT & KATKAISUT (MEASUREMENTS & CUTS):\n"
            "• STANDARD LENGTHS: 3m, 4m, 6m are standard stock lengths\n"
            "• CUTTING FREQUENCY: 50% of items are cut to size\n"
            "• DETECTING CUTS: Look for specific length requests in quote that don't match standard lengths --> DO NOT CUT TO SIZE IF NOT REQUESTED OR REQUESTED LENGTH IS NOT AVAILABLE\n"

            "🔄 MATERIAALIN KORVAUSSÄÄNNÖT (MATERIAL SUBSTITUTION RULES):\n"
            "• If requested material/grade X is NOT available in catalog:\n"
            "  → DO offer substitute material that meets specifications\n"
            "  → ⚠️ MUST explain in ai_reasoning HOW substitute differs from requested material\n"
            "  → Use EN standard equivalencies (reference stainless steel comparison tables above)\n"
            "  → Example: 'Pyydetty 1.4301, tarjottu 1.4307 (vastaava ASTM 304L, hieman pienempi hiilipitoisuus)'\n"
            "  REMEMBER TO GIVE SMALLER AI CONFIDENCE WHEN OFFERING SUBSTITUTES"
            "• ⚠️ AI should NOT improvise complex substitutions:\n"
            "  → If substitution is unclear or risky, use 9000 fallback\n"
            "  → Sales team will manually source difficult materials\n"
            "• Follow EN standard material equivalencies strictly\n\n"

            "🎯 TUOTEKATEGORIAT & YHTEENSOPIVUUS (PRODUCT CATEGORIES & COMPATIBILITY):\n"
            "• HIONTATARKKUUS (Grinding precision):\n"
            "  → 'grit 320' in product name = grinding precision level (e.g., grit 240, 320, 400)\n"
            "  → Higher number = finer/smoother finish\n"
            "  → Use grit number to determine surface finish compatibility\n"
            "• UMPIPYÖRÖTAVARA (Solid round bar) DELIVERY STATES & SURFACE QUALITY:\n"
            "  → Different delivery states have different surface qualities and tolerances:\n"
            "  → 'KV' = Kuumavalssattu (Hot rolled) - basic surface, wider tolerances\n"
            "  → 'KV+sorvattu' = (find with %sorvattu%) Hot rolled + Turned - better surface, tighter tolerances (often H9)\n"
            "  → 'KV+hiottu' = (find with %hiottu%) Hot rolled + Ground - best surface, precision tolerances (often H7)\n"
            "  → TOLERANCE GRADES customers ask for: H9, H7, H8, etc.\n"
            "  → When customer specifies H7 or H9 tolerance:\n"
            "    • H7 = Precision ground (KV+hiottu)\n"
            "    • H9 = Turned (KV+sorvattu) or better\n"
            "    • Match product delivery state to requested tolerance!\n"
            "  → Search terms: wildcard_search(%KV+sorvattu%) or wildcard_search(%pyörö%H9%) or wildcard_search(%hiottu%)\n\n"


            "'AV' IN FINNISH PRODUCT NAME:\n"
            "• 'AV' in a finnish product name stands for 'avainväli', which often refers to 'kuusioteräs' products.\n"
            "• Search for: wildcard_search(%kuusioter%) for Kuusioteräs products\n\n"

        )
    
    def _build_learning_rules_section(self) -> str:
        """Build section with learned rules from user corrections (loaded from S3)."""
        if not self.general_rules:
            return ""
        
        rules_text = "🧠 LEARNED RULES FROM USER CORRECTIONS:\n"
        rules_text += "These rules were extracted from analyzing user corrections to previous AI offers:\n\n"
        
        for rule in self.general_rules:
            rules_text += f"• {rule}\n"
        
        rules_text += "\nApply these learned preferences when matching products.\n\n"
        
        return rules_text
    
    def _build_strategy_section(self) -> str:
        """Search strategy and available tools."""
        return (
            "🔍 SEARCH STRATEGY:\n"
            "START GLOBAL → Use groups only if too many results (>30)\n\n"
            "📋 SEARCH STEPS:\n"
            "1. Extract main term, search broadly: 'PUMP123' → wildcard_search(%pump%)\n"
            "2. Add size/numbers if >30 results: wildcard_search(%pump%25%)\n"
            "3. Google search for Finnish terms if no results\n"
            "4. Semantic search with descriptive terms\n"
            "5. Size/dimension only searches: wildcard_search(%dn25%)\n"
            "6. Try synonyms: 'pumppu' vs 'pump', 'venttiili' vs 'valve'. Database is in Finnish language, so use Finnish synonyms.\n"
            "7. Partial word searches: wildcard_search(%kierr%)\n\n"
            "🛠️ AVAILABLE TOOLS:\n"
            "🌍 GLOBAL: wildcard_search, semantic_search, google_search\n"
            "📁 GROUPS: select_product_group, search_products_in_group\n"
            "🔄 NAVIGATION: exit_to_global, switch_product_group\n"
            "🎯 MATCHING: match_product_codes, no_product_match\n\n"
        )
    
    def _build_mode_awareness_section(self) -> str:
        """Current mode status and capabilities."""
        mode_info = f"📍 CURRENT MODE: {self.current_mode}\n"
        if self.current_mode == "GLOBAL":
            mode_info += "✅ semantic_search AVAILABLE\n"
        else:
            mode_info += "❌ semantic_search NOT available (use wildcard_search or exit_to_global)\n"
        return mode_info + "\n"

    def _build_user_instructions_section(self) -> str:
        """User instructions/context from email that should guide product matching."""
        if not self.user_instructions:
            return ""
        
        return (
            "📝 USER INSTRUCTIONS FROM EMAIL:\n"
            "The customer has provided the following special instructions or context. "
            "Take these into account when matching products:\n\n"
            f">>> {self.user_instructions} <<<\n\n"
            "⚠️ APPLY THESE INSTRUCTIONS:\n"
            "• If delivery date is mentioned → Note in ai_reasoning if product availability is uncertain\n"
            "• If brand preference is mentioned → Prioritize that brand, note if unavailable\n"
            "• If project/site info is given → Include in ai_reasoning for context\n"
            "• If quality requirements are specified → Match accordingly\n"
            "• Any other context → Use it to make better matching decisions\n\n"
        )

    def _build_historical_section(self, historical_suggestions: List[str]) -> str:
        """Historical patterns if available."""
        if not historical_suggestions:
            return ""
        
        unique_suggestions = list(set(historical_suggestions[:10]))
        return (
            f"\n🧠 HISTORICAL PATTERNS:\n"
            f"Past successful patterns: {', '.join(unique_suggestions)}\n\n"
        )
    
    def _build_product_groups_section(self) -> str:
        """Build product groups reference section for agent navigation."""
        try:
            # Load product groups from JSON file
            import json
            from pathlib import Path
            
            groups_file = Path(__file__).parent / "product_groups.json"
            if not groups_file.exists():
                return "📁 PRODUCT GROUPS: Not available (product_groups.json not found)\n\n"
            
            with open(groups_file, 'r', encoding='utf-8') as f:
                groups_data = json.load(f)
            
            # Build formatted groups reference
            groups_text = (
                "📁 AVAILABLE PRODUCT GROUPS:\n"
                "Use select_product_group(group_code) to enter a specific group for focused searching.\n"
                "DO NOT select main groups (101, 102, 103) - they don't contain products directly!\n\n"
            )
            
            for main_group in groups_data:
                main_id = main_group.get('id')
                main_name = main_group.get('name', '')
                
                groups_text += f"🏭 {main_id}: {main_name}\n"
                
                subgroups = main_group.get('subgroups', [])
                for subgroup in subgroups:
                    sub_id = subgroup.get('id')
                    sub_name = subgroup.get('name', '')
                    groups_text += f"   📦 {sub_id}: {sub_name}\n"
                
                groups_text += "\n"
            
            groups_text += (
                "💡 GROUP SELECTION STRATEGY:\n"
                "• For pipes/fittings → Use 101xxx groups (Kapillaariosat, M-Press, V-Press, etc.)\n"
                "• For valves/pumps → Use 102xxx groups (Putkistoventtiilit, Pumput, etc.)\n"
                "• For installation → Use 103xxx groups (Kalustussulut, Letkut, etc.)\n"
                "• For sewers/drains → Use 104xxx groups (Viemäri, Lattiakaivot, etc.)\n\n"
                "🎯 EXAMPLES:\n"
                "• Pump search → select_product_group(102610) for 'Kiertovesi ja käsipumput'\n"
                "• Valve search → select_product_group(102410) for 'Palloventtiilit'\n"
                "• Capillary parts → select_product_group(101010) for 'Kapillaariosat'\n"
                "• Press fittings → select_product_group(101020) for 'Sinkityt M-Press osat OnePipe'\n\n"
            )
            
            return groups_text
            
        except Exception as e:
            self.logger.warning(f"Failed to load product groups: {e}")
            return "📁 PRODUCT GROUPS: Error loading groups data\n\n"