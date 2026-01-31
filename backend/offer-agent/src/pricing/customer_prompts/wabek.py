from typing import List

def _build_batch_system_instruction(self, products_context: str, historical_suggestions: List[str]) -> str:
    """Build modular system instruction with improved structure."""
    
    # Core role and constraints
    core_section = self._build_core_instructions()
    
    # Data sources and prioritization
    data_sources_section = self._build_data_sources_section()
    
    # Brand preference rules
    brand_section = self._build_brand_preference_section()

    
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
        "• Only match products AFTER you've found them through search\n"
        "• If validation fails, try different search strategies\n"
        "• Don't repeatedly match the same products\n"
        "• ALWAYS match ALL sizes/variants requested in a product series\n"
        "• NEVER mix different connection systems (capillary vs press vs threaded)\n\n"
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
        "• FOAM INSULATION PRODUCTS: K-Flex > Other brands > Armacell (last resort)\n"
        "  → ALWAYS prefer K-Flex for solukumieriste/solukumisukat/solukumimatto\n"
        "  → Use Armacell ONLY if K-Flex not available\n"
        "• PIPES/FITTINGS: If NO specific brand requested AND multiple options:\n"
        "  → DEFAULT to OnePipe brand (our own, cost-effective)\n"
        "• If specific brand IS requested:\n"
        "  → Use the requested brand\n"
        "• If brand is not available, use the best available option\n"
        "• Always prioritize exact specifications (size, material, etc.)\n\n"
    )


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
        "🔧 PRESS FITTING PREFERENCES:\n"
        "• IF press fittings are needed: DEFAULT to M-PRESS (OnePipe preferred)\n"
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
        "🎛️ VALVE TYPE PREFERENCES:\n"
        "• LSV (linjasäätöventtiili) → Prefer OnePipe line regulators over STAD types\n"
        "• Search for OnePipe LSV/linjasäätö products first\n"
        "• Only use STAD if OnePipe alternatives not available\n\n"
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
        "🔴 CRITICAL: K-FLEX vs ARMACELL FOAM INSULATION POLICY:\n"
        "• ALL foam insulation products (solukumieriste, solukumisukat, solukumimatto) MUST DEFAULT to K-FLEX brand\n"
        "• ONLY use Armacell if K-Flex alternative is NOT AVAILABLE in catalog\n"
        "• This applies to ALL sizes and types: 13mm, 19mm, 25mm, 35mm, etc.\n"
        "• K-Flex products may NOT have 'K-FLEX' explicitly in product name/description\n"
        "• Armacell products typically show 'ARMACELL' or 'ARMACELL TT' in description\n\n"
        "🔍 HOW TO IDENTIFY K-FLEX vs ARMACELL:\n"
        "• Search: wildcard_search(%solukumi%19%35%) returns multiple brands\n"
        "• CHECK product descriptions and supplier info in search results\n"
        "• FILTER OUT products with 'ARMACELL' in description if K-Flex alternatives exist\n"
        "• K-Flex products may appear as generic 'SOLUKUMISUKKA' without brand mention\n"
        "• When in doubt: prefer products WITHOUT 'Armacell' mention over those with it\n"
        "• If only Armacell available: match it but note in ai_reasoning: 'K-Flex ei saatavilla, käytetty Armacell'\n\n"
        "📏 SPECIFIC SIZE CORRECTIONS:\n"
        "• Solukumieriste 168×19 mm: Use 170×19 mm (our standard size). Always prefer K-Flex.\n"
        "• If customer requests non-standard size, offer closest K-Flex size with note in ai_reasoning\n\n"
        "🌬️ OTHER MANDATORY RULES:\n\n"
        "🔴 COPPER PIPES (Cu-putket) LENGTH RULE:\n"
        "• DEFAULT: ALWAYS use 5m copper pipes (more cost-effective per meter)\n"
        "• ONLY use 3m pipes if EXPLICITLY stated '3m' or '3 metriä' in customer request\n"
        "• If no length mentioned → DEFAULT to 5m\n"
        "• Search examples: wildcard_search(%cu%putki%5m%) or wildcard_search(%kupari%putki%5%)\n"
        "• Reasoning when 5m selected: 'Valittu 5m putket (kustannustehokkaampi vaihtoehto)'\n\n"
        "🔧 CAPILLARY T-BRANCH (Kapillaariosat T-haara) SIZING RULE:\n"
        "• If exact size T-branch NOT available in catalog:\n"
        "  1. Search for next LARGER size T-branch\n"
        "  2. Add necessary REDUCER fittings (supistus/supistusnippa) to match required size\n"
        "  3. Match BOTH: larger T-branch + reducer fitting(s)\n"
        "• Example: Need T-haara 22x18x18, only 22x22x22 available:\n"
        "  → Match: T-haara 22x22x22 + Supistus 22x18 (quantity: 2)\n"
        "  → ai_reasoning: 'Käytetty isompaa T-haaraa 22x22x22 ja supistuksia 22x18 (2 kpl)'\n"
        "• ONLY use 9000 fallback if no larger size available either\n\n"
        "🌬️ VENTILATION DUCTS & OTHER RULES:\n"
        "• Kierresaumakanavat: DEFAULT length is 3 m. Use 6 m ONLY if explicitly requested.\n"
        "• IV muunto‑osat 250×160 and 160×125: use MUUNTOLIITIN OSALLE. Do not use 'muuntoyhde epäk kan/kan' unless explicitly requested as epäkeskona.\n"
        "• IV T‑haarat: If the request says only 'T‑haara', it means a normal IV T‑haara without insulation (galvanized steel). 'Insuplast T‑haara' is just insulation around a standard T‑haara—use it ONLY when 'insuplast' is explicitly mentioned.\n\n"
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