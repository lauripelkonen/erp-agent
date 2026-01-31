# Gemini 2.0 Search Grounding Integration

## Overview

The offer automation system now integrates **Gemini 2.0 Search Grounding** for intelligent web searches, replacing traditional web scraping with Google's built-in search capabilities.

## Features

### 🔍 **Intelligent Company Search**
- Uses Gemini 2.0 Flash with Google Search tool
- Extracts structured company information from search results
- Supports Finnish and international companies
- Provides grounding metadata for transparency

### 🎯 **Smart Information Extraction**
- **Company Names**: Including Finnish suffixes (Oy, Oyj, Ltd, AB)
- **Contact Information**: Email addresses, phone numbers, addresses
- **Business Details**: Industry classification, location data
- **Confidence Scoring**: Weighted matching for accuracy

### 🚀 **Performance Benefits**
- **No Web Scraping**: Eliminates brittle HTML parsing
- **Real-time Results**: Google's fresh search index
- **Rate Limit Friendly**: Built-in throttling and retry logic
- **Grounding Metadata**: Transparent source attribution

## Configuration

### Environment Variables

```bash
# Enable/disable Search Grounding
ENABLE_SEARCH_GROUNDING=true

# Gemini API configuration
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-2.0-flash
```

### Required Dependencies

```bash
pip install google-generativeai>=0.7.0
```

## Usage

### Customer Lookup Integration

The Search Grounding automatically integrates with the customer lookup pipeline:

```python
from customer.lookup import CustomerLookup

# Search Grounding is used as a fallback strategy
lookup = CustomerLookup()
customer = await lookup.find_customer({
    'email_address': 'contact@example.com',
    'search_terms': ['Example Company', 'Esimerkki Oy']
})
```

### Direct Search Usage

```python
from customer.gemini_search import get_web_search_client

search_client = get_web_search_client()
result = await search_client.search_company("Nokia", location="Finland")

if result:
    print(f"Company: {result['company_name']}")
    print(f"Email: {result.get('email', 'N/A')}")
    print(f"Phone: {result.get('phone', 'N/A')}")
```

## Search Process

### 1. **Query Construction**
```
"{search_term} company {location} contact information business"
```

### 2. **Gemini 2.0 Search Execution**
- Uses `GenerateContentConfig` with `GoogleSearch` tool
- Low temperature (0.1) for factual information
- Structured response format

### 3. **Information Extraction**
- **Company Name Patterns**: Regex matching with Finnish suffixes
- **Contact Extraction**: Email/phone pattern recognition
- **Business Classification**: Industry keyword matching
- **Location Detection**: Finnish city recognition

### 4. **Lemonsoft Integration**
- Search results matched against existing customers
- Confidence scoring with search-assisted weighting
- Detailed match metadata for audit trails

## Example Search Response

```json
{
  "company_name": "Nokia Oyj",
  "email": "info@nokia.com",
  "phone": "+358 10 44 88 000",
  "address": "Karaportti 3, 02610 Espoo, Finland",
  "industry": "Technology",
  "location": "Espoo",
  "source": "gemini_search_grounding",
  "search_term": "Nokia"
}
```

## Fallback Strategy

The system gracefully handles various scenarios:

### ✅ **Search Grounding Available**
- Google GenAI package installed
- Valid Gemini API key configured
- Feature enabled in settings

### 🔄 **Fallback Modes**
- **Package Missing**: Logs warning, continues without web search
- **API Key Invalid**: Validation error with clear instructions  
- **Feature Disabled**: Skips web search step entirely

## Testing

Run the test script to verify functionality:

```bash
python test_gemini_search.py
```

**Expected Output:**
```
🧪 Testing Gemini 2.0 Search Grounding
========================================
✅ Search client initialized successfully
   Gemini API Key: ********************xyz

🔍 Searching for: Nokia
   ✅ Found: Nokia Oyj
   📧 Email: info@nokia.com
   📞 Phone: +358 10 44 88 000
   📍 Location: Espoo
```

## Advantages Over Traditional Web Scraping

| Aspect | Traditional Scraping | Gemini Search Grounding |
|--------|---------------------|------------------------|
| **Reliability** | Brittle HTML parsing | AI-powered extraction |
| **Freshness** | Cache-dependent | Real-time Google index |
| **Rate Limits** | Site-specific blocks | Google-managed throttling |
| **Maintenance** | Requires DOM updates | Self-adapting |
| **Quality** | Raw HTML content | Structured information |
| **Transparency** | Black box results | Grounding metadata |

## Error Handling

The system provides comprehensive error handling:

```python
try:
    result = await search_client.search_company("CompanyName")
except ExternalServiceError as e:
    logger.error(f"Search Grounding failed: {e}")
    # Falls back to other customer identification strategies
```

## Monitoring and Logging

All Search Grounding activities are logged with structured data:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Performing Gemini Search Grounding",
  "search_query": "Nokia company Finland contact information business",
  "response_length": 1234,
  "extraction_success": true
}
```

## Cost Optimization

- **Caching**: Results cached to avoid repeated searches
- **Rate Limiting**: Built-in request throttling
- **Fallback Logic**: Only searches when primary methods fail
- **Query Optimization**: Focused search terms for efficiency

## Security Considerations

- **API Key Protection**: Stored as environment variable
- **Request Validation**: Input sanitization for search terms
- **Error Masking**: Sensitive information not logged
- **Rate Limiting**: Prevents API abuse

---

**Next Steps**: The Search Grounding feature is ready for production use. Monitor search quality and adjust extraction patterns based on real-world usage patterns. 