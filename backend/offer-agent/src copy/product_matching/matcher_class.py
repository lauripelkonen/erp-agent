"""
Product identification and matching system using RAG pipeline with agentic search fallback.
Combines vector similarity search with intelligent query strategies for optimal product matching.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import uuid

import pandas as pd
import numpy as np
import openai

from src.config.settings import get_settings
from src.utils.logger import get_logger, get_audit_logger
from src.utils.exceptions import ProductNotFoundError, ExternalServiceError
from src.embeddings import ProductEmbeddingService


@dataclass
class ProductMatch:
    """Represents a matched product with confidence scoring."""
    product_code: str
    product_name: str
    description: str = ""
    unit: str = "KPL"
    price: float = 0.0
    product_group: str = ""
    confidence_score: float = 0.0
    match_method: str = "unknown"
    similarity_score: float = 0.0
    search_query: str = ""
    quantity_requested: int = 1
    match_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.match_details is None:
            self.match_details = {}

