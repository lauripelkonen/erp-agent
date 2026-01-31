"""
AI-based extraction services for offer automation.

These services extract information from emails using AI (Gemini).
They are completely ERP-independent - pure text/content extraction.
"""

from src.extraction.company_extractor import CompanyExtractor

__all__ = [
    "CompanyExtractor",
]
