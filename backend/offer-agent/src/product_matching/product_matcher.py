import logging
import os
import re
import numpy as np  # Added for semantic vector operations
import time
import sys
import http.client
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

import pandas as pd
from google import genai
from openai import OpenAI
from google.genai import types

# Import OpenRouter handler for routing LLM requests
try:
    from .openrouter_handler import get_openrouter_handler, OPENROUTER_MODEL_MAPPING, THINKING_CAPABLE_MODELS
except ImportError:
    get_openrouter_handler = None
    OPENROUTER_MODEL_MAPPING = {}
    THINKING_CAPABLE_MODELS = set()

# Import Grok handler for direct xAI API routing
try:
    from .grok_handler import get_grok_handler, is_grok_model as grok_is_grok_model
except ImportError:
    get_grok_handler = None
    grok_is_grok_model = None

# Check if OpenRouter routing is enabled
USE_OPENROUTER = os.getenv("USE_OPENROUTER") == "True"

# Add both src and emails directories to path for imports (same as main.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lemonsoft.api_client import LemonsoftAPIClient
from src.lemonsoft.database_connection import create_database_client

# Import the new GroupBasedMatcher for primary matching strategy
try:
    from .group_based_matcher import GroupBasedMatcher
except ImportError:
    # Fallback if import fails - log but continue
    GroupBasedMatcher = None
    logging.getLogger(__name__).warning("Could not import GroupBasedMatcher - will use traditional matching only")

# Import the ProductMatchReviewer for post-processing review
try:
    from .product_match_reviewer import ProductMatchReviewer
except ImportError:
    # Fallback if import fails - log but continue
    ProductMatchReviewer = None
    logging.getLogger(__name__).warning("Could not import ProductMatchReviewer - will skip match review")

try:
    from .config import Config
except ImportError:
    # Fallback configuration when config module is not available
    class Config:
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        GEMINI_MODEL = os.getenv('GEMINI_MODEL_ITERATION', 'gemini-2.5-flash')
        OPENAI_RATE_LIMIT_PER_DAY = int(os.getenv('OPENAI_RATE_LIMIT_PER_DAY', '10000'))
        OPENAI_RATE_LIMIT_PER_MINUTE = int(os.getenv('OPENAI_RATE_LIMIT_PER_MINUTE', '500'))
        MAX_EMBEDDING_PRODUCTS = int(os.getenv('MAX_EMBEDDING_PRODUCTS', '0'))
        EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
        SEMANTIC_SIMILARITY_THRESHOLD = float(os.getenv('SEMANTIC_SIMILARITY_THRESHOLD', '0.3'))
        OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
        MAX_CONTEXT_TOKENS = int(os.getenv('MAX_CONTEXT_TOKENS', '6000'))

# Constants for the matcher – kept local to avoid changing global config
_MATCHED_CSV_COLUMNS = [
    "unclear_term",
    "quantity",  # Added quantity column
    "matched_product_code",
    "matched_product_name",
    "email_subject",
    "email_date",
]

class OpenRouterGeminiResponse:
    """Wrapper to convert OpenRouter response to Gemini SDK-like response format.
    
    This allows OpenRouter responses to be used transparently with code
    that expects Gemini SDK response objects.
    """
    
    def __init__(self, openrouter_result: Dict):
        self._result = openrouter_result
        self._text = openrouter_result.get("content", "")
        self._function_calls = openrouter_result.get("function_calls")
        self._thinking_content = openrouter_result.get("thinking_content")
        self._usage = openrouter_result.get("usage", {})
        self._finish_reason = openrouter_result.get("finish_reason")
        
        # Build candidates structure to mimic Gemini response
        self.candidates = [self._build_candidate()]
    
    def _build_candidate(self):
        """Build a candidate object mimicking Gemini SDK structure."""
        return OpenRouterCandidate(
            text=self._text,
            function_calls=self._function_calls,
            thinking_content=self._thinking_content,
            finish_reason=self._finish_reason
        )
    
    @property
    def text(self) -> str:
        """Return the text content from the response."""
        return self._text
    
    @property
    def usage_metadata(self) -> Dict:
        """Return usage metadata."""
        return self._usage


class OpenRouterCandidate:
    """Mimics Gemini SDK candidate structure."""
    
    def __init__(self, text: str, function_calls: Optional[List], thinking_content: Optional[str], finish_reason: Optional[str]):
        # Assistant responses have role "model" in Gemini SDK
        self.content = OpenRouterContent(text, function_calls, thinking_content, role="model")
        self.finish_reason = finish_reason


class OpenRouterContent:
    """Mimics Gemini SDK content structure.
    
    Parts order matches Gemini SDK: function_calls first (for indexed access),
    then text, then thinking content.
    """
    
    def __init__(self, text: str, function_calls: Optional[List], thinking_content: Optional[str], role: str = "model"):
        self.role = role  # "model" for assistant responses, "user" for user messages
        self.parts = []
        
        # Add function calls as parts FIRST (code expects parts[0].function_call)
        if function_calls:
            for fc in function_calls:
                self.parts.append(OpenRouterPart(text=None, function_call=OpenRouterFunctionCall(fc)))
        
        # Add text content part (when there's no function call, this becomes parts[0])
        if text:
            self.parts.append(OpenRouterPart(text=text))
        
        # Add thinking content part at the end (not accessed by index)
        if thinking_content:
            self.parts.append(OpenRouterPart(text=None, thinking_content=thinking_content))
        
        # Ensure at least one empty part
        if not self.parts:
            self.parts.append(OpenRouterPart(text=""))


class OpenRouterPart:
    """Mimics Gemini SDK part structure."""
    
    def __init__(self, text: Optional[str] = None, function_call=None, thinking_content: Optional[str] = None):
        self.text = text
        self.function_call = function_call
        self.thinking_content = thinking_content


class OpenRouterFunctionCall:
    """Mimics Gemini SDK function_call structure."""
    
    def __init__(self, fc_dict: Dict):
        self.name = fc_dict.get("name")
        self.args = fc_dict.get("arguments", {})
        self.id = fc_dict.get("id")
        # Preserve thought_signature for Gemini 3+ compatibility
        self.thought_signature = fc_dict.get("thought_signature")


class ProductMatcher:
    """Matches unclear HVAC product terms to the official product list.

    The matcher uses a three-tier approach:
    1. GroupBasedMatcher: AI agent navigates product groups for structured matching (primary)
    2. Local wildcard / substring search for fast exact matches (fallback)
    3. Agentic search with Gemini for complex fuzzy situations (final fallback)
    """

    def _retry_llm_request(self, request_func, *args, **kwargs):
        """Wrapper to retry LLM requests with exponential backoff and model fallback.
        
        - Routes through OpenRouter if USE_OPENROUTER=True environment variable is set
        - Uses exponential backoff for all retry attempts
        - Falls back to alternative models after 3 failures with primary model
        - Model fallback order: Uses passed model -> gemini-2.5-flash -> gemini-2.0-flash
        - Special handling for thought_signature errors (Gemini 3+ models)
        """
        max_retries = 5
        base_wait = 1  # Base wait time in seconds
        primary_model_failures = 3  # Number of failures before trying fallback models
        
        # Get the initially requested model (preserve it for fallback chain)
        initial_model = kwargs.get('model', Config.GEMINI_MODEL)
        
        # Define model fallback chain - start with requested model
        fallback_models = [
            initial_model,        # Use whatever model was requested
            'gemini-2.5-flash',   # First fallback
            'gemini-2.0-flash',   # Second fallback
        ]
        
        current_model_index = 0
        total_attempts = 0
        thought_signature_errors = 0  # Track thought_signature specific errors
        
        for attempt in range(max_retries):
            total_attempts += 1
            current_model = fallback_models[current_model_index]
            
            # Switch to fallback model if primary has failed enough times
            # BUT don't switch if the error is thought_signature related (it needs fixing, not model change)
            if attempt >= primary_model_failures and current_model_index < len(fallback_models) - 1 and thought_signature_errors == 0:
                current_model_index += 1
                current_model = fallback_models[current_model_index]
                self.logger.info(f"Switching to fallback model: {current_model}")
                
                # Update the model in kwargs if it exists
                if 'model' in kwargs:
                    kwargs['model'] = current_model
                # Also check if model is passed in args (for some API calls)
                args_list = list(args)
                for i, arg in enumerate(args_list):
                    if isinstance(arg, str) and 'gemini' in arg.lower():
                        args_list[i] = current_model
                        args = tuple(args_list)
                        break
            
            try:
                # ============================================================
                # GROK ROUTING: Route directly to xAI API for Grok models
                # This takes priority over OpenRouter for direct xAI access
                # ============================================================
                is_grok_model = self._is_grok_model(current_model) and get_grok_handler

                if is_grok_model:
                    self.logger.info(f"[GROK] Grok model '{current_model}' - routing via xAI API")
                    result = self._call_via_grok(current_model, kwargs)

                    # Log success if we had to use a fallback model
                    if current_model_index > 0:
                        self.logger.info(f"Request succeeded with fallback model via xAI: {current_model}")

                    return result
                # ============================================================
                # END GROK ROUTING
                # ============================================================

                # ============================================================
                # OPENROUTER ROUTING: Route through OpenRouter if:
                # 1. USE_OPENROUTER=True (explicit opt-in for all models), OR
                # 2. Model is NOT a Gemini model (non-Gemini must use OpenRouter)
                # ============================================================
                is_gemini_model = self._is_gemini_model(current_model)
                should_use_openrouter = (USE_OPENROUTER or not is_gemini_model) and get_openrouter_handler

                if should_use_openrouter:
                    if not is_gemini_model:
                        self.logger.info(f"[OPENROUTER] Non-Gemini model '{current_model}' - routing via OpenRouter")
                    result = self._call_via_openrouter(current_model, kwargs)

                    # Log success if we had to use a fallback model
                    if current_model_index > 0:
                        self.logger.info(f"Request succeeded with fallback model via OpenRouter: {current_model}")

                    return result
                # ============================================================
                # END OPENROUTER ROUTING
                # ============================================================

                # Call the wrapped function (direct Gemini SDK call)
                result = request_func(*args, **kwargs)

                # Log success if we had to use a fallback model
                if current_model_index > 0:
                    self.logger.info(f"Request succeeded with fallback model: {fallback_models[current_model_index]}")

                return result
                
            except Exception as e:
                error_str = str(e).lower()
                self.logger.warning(f"LLM request failed with {current_model} (attempt {total_attempts}/{max_retries}): {e}")
                
                # Check if this is a thought_signature error (Gemini 3+ models)
                if "thought_signature" in error_str or "thoughtsignature" in error_str:
                    thought_signature_errors += 1
                    self.logger.warning(f"⚠️ Thought signature error detected ({thought_signature_errors}x). This requires conversation history fix, not model change.")
                
                # Check if it's the last attempt
                if attempt == max_retries - 1:
                    self.logger.error(f"LLM request failed after {max_retries} attempts across {current_model_index + 1} models")
                    raise
                
                # Use exponential backoff for all error types
                wait_time = base_wait * (2 ** (attempt % 3))  # Cap exponential growth by resetting every 3 attempts
                
                # Special handling for specific error types (but still use exponential backoff)
                if "503" in error_str or "service unavailable" in error_str:
                    self.logger.info(f"503 error detected, waiting {wait_time}s (exponential backoff)")
                    
                elif "429" in error_str or "rate limit" in error_str or "quota" in error_str:
                    # Rate limit errors might need longer wait
                    wait_time = max(wait_time, 10)  # Minimum 10 seconds for rate limits
                    self.logger.info(f"Rate limit error detected, waiting {wait_time} seconds (exponential backoff)")
                    
                elif "500" in error_str or "internal" in error_str:
                    self.logger.info(f"Server error detected, waiting {wait_time} seconds (exponential backoff)")
                    
                else:
                    self.logger.info(f"Error occurred, waiting {wait_time} seconds (exponential backoff)")
                
                # Wait before retrying
                time.sleep(wait_time)
        
        # This should never be reached due to the raise in the last attempt
        raise Exception(f"Failed to complete LLM request after {max_retries} attempts")

    def _is_gemini_model(self, model: str) -> bool:
        """Check if the model is a Gemini model (can be handled by direct Gemini SDK).
        
        Non-Gemini models (Claude, Grok, GPT, etc.) must be routed through OpenRouter.
        """
        model_lower = model.lower()
        # Check for Gemini patterns
        if 'gemini' in model_lower:
            return True
        if model_lower.startswith('google/'):
            return True
        # Check if it's in the OpenRouter mapping and maps to a Gemini model
        if model in OPENROUTER_MODEL_MAPPING:
            mapped = OPENROUTER_MODEL_MAPPING[model]
            if 'gemini' in mapped.lower() or mapped.startswith('google/'):
                return True
        return False

    def _is_grok_model(self, model: str) -> bool:
        """Check if the model is a Grok model (should be routed via xAI API).

        Grok models are routed directly through xAI API instead of OpenRouter
        for lower latency and direct access to xAI-specific features.
        """
        if grok_is_grok_model:
            return grok_is_grok_model(model)
        # Fallback pattern matching if grok_handler not imported
        model_lower = model.lower()
        return 'grok' in model_lower

    def _call_via_grok(self, model: str, kwargs: Dict) -> OpenRouterGeminiResponse:
        """Route LLM request through xAI API and return Gemini-compatible response.

        Uses the GrokHandler for direct xAI API access.
        """
        self.logger.info(f"[GROK] Routing request to xAI API for model: {model}")

        grok = get_grok_handler()

        # Extract parameters from kwargs
        contents = kwargs.get('contents')
        config = kwargs.get('config')

        # Convert contents to prompt/messages format
        prompt = None
        messages = None
        system_prompt = None
        tools = None
        temperature = None
        max_tokens = None

        # Handle config (types.GenerateContentConfig)
        if config:
            temperature = getattr(config, 'temperature', None)
            max_tokens = getattr(config, 'max_output_tokens', None)

            # Extract system_instruction from config
            config_system = getattr(config, 'system_instruction', None)
            if config_system:
                if isinstance(config_system, str):
                    system_prompt = config_system
                elif hasattr(config_system, 'parts'):
                    parts = config_system.parts
                    if parts and hasattr(parts[0], 'text'):
                        system_prompt = parts[0].text
                elif hasattr(config_system, 'text'):
                    system_prompt = config_system.text

            # Extract tools from config if present
            config_tools = getattr(config, 'tools', None)
            if config_tools:
                tools = config_tools

        # Convert contents to messages format
        if isinstance(contents, str):
            prompt = contents
        elif isinstance(contents, list):
            messages = contents
        elif hasattr(contents, 'parts'):
            messages = [contents]
        else:
            prompt = str(contents) if contents else ""

        # Call Grok handler (synchronous)
        result = grok.generate(
            model=model,
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.logger.info(f"[GROK] Request completed successfully for model: {model}")

        # Wrap result in Gemini-compatible response object
        return OpenRouterGeminiResponse(result)

    def _call_via_openrouter(self, model: str, kwargs: Dict) -> OpenRouterGeminiResponse:
        """Route LLM request through OpenRouter and return Gemini-compatible response.

        Handles conversion between Gemini SDK format and OpenRouter format.
        """
        self.logger.info(f"[OPENROUTER] Routing request to OpenRouter for model: {model}")
        
        openrouter = get_openrouter_handler()
        
        # Extract parameters from kwargs
        contents = kwargs.get('contents')
        config = kwargs.get('config')
        
        # Convert contents to prompt/messages format for OpenRouter
        prompt = None
        messages = None
        system_prompt = None
        tools = None
        temperature = None
        max_tokens = None
        
        # Handle config (types.GenerateContentConfig)
        if config:
            temperature = getattr(config, 'temperature', None)
            max_tokens = getattr(config, 'max_output_tokens', None)
            
            # Extract system_instruction from config
            config_system = getattr(config, 'system_instruction', None)
            if config_system:
                if isinstance(config_system, str):
                    system_prompt = config_system
                elif hasattr(config_system, 'parts'):
                    # types.Content object
                    parts = config_system.parts
                    if parts and hasattr(parts[0], 'text'):
                        system_prompt = parts[0].text
                elif hasattr(config_system, 'text'):
                    system_prompt = config_system.text
            
            # Extract tools from config if present
            config_tools = getattr(config, 'tools', None)
            if config_tools:
                tools = config_tools
        
        # Convert contents to messages format
        if isinstance(contents, str):
            prompt = contents
        elif isinstance(contents, list):
            # List of Content objects or messages
            messages = contents
        elif hasattr(contents, 'parts'):
            # Single Content object
            messages = [contents]
        else:
            prompt = str(contents) if contents else ""
        
        # Run async OpenRouter generate in sync context
        # thinking=None means auto-detect based on model capability
        async def _run_openrouter():
            return await openrouter.generate(
                model=model,
                prompt=prompt,
                messages=messages,
                system_prompt=system_prompt,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking=None,  # Auto-detect thinking capability based on model
            )
        
        # Execute async call - handle both sync and async contexts
        try:
            # Try to get existing event loop (if we're already in async context)
            loop = asyncio.get_running_loop()
            # We're in an async context, use run_coroutine_threadsafe or similar
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run_openrouter())
                result = future.result(timeout=120)
        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            result = asyncio.run(_run_openrouter())
        
        self.logger.info(f"[OPENROUTER] Request completed successfully for model: {model}")
        
        # Wrap result in Gemini-compatible response object
        return OpenRouterGeminiResponse(result)

    def __init__(self, products_csv_path: Optional[str] = None, max_iterations: int = 5, product_repository=None):
        self.logger = logging.getLogger(__name__)
        self.products_csv_path = products_csv_path or os.path.join(os.path.dirname(__file__), "products.csv")  # Default to products.csv in same directory
        self.max_iterations = max(max_iterations, 5)  # Ensure minimum 5 iterations

        # Conversation history memory for learning across products
        self.conversation_history = []  # Stores all function calls and responses
        self.successful_searches = {}  # Maps search patterns to successful results
        self.failed_searches = set()  # Tracks failed search patterns to avoid repetition

        # Multi-product context tracking
        self.all_products_context = []  # List of all products to be matched
        self.matched_products = {}  # Maps unclear_term to matched product info
        self.usage_tracker = {}  # Track function calls per unclear term
        self.current_mode = "GLOBAL"  # Track current search mode (GLOBAL or GROUP_xxx)
        self.current_group = None  # Track currently selected group
        self.user_instructions = ""  # User instructions/context from email

        # Use provided product repository or create default Lemonsoft client for backward compatibility
        self.product_repository = product_repository
        self.lemonsoft_client = None  # Initialize to None
        if self.product_repository:
            self.logger.info(f"Product matcher initialized with repository: {type(self.product_repository).__name__}")
        else:
            # Legacy mode: Initialize Lemonsoft API client for product searches (same as main.py)
            self.lemonsoft_client = LemonsoftAPIClient()
            self.logger.info("Lemonsoft API client created for product searches (legacy mode)")
            self.logger.info(f"Lemonsoft base URL: {self.lemonsoft_client.credentials.base_url}")
            # Note: Will be initialized (authenticated) when first needed
        
        # Initialize GroupBasedMatcher for combined strategy
        try:
            from src.product_matching.group_based_matcher import GroupBasedMatcher
            self.group_based_matcher = GroupBasedMatcher(product_repository=self.product_repository)
            self.logger.info("GroupBasedMatcher initialized for combined strategy")
        except Exception as e:
            self.logger.warning(f"Failed to initialize GroupBasedMatcher: {e}")
            self.group_based_matcher = None
        
        # SQL proxy configuration based on deployment mode (same pattern as pricing calculator)
        self.deployment_mode = os.getenv('DEPLOYMENT_MODE', 'direct').lower()
        self.logger.info(f"Product matcher deployment mode: {self.deployment_mode}")
        
        # SQL proxy configuration for Docker mode
        if self.deployment_mode == 'docker':
            self.sql_proxy_url = os.getenv('SQL_PROXY_URL', 'https://xxxxx.azurewebsites.net')
            self.sql_proxy_api_key = os.getenv('SQL_PROXY_API_KEY', '')
            self.azure_function_key = os.getenv('AZURE_FUNCTION_KEY', '')
            self.logger.info(f"SQL proxy configured: {self.sql_proxy_url}")
            self.http_client = None  # Will be initialized when needed
        else:
            self.http_client = None

        # Keep CSV loading as fallback for semantic search embeddings
        if os.path.exists(self.products_csv_path):
            try:
                # Load product catalogue (keep only code + Finnish name to save RAM/tokens)
                self.products_df = pd.read_csv(self.products_csv_path, encoding="utf-8", on_bad_lines='skip', delimiter=';')
                
                # Check if required columns exist
                required_columns = ['Tuotekoodi', 'Tuotenimi']
                missing_columns = [col for col in required_columns if col not in self.products_df.columns]
                if missing_columns:
                    self.logger.warning(f"Missing required columns in products CSV: {missing_columns}. Available columns: {list(self.products_df.columns)}")
                    self.products_df = None
                else:
                    # Clean the data and create lowercase column
                    self.products_df = self.products_df.dropna(subset=['Tuotenimi'])
                    self.products_df['Tuotenimi'] = self.products_df['Tuotenimi'].astype(str)
                    self.products_df["Tuotenimi_lower"] = self.products_df["Tuotenimi"].str.lower()
                    
                    self.logger.info(f"Successfully loaded {len(self.products_df)} products from {self.products_csv_path} as fallback")
                
            except Exception as e:
                self.logger.warning(f"Error loading products CSV from {self.products_csv_path}: {e}")
                self.products_df = None
        else:
            self.logger.warning(f"Products CSV not found at {self.products_csv_path}, using Lemonsoft API only")
            self.products_df = None

        # Gemini setup (for agentic search)
        self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        # OpenAI setup (for embeddings)
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1"  # Force real OpenAI endpoint
        )
        self.embedding_model = "text-embedding-3-large"  # Real OpenAI model
        self.product_embeddings: Optional[np.ndarray] = None  # Lazy-loaded
        
        # Fallback system using filtered products
        # Use path relative to this script's directory to always find the CSV file
        script_dir = Path(__file__).parent
        self.filtered_products_csv_path = script_dir / "products_9000_filtered.csv"
        self.filtered_products_df: Optional[pd.DataFrame] = None
        self.filtered_product_embeddings: Optional[np.ndarray] = None
        self.fallback_product_code = "9000"  # Always use this code for fallback matches

        # Track API usage for logging and debugging
        self.api_calls_made = 0
        self.api_errors = 0
        
        # Rate limiting tracking
        self.daily_calls = 0
        self.minute_calls = 0
        self.minute_tokens = 0  # Track tokens per minute (TPM limit)
        self.last_minute_reset = datetime.now()
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Google search API key for market research
        self.google_search_api_key = os.getenv('SERPER_API_KEY', '')
        
        # Track last function call signature in batch mode to prevent immediate repetition
        self._last_batch_function_signature = None
        self._last_batch_function_repeat_count = 0
        self._forced_stop_due_to_repetition = False

        # Initialize GroupBasedMatcher for primary matching strategy
        self.group_based_matcher = None
        if GroupBasedMatcher:
            try:
                self.group_based_matcher = GroupBasedMatcher(max_products_display=200, product_repository=self.product_repository)
                self.logger.info("✅ GroupBasedMatcher initialized successfully - will be used as primary matching strategy")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize GroupBasedMatcher: {e} - falling back to traditional matching")
                self.group_based_matcher = None
        else:
            self.logger.warning("⚠️ GroupBasedMatcher not available - using traditional matching only")
        
        # Initialize ProductMatchReviewer for post-processing review
        self.match_reviewer = None
        if ProductMatchReviewer:
            try:
                self.match_reviewer = ProductMatchReviewer(self, self.logger)
                self.logger.info("✅ ProductMatchReviewer initialized successfully - will review matches for consistency")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize ProductMatchReviewer: {e} - will skip match review")
                self.match_reviewer = None
        else:
            self.logger.warning("⚠️ ProductMatchReviewer not available - skipping match review")
        
        # Learning system: Download and merge S3 learnings
        self.s3_learnings_merged = False
        self.general_rules = []
        try:
            self._merge_s3_learnings()
        except Exception as e:
            self.logger.warning(f"Failed to merge S3 learnings: {e}")
        
    def _merge_s3_learnings(self):
        """
        Download S3 learnings and merge with local training dataset.
        
        This method:
        1. Downloads product_swaps.csv from S3
        2. Merges it with local training_dataset.csv
        3. Loads general_rules.txt from S3
        4. Caches the merged data for the session
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get S3 configuration
            bucket_name = os.getenv('AWS_S3_BUCKET_LEARNING', 'offer-learning-data')
            region = os.getenv('AWS_REGION', 'eu-north-1')
            
            # Initialize S3 client
            s3_client = boto3.client('s3', region_name=region)
            
            # Download product swaps CSV from S3
            try:
                response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key='learnings/product_swaps.csv'
                )
                s3_csv_content = response['Body'].read().decode('utf-8')
                
                # Parse S3 CSV
                from io import StringIO
                s3_df = pd.read_csv(StringIO(s3_csv_content))
                
                self.logger.info(f"✅ Downloaded {len(s3_df)} learnings from S3: learnings/product_swaps.csv")
                
                # Merge with local training dataset
                local_csv_path = os.path.join(os.path.dirname(__file__), "training_dataset.csv")
                
                if os.path.exists(local_csv_path):
                    local_df = pd.read_csv(local_csv_path)
                    
                    # Combine both datasets
                    merged_df = pd.concat([local_df, s3_df], ignore_index=True)
                    
                    # Remove duplicates based on customer_term + matched_product_code
                    merged_df = merged_df.drop_duplicates(
                        subset=['customer_term', 'matched_product_code'],
                        keep='last'  # Keep most recent (S3 learnings take precedence)
                    )
                    
                    # Save merged dataset back to local CSV
                    merged_df.to_csv(local_csv_path, index=False)
                    
                    self.logger.info(
                        f"✅ Merged S3 learnings with local training data: "
                        f"{len(local_df)} local + {len(s3_df)} S3 = {len(merged_df)} total (after dedup)"
                    )
                    self.s3_learnings_merged = True
                else:
                    # No local file, just save S3 data
                    s3_df.to_csv(local_csv_path, index=False)
                    self.logger.info(f"✅ Created training dataset from S3 learnings: {len(s3_df)} entries")
                    self.s3_learnings_merged = True
                    
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    self.logger.info("No S3 learnings CSV found yet (learnings/product_swaps.csv)")
                else:
                    self.logger.warning(f"Error downloading S3 learnings CSV: {e}")
            
            # Download general rules from S3
            try:
                response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key='learnings/general_rules.txt'
                )
                rules_content = response['Body'].read().decode('utf-8')
                
                # Parse rules (one per line)
                self.general_rules = [
                    line.strip() 
                    for line in rules_content.split('\n') 
                    if line.strip()
                ]
                
                self.logger.info(f"✅ Loaded {len(self.general_rules)} general rules from S3")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    self.logger.info("No S3 general rules found yet (learnings/general_rules.txt)")
                else:
                    self.logger.warning(f"Error downloading S3 general rules: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to merge S3 learnings: {e}")
            self.s3_learnings_merged = False
    
    def get_dynamic_iteration_limit(self, search_term: str, usage_context: Optional[str] = None) -> int:
        """Dynamically determine iteration limit based on search complexity and context."""
        base_iterations = max(self.max_iterations, 5)  # Minimum 5 iterations
        
        # Analyze search term complexity
        complexity_factors = [
            len(search_term.split()) > 3,  # Multi-word terms need more attempts
            any(char in search_term for char in ['/', '-', '&', '+', '(', ')']),  # Complex punctuation
            bool(re.search(r'\d+', search_term)),  # Contains numbers (models/sizes)
            len(search_term) > 20,  # Long product names
            bool(re.search(r'[A-Z]{2,}', search_term)),  # Contains abbreviations/codes
        ]
        
        # Context-based factors
        context_factors = []
        if usage_context:
            context_factors = [
                len(usage_context) > 500,  # Rich context available
                bool(re.search(r'\d+(?:mm|cm|m|inch|"|\')', usage_context)),  # Technical specs
                any(brand.lower() in usage_context.lower() for brand in ['honeywell', 'danfoss', 'siemens', 'grundfos']),
                'urgent' in usage_context.lower() or 'asap' in usage_context.lower(),  # Urgency
            ]
        
        # Calculate complexity boost
        complexity_boost = sum(complexity_factors) * 2
        context_boost = sum(context_factors) * 1
        
        # Check if we have relevant historical data
        historical_boost = 0
        similar_searches = [pattern for pattern in self.successful_searches.keys() 
                          if any(word in pattern.lower() for word in search_term.lower().split())]
        if similar_searches:
            historical_boost = 1  # Slight boost if we have relevant history
        
        final_limit = base_iterations + complexity_boost + context_boost + historical_boost
        
        # Cap at reasonable maximum
        final_limit = min(final_limit, 15)
        
        self.logger.info(f"Dynamic iteration limit for '{search_term}': {final_limit} "
                        f"(base: {base_iterations}, complexity: {complexity_boost}, "
                        f"context: {context_boost}, historical: {historical_boost})")
        
        return final_limit
    
    def add_to_conversation_history(self, role: str, content: str, function_name: str = None, function_result: str = None):
        """Add interaction to conversation history for learning and context."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'role': role,  # 'user', 'agent', 'function'
            'content': content,
        }
        
        if function_name:
            entry['function_name'] = function_name
        if function_result:
            entry['function_result'] = function_result
            
        self.conversation_history.append(entry)
        
        # Keep history manageable (last 50 interactions)
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def learn_from_search_result(self, search_pattern: str, search_term: str, result_count: int, success: bool):
        """Learn from search results to improve future searches."""
        if success and result_count > 0:
            # Store successful search patterns
            pattern_key = search_pattern.lower().strip('%')
            if pattern_key not in self.successful_searches:
                self.successful_searches[pattern_key] = []
            
            self.successful_searches[pattern_key].append({
                'original_term': search_term,
                'result_count': result_count,
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.debug(f"Learning: '{search_pattern}' worked for '{search_term}' ({result_count} results)")
            
        elif not success:
            # Track failed searches to avoid repetition
            self.failed_searches.add(search_pattern.lower())
            self.logger.debug(f"Learning: '{search_pattern}' failed for '{search_term}'")
    
    def get_historical_suggestions(self, search_term: str) -> List[str]:
        """Get search suggestions based on historical successful patterns."""
        suggestions = []
        term_words = set(search_term.lower().split())
        
        # Find successful patterns that share words with current search term
        for pattern, results in self.successful_searches.items():
            pattern_words = set(pattern.split())
            
            # Check for word overlap
            if term_words.intersection(pattern_words):
                # Suggest variations of successful patterns
                suggestions.append(f"%{pattern}%")
                
                # If pattern worked for similar terms, suggest it
                for result in results[:3]:  # Check last 3 successful uses
                    original_words = set(result['original_term'].lower().split())
                    if term_words.intersection(original_words):
                        suggestions.append(f"%{pattern}%")
                        break
        
        # Remove duplicates and failed patterns
        suggestions = list(set(suggestions))
        suggestions = [s for s in suggestions if s.lower() not in self.failed_searches]
        
        if suggestions:
            self.logger.info(f"Historical suggestions for '{search_term}': {suggestions[:3]}")
        
        return suggestions[:3]  # Return top 3 suggestions

    def _google_search_product(self, search_term: str) -> Dict:
        """Search for product information on Google using Finnish market focus.
        
        Args:
            search_term: Product term to search for
            
        Returns:
            Dict containing search results with organic results and related searches
        """
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            
            # Search in Finnish with Finnish location
            payload = json.dumps({
                "q": search_term,
                "location": "Finland", 
                "gl": "fi"  # Finnish results
            })
            
            headers = {
                'X-API-KEY': self.google_search_api_key,
                'Content-Type': 'application/json'
            }
            
            self.logger.info(f"🔍 Google searching for '{search_term}' in Finnish market")
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            if res.status == 200:
                search_results = json.loads(data.decode("utf-8"))
                
                # Extract useful information
                organic_results = search_results.get("organic", [])
                related_searches = search_results.get("relatedSearches", [])
                
                self.logger.info(f"✅ Google found {len(organic_results)} organic results for '{search_term}'")
                
                # Format results for the agent
                formatted_results = {
                    "organic_count": len(organic_results),
                    "top_results": [],
                    "related_terms": [rel.get("query", "") for rel in related_searches[:5]]  # Top 5 related searches
                }
                
                # Get top 5 organic results with useful info
                for result in organic_results[:5]:
                    formatted_results["top_results"].append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "link": result.get("link", "")
                    })
                
                return {"success": True, "results": formatted_results}
                
            else:
                self.logger.warning(f"❌ Google search failed with status {res.status}")
                return {"success": False, "error": f"HTTP {res.status}"}
                
        except Exception as e:
            self.logger.error(f"❌ Google search error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            try:
                conn.close()
            except:
                pass

    # ------------------------------------------------------------------
    # Rate limiting helpers
    # ------------------------------------------------------------------
    def _check_rate_limits(self):
        """Check and enforce OpenAI API rate limits."""
        now = datetime.now()
        
        # Reset daily counter if needed
        if now >= self.daily_reset_time + timedelta(days=1):
            self.daily_calls = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
        # Reset minute counter if needed
        if now >= self.last_minute_reset + timedelta(minutes=1):
            self.minute_calls = 0
            self.last_minute_reset = now
            
        # Check daily limit
        if self.daily_calls >= Config.OPENAI_RATE_LIMIT_PER_DAY:
            raise Exception(f"Daily OpenAI API limit reached ({Config.OPENAI_RATE_LIMIT_PER_DAY} calls)")
            
        # Check minute limit
        if self.minute_calls >= Config.OPENAI_RATE_LIMIT_PER_MINUTE:
            sleep_time = 60 - (now - self.last_minute_reset).total_seconds()
            if sleep_time > 0:
                self.logger.info(f"⏳ Rate limit reached. Sleeping {sleep_time:.1f}s until next minute...")
                time.sleep(sleep_time)
                self.minute_calls = 0
                self.last_minute_reset = datetime.now()
    
    def _get_openai_embedding(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI with rate limiting."""
        self._check_rate_limits()
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            
            # Update rate limiting counters
            self.daily_calls += 1
            self.minute_calls += 1
            self.api_calls_made += 1
            
            # Extract embeddings
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"OpenAI embedding API error: {e}")
            raise
    async def match_terms_batch(self, term_dicts: List[Dict], user_instructions: str = "") -> List[Dict]:
        """Match multiple product terms with full context awareness.
        
        Uses a single agent with visibility of all products to match,
        allowing for better pattern recognition and coherent matching
        of related products.
        
        Args:
            term_dicts: List of term dictionaries with unclear_term, quantity, etc.
            user_instructions: Optional user instructions/context from email (delivery dates, brand preferences, etc.)
        
        Returns list of match dictionaries ready for CSV output.
        """
        if not term_dicts:
            return []
        
        # Store user instructions for use in system prompt
        self.user_instructions = user_instructions
        if user_instructions:
            self.logger.info(f"📝 User instructions received: {user_instructions[:100]}...")
            
        # Initialize context for all products
        self.all_products_context = []
        self.matched_products = {}
        self.usage_tracker = {}
        
        # Prepare all unclear terms
        for term_dict in term_dicts:
            search_term = str(term_dict.get("unclear_term", "")).strip()
            if search_term:
                self.all_products_context.append(search_term)
                self.usage_tracker[search_term] = {
                    "calls": 0,
                    "max_calls": 20,  # Allow 15-20 iterations per product
                    "status": "pending",
                    "searches": [],  # Track search function calls
                    "search_types": []  # Track types of searches (wildcard, semantic, google)
                }

        if not self.all_products_context:
            return []
        
        self.logger.info(f"🎯 Starting batch matching for {len(self.all_products_context)} products with full context")
        
        # Use the enhanced agentic match with full context
        results = await self._agentic_batch_match_with_context(term_dicts)
        
        return results
        

    # --------------------------- priority classification ---------------
    def _classify_product_priority(self, group_code):
        """Classify product as priority or non-priority based on group_code.
        
        Args:
            group_code: Integer group code from API or SQL
            
        Returns:
            str: 'priority' if group_code >= 101010, 'non-priority' if < 101010
        """
        if group_code is None:
            return 'non-priority'  # Default to non-priority if no group_code
        
        try:
            group_code_int = int(group_code)
            return 'priority' if group_code_int >= 101010 else 'non-priority'
        except (ValueError, TypeError):
            return 'non-priority'  # Default to non-priority if invalid group_code

    async def _get_group_code_for_product(self, product_code: str):
        """Get group_code for a specific product via API.
        
        Args:
            product_code: Product SKU/code
            
        Returns:
            int or None: group_code value or None if not found
        """
        try:
            # Ensure client is initialized
            await self._ensure_lemonsoft_initialized()
            
            response = await self.lemonsoft_client.get('/api/products', params={'filter.sku': product_code})
            if response and response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    return results[0].get('group_code')
        except Exception as e:
            self.logger.debug(f"Error getting group_code for product {product_code}: {e}")
        
        return None

    # --------------------------- SQL execution methods --------------------------
    async def _initialize_http_client(self):
        """Initialize HTTP client for Function App proxy if needed."""
        if self.deployment_mode == 'docker' and self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
            
    async def _execute_sql_query(self, query: str, params: list = None) -> list:
        """
        Execute SQL query using the appropriate method based on deployment mode.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        if self.deployment_mode == 'docker':
            await self._initialize_http_client()
            return await self._execute_sql_via_function_app(query, params)
        else:
            # Direct database mode - use existing create_database_client pattern
            db_client = create_database_client()
            if not db_client:
                raise Exception("Failed to create database client")
            return db_client._execute_query_sync(query, params)
    
    async def _execute_sql_via_function_app(self, query: str, params: list = None) -> list:
        """Execute SQL query via Azure Function App proxy."""
        try:
            headers = {
                'x-functions-key': self.azure_function_key,
                'X-API-Key': self.sql_proxy_api_key,
                'Content-Type': 'application/json'
            }
            
            database_name = os.getenv('DATABASE_NAME', 'LemonDB1')
            
            payload = {
                'query': query,
                'params': params or [],
                'database': database_name
            }
            
            self.logger.debug(f"Executing SQL via Function App: {query[:100]}...")
            
            response = await self.http_client.post(
                f"{self.sql_proxy_url}/api/query",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.debug(f"Function App query successful: {result.get('row_count', 0)} rows")
                    return result.get('data', [])
                else:
                    raise Exception(f"Function App query failed: {result.get('error')}")
            else:
                error_text = response.text if response.text else f"HTTP {response.status_code}"
                raise Exception(f"Function App request failed: {error_text}")
                
        except Exception as e:
            self.logger.error(f"SQL query via Function App failed: {e}")
            raise


    async def _local_wildcard_search(self, pattern: str):
        """
        Perform wildcard search on products.

        Routes to product_repository if available (ERP-agnostic),
        otherwise falls back to legacy Lemonsoft SQL logic.
        """
        # Use product repository if available (ERP-agnostic approach)
        if self.product_repository:
            try:
                self.logger.info(f"🔍 Using ProductRepository for wildcard search: '{pattern}'")
                df = await self.product_repository.wildcard_search(pattern)
                return df
            except Exception as e:
                self.logger.error(f"ProductRepository wildcard search failed: {e}")
                # Fall through to legacy mode
                return None

        # Legacy Lemonsoft-specific implementation
        return await self._legacy_local_wildcard_search(pattern)

    async def _legacy_local_wildcard_search(self, pattern: str):
        """Search for products using SQL query across all text fields.
        
        Searches in:
        1. product_description (name)
        2. product_description2 (extra_name)  
        3. product_searchcode (search_code)
        4. product_texts.text_note (description)
        5. training_dataset.csv historical mappings
        
        Results are filtered and deduplicated by SKU.
        """
        if not pattern:
            return None

        try:
            # Split pattern by % to get individual search terms
            # Remove empty strings from the split
            search_terms = [term.strip() for term in pattern.split('%') if term.strip()]

            self.logger.info(f"SQL wildcard search - Original pattern: '{pattern}'")
            self.logger.info(f"SQL wildcard search - Split into {len(search_terms)} terms: {search_terms}")

            # Build WHERE clause: each term must appear in the combined text fields
            # We create a concatenated field of all searchable columns and check each term appears in it
            where_conditions = []
            combined_fields = "CONCAT(COALESCE(p.product_description, ''), ' ', COALESCE(p.product_description2, ''), ' ', COALESCE(p.product_searchcode, ''), ' ', COALESCE(pt.text_note, ''))"

            for term in search_terms:
                # Escape single quotes in SQL by doubling them
                escaped_term = term.replace("'", "''")
                where_conditions.append(f"{combined_fields} LIKE '%{escaped_term}%'")

            # Join all conditions with AND - all terms must be present
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            self.logger.info(f"SQL WHERE clause: All terms must appear in combined fields")

            query = f"""
            WITH yearly_sales AS (
                SELECT 
                    ir.invoicerow_productcode as product_code,
                    SUM(ir.invoicerow_amount) as total_sales_qty
                FROM invoicerows ir
                JOIN invoices i ON ir.invoice_id = i.invoice_id
                WHERE i.invoice_date >= DATEADD(year, -1, GETDATE())
                  AND ir.invoicerow_amount > 0
                GROUP BY ir.invoicerow_productcode
            ),
            total_stock AS (
                SELECT 
                    p.product_code,
                    SUM(COALESCE(ps.stock_instock, 0)) as total_current_stock
                FROM products p
                LEFT JOIN product_stocks ps ON p.product_id = ps.product_id
                GROUP BY p.product_code
            )
            SELECT TOP 200
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
                p.product_nonstock_bit,
                pd.product_group_code,
                COALESCE(p.product_price, 0) as price,
                pt.text_note as description,
                COALESCE(ts.total_current_stock, 0) as total_stock,
                COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
            FROM products p
            INNER JOIN product_dimensions pd ON p.product_id = pd.product_id
            LEFT JOIN product_texts pt ON p.product_id = pt.product_id
                AND pt.text_header_number = 3
                AND (pt.language_code IS NULL OR pt.language_code = '')
            LEFT JOIN total_stock ts ON p.product_code = ts.product_code
            LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
            WHERE
                (
                    {where_clause}
                )
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND (p.product_nonstock_bit IS NULL OR p.product_nonstock_bit = 0)
                AND pd.product_group_code != 0
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa
                    WHERE pa.product_id = p.product_id
                        AND pa.attribute_code IN (30)
                )
            ORDER BY p.product_code
            """
            
            results = await self._execute_sql_query(query, [])
            print("SQL successful")
            
            search_results = []
            
            # First, add results from training dataset CSV
            try:
                training_csv_path = os.path.join(os.path.dirname(__file__), "training_dataset.csv")
                self.logger.info(f"🔍 Searching training dataset at: {training_csv_path}")
                
                if os.path.exists(training_csv_path):
                    training_df = pd.read_csv(training_csv_path)
                    self.logger.info(f"📊 Loaded training dataset with {len(training_df)} historical terms")
                    
                    # Convert pattern to regex for matching - more flexible approach
                    if '%' in pattern:
                        # Convert SQL LIKE pattern to regex (% = .*, case insensitive)
                        regex_pattern = pattern.replace('%', '.*')
                        self.logger.info(f"🔧 Using wildcard pattern: '{pattern}' -> regex: '{regex_pattern}'")
                    else:
                        # If no wildcards, do a contains search
                        regex_pattern = f'.*{re.escape(pattern)}.*'
                        self.logger.info(f"🔧 Using contains pattern: '{pattern}' -> regex: '{regex_pattern}'")
                    
                    # Search in customer_term column (case-insensitive)
                    matches = training_df[training_df['customer_term'].str.contains(regex_pattern, case=False, na=False, regex=True)]
                    
                    if not matches.empty:
                        self.logger.info(f"✅ TRAINING DATASET: Found {len(matches)} historical matches for pattern '{pattern}'")
                        
                        # Extract product codes from historical matches
                        historical_product_codes = [str(row['matched_product_code']) for _, row in matches.iterrows()]
                        
                        # Fetch stock and sales data for historical product codes
                        stock_sales_data = {}
                        if historical_product_codes:
                            try:
                                self.logger.info(f"📊 Fetching stock/sales data for {len(historical_product_codes)} historical products")
                                escaped_codes = [code.replace("'", "''") for code in historical_product_codes]
                                codes_list = "', '".join(escaped_codes)
                                
                                stock_sales_query = f"""
                                WITH yearly_sales AS (
                                    SELECT 
                                        ir.invoicerow_productcode as product_code,
                                        SUM(ir.invoicerow_amount) as total_sales_qty
                                    FROM invoicerows ir
                                    JOIN invoices i ON ir.invoice_id = i.invoice_id
                                    WHERE i.invoice_date >= DATEADD(year, -1, GETDATE())
                                      AND ir.invoicerow_amount > 0
                                      AND ir.invoicerow_productcode IN ('{codes_list}')
                                    GROUP BY ir.invoicerow_productcode
                                ),
                                total_stock AS (
                                    SELECT 
                                        p.product_code,
                                        SUM(COALESCE(ps.stock_instock, 0)) as total_current_stock
                                    FROM products p
                                    LEFT JOIN product_stocks ps ON p.product_id = ps.product_id
                                    WHERE p.product_code IN ('{codes_list}')
                                    GROUP BY p.product_code
                                )
                                SELECT 
                                    p.product_code,
                                    COALESCE(ts.total_current_stock, 0) as total_stock,
                                    COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
                                FROM products p
                                LEFT JOIN total_stock ts ON p.product_code = ts.product_code
                                LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
                                WHERE p.product_code IN ('{codes_list}')
                                """
                                
                                stock_sales_results = await self._execute_sql_query(stock_sales_query, [])
                                
                                if stock_sales_results:
                                    for row in stock_sales_results:
                                        if isinstance(row, dict):
                                            code = str(row.get('product_code', ''))
                                            stock_sales_data[code] = {
                                                'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                                                'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0
                                            }
                                        else:
                                            code = str(row[0]) if row[0] else ''
                                            stock_sales_data[code] = {
                                                'total_stock': float(row[1]) if len(row) > 1 and row[1] else 0.0,
                                                'yearly_sales_qty': float(row[2]) if len(row) > 2 and row[2] else 0.0
                                            }
                                    self.logger.info(f"✅ Retrieved stock/sales data for {len(stock_sales_data)} historical products")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Could not fetch stock/sales for historical matches: {e}")
                        
                        # Convert training dataset matches to search result format
                        for _, row in matches.iterrows():
                            product_code = str(row['matched_product_code'])
                            stock_sales = stock_sales_data.get(product_code, {})
                            
                            search_results.append({
                                'id': '',  # No ID in training data
                                'sku': product_code,
                                'name': str(row['matched_product_name']),
                                'extra_name': '',  # Keep clean
                                'price': 0.0,  # No price in training data
                                'product_searchcode': '',
                                'description': f"Confidence: {row['confidence_score']}, Type: {row.get('match_type', 'historical')}",
                                'group_code': 0,  # No group code in training data
                                'priority': 'high',  # Give high priority to training matches
                                'total_stock': stock_sales.get('total_stock'),  # Real stock data or None
                                'yearly_sales_qty': stock_sales.get('yearly_sales_qty'),  # Real sales data or None
                                'historical_customer_term': str(row['customer_term']),  # NEW FIELD
                                'data_source': 'HISTORICAL_TRAINING'  # NEW FIELD to identify source
                            })
                        
                        # Log each historical match found
                        for _, row in matches.iterrows():
                            self.logger.info(f"   📚 Historical: '{row['customer_term']}' -> {row['matched_product_code']} ({row['confidence_score']})")
                    else:
                        self.logger.info(f"📭 TRAINING DATASET: No historical matches found for pattern '{pattern}'")
                else:
                    self.logger.warning(f"📭 Training dataset not found at: {training_csv_path}")
            except Exception as e:
                self.logger.error(f"❌ Could not search training dataset: {e}")
                import traceback
                self.logger.debug(f"Training dataset search traceback: {traceback.format_exc()}")
            
            # Process SQL results if any
            if results:
                # Convert SQL results to API-compatible format
                for row in results:
                    # Handle both dict (direct DB) and tuple (Function App) responses
                    if isinstance(row, dict):
                        group_code = int(row.get('product_group_code')) if row.get('product_group_code') else 0
                        priority = self._classify_product_priority(group_code)
                        
                        search_results.append({
                            'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                            'sku': str(row.get('product_code', '')) if row.get('product_code') else '',
                            'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                            'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                            'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                            'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                            'description': str(row.get('description', '')) if row.get('description') else '',
                            'group_code': group_code,
                            'priority': priority,
                            'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                            'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0,
                            'data_source': 'SQL_DATABASE'  # Mark as SQL database result
                        })
                    else:
                        # Legacy tuple handling for Function App
                        group_code = int(row[7]) if row[7] else 0
                        priority = self._classify_product_priority(group_code)
                        
                        search_results.append({
                            'id': str(row[0]) if row[0] else '',
                            'sku': str(row[1]) if row[1] else '',
                            'name': str(row[2]) if row[2] else '',
                            'extra_name': str(row[3]) if row[3] else '',
                            'price': float(row[8]) if row[8] else 0.0,
                            'product_searchcode': str(row[4]) if row[4] else '',
                            'description': str(row[9]) if row[9] else '',
                            'group_code': group_code,
                            'priority': priority,
                            'total_stock': float(row[10]) if len(row) > 10 and row[10] else 0.0,
                            'yearly_sales_qty': float(row[11]) if len(row) > 11 and row[11] else 0.0,
                            'data_source': 'SQL_DATABASE'  # Mark as SQL database result
                        })
            else:
                self.logger.info(f"❌ No products found from SQL wildcard search with pattern '{pattern}'")
            
            # Process ALL search results (both historical and SQL)
            if search_results:
                # Remove duplicates by SKU
                unique_products = {}
                for product in search_results:
                    if isinstance(product, dict):
                        sku = product.get('sku', '')
                        if sku and sku not in unique_products:
                            unique_products[sku] = product

                final_results = list(unique_products.values())
                
                # Count sources for logging
                historical_count = sum(1 for p in final_results if p.get('data_source') == 'HISTORICAL_TRAINING')
                sql_count = sum(1 for p in final_results if p.get('data_source') == 'SQL_DATABASE')
                
                self.logger.info(f"Found {len(final_results)} unique products (Historical: {historical_count}, SQL: {sql_count})")

                # Convert to DataFrame for consistency with existing interface
                if final_results:
                    df = pd.DataFrame(final_results)
                    
                    # Separate products by priority for better ordering
                    # Historical matches get highest priority
                    historical_products = []
                    priority_products = []
                    non_priority_products = []
                    
                    for _, row in df.iterrows():
                        if row.get('data_source') == 'HISTORICAL_TRAINING':
                            historical_products.append(row)
                        elif row.get('priority') == 'priority':
                            priority_products.append(row)
                        else:
                            non_priority_products.append(row)
                    
                    # Combine with historical first, then priority, then others
                    all_rows = historical_products + priority_products + non_priority_products
                    
                    if all_rows:
                        final_df = pd.DataFrame(all_rows)
                        self.logger.info(f"✅ Found {len(final_df)} products from wildcard search with pattern '{pattern}'")
                        return final_df
                    else:
                        self.logger.info(f"❌ No products found from wildcard search with pattern '{pattern}'")
                        return None
                else:
                    self.logger.info(f"❌ No products found from wildcard search with pattern '{pattern}'")
                    return None
            else:
                self.logger.info(f"❌ No products found from wildcard search with pattern '{pattern}'")
                return None
                
        except Exception as e:
            self.logger.warning(f"SQL wildcard search failed for pattern '{pattern}': {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            # Fallback to CSV search if available
            return self._local_wildcard_search_csv(pattern)

    async def _search_by_product_codes(self, product_codes: list):
        """
        Search for products by their product codes.

        Routes to product_repository if available (ERP-agnostic),
        otherwise falls back to legacy Lemonsoft SQL logic.

        Args:
            product_codes: List of product codes to search for (e.g., ['12345', '67890'])

        Returns:
            DataFrame with matching products in same format as wildcard_search, or None if no results
        """
        # Use product repository if available (ERP-agnostic approach)
        if self.product_repository:
            try:
                self.logger.info(f"🔢 Using ProductRepository for product code search")
                df = await self.product_repository.search_by_product_codes(product_codes)
                return df
            except Exception as e:
                self.logger.error(f"ProductRepository product code search failed: {e}")
                # Fall through to legacy mode
                return None

        # Legacy Lemonsoft-specific implementation
        return await self._legacy_search_by_product_codes(product_codes)

    async def _legacy_search_by_product_codes(self, product_codes: list):
        """Search for products by their product codes directly from SQL database (legacy).

        Args:
            product_codes: List of product codes to search for (e.g., ['12345', '67890'])

        Returns:
            DataFrame with matching products in same format as wildcard_search, or None if no results
        """
        if not product_codes:
            self.logger.warning("No product codes provided for search")
            return None
        
        try:
            # Clean and prepare product codes
            clean_codes = [str(code).strip() for code in product_codes if code]
            
            if not clean_codes:
                return None
            
            self.logger.info(f"🔢 Product code search - Searching for {len(clean_codes)} codes: {clean_codes}")
            
            # Build IN clause for SQL query
            # Escape single quotes by doubling them
            escaped_codes = [code.replace("'", "''") for code in clean_codes]
            codes_list = "', '".join(escaped_codes)
            
            query = f"""
            WITH yearly_sales AS (
                SELECT 
                    ir.invoicerow_productcode as product_code,
                    SUM(ir.invoicerow_amount) as total_sales_qty
                FROM invoicerows ir
                JOIN invoices i ON ir.invoice_id = i.invoice_id
                WHERE i.invoice_date >= DATEADD(year, -1, GETDATE())
                  AND ir.invoicerow_amount > 0
                  AND ir.invoicerow_productcode IN ('{codes_list}')
                GROUP BY ir.invoicerow_productcode
            ),
            total_stock AS (
                SELECT 
                    p.product_code,
                    SUM(COALESCE(ps.stock_instock, 0)) as total_current_stock
                FROM products p
                LEFT JOIN product_stocks ps ON p.product_id = ps.product_id
                WHERE p.product_code IN ('{codes_list}')
                GROUP BY p.product_code
            )
            SELECT 
                p.product_id,
                p.product_code,
                p.product_description,
                p.product_description2,
                p.product_searchcode,
                p.product_nonactive_bit,
                p.product_nonstock_bit,
                pd.product_group_code,
                COALESCE(p.product_price, 0) as price,
                pt.text_note as description,
                COALESCE(ts.total_current_stock, 0) as total_stock,
                COALESCE(ys.total_sales_qty, 0) as yearly_sales_qty
            FROM products p
            INNER JOIN product_dimensions pd ON p.product_id = pd.product_id
            LEFT JOIN product_texts pt ON p.product_id = pt.product_id
                AND pt.text_header_number = 3
                AND (pt.language_code IS NULL OR pt.language_code = '')
            LEFT JOIN total_stock ts ON p.product_code = ts.product_code
            LEFT JOIN yearly_sales ys ON p.product_code = ys.product_code
            WHERE
                p.product_code IN ('{codes_list}')
                AND (p.product_nonactive_bit IS NULL OR p.product_nonactive_bit = 0)
                AND (p.product_nonstock_bit IS NULL OR p.product_nonstock_bit = 0)
                AND pd.product_group_code != 0
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes pa
                    WHERE pa.product_id = p.product_id
                        AND pa.attribute_code IN (30)
                )
            ORDER BY p.product_code
            """
            
            results = await self._execute_sql_query(query, [])
            
            if not results:
                self.logger.info(f"❌ No products found for codes: {clean_codes}")
                return None
            
            search_results = []
            found_codes = []
            
            # Process SQL results
            for row in results:
                # Handle both dict (direct DB) and tuple (Function App) responses
                if isinstance(row, dict):
                    product_code = str(row.get('product_code', ''))
                    found_codes.append(product_code)
                    
                    group_code = int(row.get('product_group_code')) if row.get('product_group_code') else 0
                    priority = self._classify_product_priority(group_code)
                    
                    search_results.append({
                        'id': str(row.get('product_id', '')) if row.get('product_id') else '',
                        'sku': product_code,
                        'name': str(row.get('product_description', '')) if row.get('product_description') else '',
                        'extra_name': str(row.get('product_description2', '')) if row.get('product_description2') else '',
                        'price': float(row.get('price', 0)) if row.get('price') else 0.0,
                        'product_searchcode': str(row.get('product_searchcode', '')) if row.get('product_searchcode') else '',
                        'description': str(row.get('description', '')) if row.get('description') else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row.get('total_stock', 0)) if row.get('total_stock') else 0.0,
                        'yearly_sales_qty': float(row.get('yearly_sales_qty', 0)) if row.get('yearly_sales_qty') else 0.0,
                        'data_source': 'PRODUCT_CODE_SEARCH'
                    })
                else:
                    # Legacy tuple handling for Function App
                    product_code = str(row[1]) if row[1] else ''
                    found_codes.append(product_code)
                    
                    group_code = int(row[7]) if row[7] else 0
                    priority = self._classify_product_priority(group_code)
                    
                    search_results.append({
                        'id': str(row[0]) if row[0] else '',
                        'sku': product_code,
                        'name': str(row[2]) if row[2] else '',
                        'extra_name': str(row[3]) if row[3] else '',
                        'price': float(row[8]) if row[8] else 0.0,
                        'product_searchcode': str(row[4]) if row[4] else '',
                        'description': str(row[9]) if row[9] else '',
                        'group_code': group_code,
                        'priority': priority,
                        'total_stock': float(row[10]) if len(row) > 10 and row[10] else 0.0,
                        'yearly_sales_qty': float(row[11]) if len(row) > 11 and row[11] else 0.0,
                        'data_source': 'PRODUCT_CODE_SEARCH'
                    })
            
            # Report which codes were found vs not found
            not_found = set(clean_codes) - set(found_codes)
            if not_found:
                self.logger.warning(f"⚠️ Product codes NOT FOUND: {list(not_found)}")
            
            if search_results:
                self.logger.info(f"✅ Found {len(search_results)} products from {len(found_codes)} product codes")
                
                # Convert to DataFrame for consistency with existing interface
                df = pd.DataFrame(search_results)
                
                # Separate products by priority for better ordering
                priority_products = []
                non_priority_products = []
                
                for _, row in df.iterrows():
                    if row.get('priority') == 'priority':
                        priority_products.append(row)
                    else:
                        non_priority_products.append(row)
                
                # Combine with priority first
                all_rows = priority_products + non_priority_products
                
                if all_rows:
                    final_df = pd.DataFrame(all_rows)
                    self.logger.info(f"✅ Returning {len(final_df)} products from product code search")
                    return final_df
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Product code search failed: {type(e).__name__}: {e}")
            import traceback
            self.logger.debug(f"Full traceback: {traceback.format_exc()}")
            return None

    def _local_wildcard_search_csv(self, pattern: str):
        """Fallback CSV-based wildcard search."""
        if not pattern or self.products_df is None:
            return None

        # Convert simple "*" wildcard to regex
        regex = (
            "^" + re.escape(pattern.lower()).replace("\\*", ".*") if "*" in pattern else f".*{re.escape(pattern.lower())}.*"
        )
        try:
            return self.products_df[
                self.products_df["Tuotenimi_lower"].str.match(regex, na=False)
            ]
        except re.error as e:
            self.logger.debug(f"Regex error for pattern '{pattern}': {e}")
            return None

    # --------------------------- semantic search ----------------------
    def _ensure_embeddings_loaded(self):
        """Load or compute product catalogue embeddings lazily."""
        if self.product_embeddings is not None:
            return

        emb_path = f"{os.path.splitext(self.products_csv_path)[0]}.openai_embeddings.npy"

        if os.path.exists(emb_path):
            try:
                self.product_embeddings = np.load(emb_path)
                self.logger.info(f"✅ Loaded pre-computed OpenAI embeddings ({self.product_embeddings.shape}) from {emb_path}")
                return
            except Exception as e:
                self.logger.warning(f"Could not load embeddings file – recomputing ({e})")

        # Optional limit (set MAX_EMBEDDING_PRODUCTS > 0 to limit, 0 = process all)
        product_names = self.products_df["Tuotenimi"].astype(str).tolist()
        total_products = len(product_names)
        
        MAX_PRODUCTS_FOR_EMBEDDING = Config.MAX_EMBEDDING_PRODUCTS
        
        if MAX_PRODUCTS_FOR_EMBEDDING > 0 and total_products > MAX_PRODUCTS_FOR_EMBEDDING:
            self.logger.warning(f"⚠️ Limiting embedding generation to first {MAX_PRODUCTS_FOR_EMBEDDING} products (out of {total_products})")
            self.logger.warning(f"💡 Set MAX_EMBEDDING_PRODUCTS=0 to process all {total_products} products")
            product_names = product_names[:MAX_PRODUCTS_FOR_EMBEDDING]
            # Also limit the DataFrame to match
            self.products_df = self.products_df.head(MAX_PRODUCTS_FOR_EMBEDDING)
        else:
            self.logger.info(f"🚀 Processing ALL {total_products} products for OpenAI embedding generation")

        # Use batch embedding generation with progress tracking
        vectors = []
        # OpenAI can handle larger batches efficiently
        batch_size = Config.EMBEDDING_BATCH_SIZE
        
        # Calculate optimal batching for RAG-like processing
        total_batches = (len(product_names) + batch_size - 1) // batch_size
        max_batches_per_minute = Config.OPENAI_RATE_LIMIT_PER_MINUTE
        estimated_time_minutes = max(total_batches / max_batches_per_minute, 1.0)
        
        self.logger.info(f"📊 RAG-style processing: {total_batches} large batches (~{batch_size} products each)")
        self.logger.info(f"📊 Estimated completion time: {estimated_time_minutes:.1f} minutes (much faster than small batches!)")
        self.logger.info(f"🔄 Using OpenAI {self.embedding_model} with rate limits: {Config.OPENAI_RATE_LIMIT_PER_MINUTE}/min, {Config.OPENAI_RATE_LIMIT_PER_DAY}/day")
            
        self.logger.info(f"🔄 Computing OpenAI embeddings for {len(product_names)} products in {total_batches} batches...")
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(product_names))
            batch_names = product_names[start_idx:end_idx]
            
            self.logger.info(f"📦 RAG batch {batch_idx + 1}/{total_batches}: {len(batch_names)} products (API calls: {self.daily_calls}/{Config.OPENAI_RATE_LIMIT_PER_DAY})")
             
            try:
                # Get embeddings using OpenAI with rate limiting
                batch_embeddings = self._get_openai_embedding(batch_names)
                vectors.extend(batch_embeddings)
                self.logger.info(f"✅ Batch {batch_idx + 1} completed: {len(batch_embeddings)} embeddings generated")
                     
            except Exception as e:
                self.logger.error(f"Batch embedding failed for batch {batch_idx + 1}: {e}")
                # Add fallback zero vectors for failed batch (OpenAI text-embedding-3-large uses 3072 dimensions)
                for _ in batch_names:
                    vectors.append([0.0] * 3072)  # OpenAI text-embedding-3-large dimension

        if len(vectors) == 0:
            self.logger.error("❌ No embeddings generated - falling back to regex-only matching")
            return

        self.product_embeddings = np.asarray(vectors, dtype="float32")
        self.logger.info(f"✅ Generated {len(vectors)} OpenAI embeddings (shape: {self.product_embeddings.shape})")

        # Try persisting for next runs
        try:
            np.save(emb_path, self.product_embeddings)
            self.logger.info(f"💾 Saved OpenAI embeddings to {emb_path}")
        except Exception as e:
            self.logger.debug(f"Could not save embeddings: {e}")

    def _semantic_search_product_catalogue(self, search_term: str, top_k: int = 40):
        """Return top-k catalogue rows by cosine similarity using OpenAI embeddings.
        
        Note: Smaller top_k (5-15) often works better than large values (40+) 
        because it reduces noise and helps the LLM focus on truly relevant matches.
        """
        if not search_term:
            return None

        # Ensure base embeddings are ready
        self._ensure_embeddings_loaded()

        try:
            # Get query embedding using OpenAI
            query_embeddings = self._get_openai_embedding([search_term])
            query_emb = query_embeddings[0]
        except Exception as e:
            self.logger.error(f"OpenAI embedding failed for query '{search_term}': {e}")
            return None

        query_vec = np.asarray(query_emb, dtype="float32")
        # Cosine similarity
        dot = np.dot(self.product_embeddings, query_vec)
        norms = np.linalg.norm(self.product_embeddings, axis=1) * (np.linalg.norm(query_vec) + 1e-8)
        similarities = dot / norms

        # Pick top-k indices (smaller k = higher quality results)
        effective_k = min(top_k, 15)  # Cap at 15 for better quality
        if top_k > 15:
            self.logger.debug(f"🎯 Reducing top_k from {top_k} to {effective_k} for better match quality")
            
        top_idx = similarities.argsort()[::-1][:effective_k]
        if len(top_idx) == 0:
            return None

        result_df = self.products_df.iloc[top_idx].copy()
        result_df["similarity"] = similarities[top_idx]

        # Debug: Log similarity scores
        max_sim = similarities[top_idx[0]] if len(top_idx) > 0 else 0.0
        self.logger.debug(f"🔍 OpenAI semantic search for '{search_term}': max similarity = {max_sim:.3f}")
        
        # Show top 3 matches for debugging
        if len(result_df) > 0:
            top_3 = result_df.head(3)
            for _, row in top_3.iterrows():
                self.logger.debug(f"   {row['similarity']:.3f}: {row['Tuotekoodi']} - {row['Tuotenimi']}")

        # Dynamic similarity threshold: at least 0.30 or Config-specified higher value
        sim_threshold = max(0.30, getattr(Config, "SEMANTIC_SIMILARITY_THRESHOLD", 0.0))

        filtered_df = result_df[result_df["similarity"] > sim_threshold]
        
        if len(filtered_df) == 0:
            self.logger.debug(f"❌ No semantic matches above {sim_threshold:.3f} threshold for '{search_term}'")
        else:
            self.logger.debug(f"✅ Found {len(filtered_df)} semantic matches above {sim_threshold:.3f} threshold")
            
        return filtered_df

   
    
    async def _agentic_batch_match_with_context(self, term_dicts: List[Dict]):
        """Enhanced agentic matching with full product context awareness.
        
        This method provides the agent with visibility of ALL products to match,
        allowing for better pattern recognition and coherent matching of related products.
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for retry_attempt in range(max_retries):
            try:
                self.logger.info(f"🚀 Starting batch agentic match (attempt {retry_attempt + 1}/{max_retries})")
                # Reset repetition tracker at the start of a batch run
                self._last_batch_function_signature = None
                self._last_batch_function_repeat_count = 0
                self._forced_stop_due_to_repetition = False
                
                # Step 1: Initialize parameters
                try:
                    num_products = len(self.all_products_context)
                    max_iterations = num_products * 7  # 10 iterations per product term
                    self.logger.info(f"🔄 Batch processing with {max_iterations} max iterations for {num_products} products ({max_iterations//num_products} iterations per product)")
                except Exception as e:
                    self.logger.error(f"❌ Error calculating max iterations: {e}. Using fallback value")
                    max_iterations = max(150, len(term_dicts) * 10) if term_dicts else 200

                # Step 2: Initialize group matcher (only if using Lemonsoft client, not product_repository)
                try:
                    if self.group_based_matcher and self.group_based_matcher.lemonsoft_client:
                        self.logger.debug("🔧 Initializing group matcher Lemonsoft client")
                        await self.group_based_matcher.lemonsoft_client.initialize()
                        self.logger.debug("✅ Group matcher Lemonsoft client initialized successfully")
                    elif self.group_based_matcher and self.group_based_matcher.product_repository:
                        self.logger.debug("✅ Group matcher using product repository (no Lemonsoft init needed)")
                except Exception as e:
                    self.logger.error(f"❌ Error initializing group matcher: {e}")
                    # Continue without group matcher
                
                # Step 3: Build products context
                try:
                    self.logger.debug("🏗️ Building products context prompt")
                    products_context = self._build_products_context_prompt()
                    self.logger.debug("✅ Products context built successfully")
                except Exception as e:
                    self.logger.error(f"❌ Error building products context: {e}")
                    products_context = "No product context available due to error"
                
                # Step 4: Get historical suggestions
                try:
                    self.logger.debug("📚 Gathering historical suggestions")
                    all_historical_suggestions = []
                    for term in self.all_products_context:
                        suggestions = self.get_historical_suggestions(term)
                        all_historical_suggestions.extend(suggestions)
                    self.logger.debug(f"✅ Gathered {len(all_historical_suggestions)} historical suggestions")
                except Exception as e:
                    self.logger.error(f"❌ Error gathering historical suggestions: {e}")
                    all_historical_suggestions = []
                
                # Step 5: Get search functions
                try:
                    self.logger.debug("🔍 Getting batch search functions")
                    search_functions = self._get_batch_search_functions()
                    self.logger.debug("✅ Batch search functions retrieved successfully")
                except Exception as e:
                    self.logger.error(f"❌ Error getting search functions: {e}")
                    raise  # This is critical, can't continue without functions
                
                # Step 6: Build system instruction
                try:
                    self.logger.debug("📝 Building batch system instruction")
                    system_instruction = self._build_batch_system_instruction(products_context, all_historical_suggestions)
                    self.logger.debug("✅ System instruction built successfully")
                except Exception as e:
                    self.logger.error(f"❌ Error building system instruction: {e}")
                    raise  # Critical error
                
                # Step 7: Configure tools and client (with system_instruction)
                try:
                    self.logger.debug("⚙️ Configuring Gemini tools and client")
                    tools = types.Tool(function_declarations=search_functions)
                    config = types.GenerateContentConfig(
                        tools=[tools],
                        temperature=0.3,
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(mode='ANY')
                        ),
                        system_instruction=system_instruction,
                    )
                    self.logger.debug("✅ Gemini configuration completed successfully")
                except Exception as e:
                    self.logger.error(f"❌ Error configuring Gemini tools: {e}")
                    raise  # Critical error
                
                # Step 8: Initialize conversation (minimal user trigger)
                # Use SDK types (Content/Part) - same import as gemini.py
                try:
                    from google import genai as genai_client
                    self.logger.debug("💬 Initializing conversation")
                    contents = [
                        genai_client.types.Content(
                            role="user",
                            parts=[genai_client.types.Part(text="Begin batch matching.")]
                        )
                    ]
                    self.logger.debug("✅ Conversation initialized successfully (SDK types)")
                except Exception as e:
                    self.logger.error(f"❌ Error initializing conversation: {e}")
                    raise  # Critical error
                
                self.logger.info(f"🤖 Starting batch agentic search for {len(self.all_products_context)} products")
                
                # Step 9: Main conversation loop
                for iteration in range(max_iterations):
                    try:
                        # Check if all products are matched
                        if all(self.usage_tracker[term]["status"] in ["matched", "no_match"] for term in self.all_products_context):
                            self.logger.info("✅ All products processed")
                            break
                        
                        self.logger.info(f"🔄 Iteration {iteration + 1}/{max_iterations}")
                        
                        # Manage context size before API call
                        contents = self._manage_conversation_context(contents, max_tokens=Config.MAX_CONTEXT_TOKENS)
                        
                        # Gemini API call with detailed error handling
                        try:
                            self.logger.debug(f"🧠 Making Gemini API call (iteration {iteration + 1})")
                            self.api_calls_made += 1
                            response = self._retry_llm_request(
                                self.gemini_client.models.generate_content,
                                model='grok-4-1-fast-reasoning',
                                contents=contents,
                                config=config,
                            )
                            self.logger.debug(f"✅ Gemini API call successful (iteration {iteration + 1})")
                            
                        except Exception as e:
                            self.logger.error(f"❌ Gemini API call failed (iteration {iteration + 1}): {e}")
                            raise  # Re-raise to trigger retry
                        
                        # Response validation
                        try:
                            if not response or not response.candidates:
                                self.logger.warning(f"❌ Empty response from Gemini (iteration {iteration + 1})")
                                break
                            
                            # Check if content and parts exist before accessing
                            if (not response.candidates[0].content or 
                                not response.candidates[0].content.parts or 
                                len(response.candidates[0].content.parts) == 0):
                                self.logger.warning(f"⚠️ No content parts in Gemini response (iteration {iteration + 1}), retrying...")
                                continue
                                
                            self.logger.debug(f"✅ Gemini response validation passed (iteration {iteration + 1})")
                            
                        except Exception as e:
                            self.logger.error(f"❌ Error validating Gemini response (iteration {iteration + 1}): {e}")
                            raise  # Re-raise to trigger retry
                        
                        # Function call handling - MUST process ALL function calls for Claude compatibility
                        # Claude requires that every tool_use has a corresponding tool_result
                        try:
                            # Collect ALL function calls from the response
                            function_calls_to_process = []
                            for part in response.candidates[0].content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    function_calls_to_process.append(part.function_call)
                            
                            if function_calls_to_process:
                                # Log all function calls
                                self.logger.info(f"💬 Batch agent called {len(function_calls_to_process)} function(s): {[fc.name for fc in function_calls_to_process]}")
                                
                                # Store all function results
                                function_results = []
                                batch_complete = False
                                
                                # Execute ALL function calls
                                for function_call in function_calls_to_process:
                                    function_name = function_call.name
                                    function_args = function_call.args
                                    
                                    self.logger.info(f"💬 Executing function: {function_name}")
                                    self.logger.debug(f"🔧 Function args: {function_args}")
                                    
                                    try:
                                        function_result = await self._execute_batch_function(
                                            function_name, function_args
                                        )
                                        function_results.append({
                                            'function_call': function_call,
                                            'result': function_result
                                        })
                                        self.logger.debug(f"✅ Function {function_name} executed successfully")
                                        
                                        # Check if batch is complete
                                        if function_result.get('batch_complete'):
                                            batch_complete = True
                                            
                                    except Exception as e:
                                        self.logger.error(f"❌ Error executing function {function_name}: {e}")
                                        raise
                                
                                if batch_complete:
                                    self.logger.info("🏁 Batch processing marked as complete")
                                    break
                                
                                # Add model response once (with ALL function calls)
                                try:
                                    model_content = response.candidates[0].content
                                    
                                    # Check if using a Gemini model (needs thought_signature conversion)
                                    # vs non-Gemini model like Claude (MUST preserve original function call IDs)
                                    current_model = 'claude-sonnet-4.5'  # The model used in this loop
                                    is_gemini_model = self._is_gemini_model(current_model)
                                    
                                    if is_gemini_model:
                                        # Gemini models: convert with thought_signature handling
                                        is_gemini_3 = self._is_gemini_3_model('gemini-3-pro-preview')
                                        model_content_converted = self._convert_content_with_signature(
                                            model_content, 
                                            is_gemini_3=is_gemini_3
                                        )
                                        contents.append(model_content_converted)
                                    else:
                                        # Non-Gemini models (Claude, etc.): use original content to preserve IDs
                                        # The _convert_content_with_signature loses function call IDs because
                                        # Gemini SDK FunctionCall doesn't have an 'id' field
                                        # Claude requires matching tool_use_id and tool_result_id
                                        contents.append(model_content)
                                        self.logger.debug(f"✅ Using original model content (preserving function call IDs for {current_model})")
                                    
                                    # Add ALL function responses - CRITICAL for Claude compatibility
                                    # Each tool_use MUST have a corresponding tool_result with matching tool_call_id
                                    for fr_data in function_results:
                                        fc = fr_data['function_call']
                                        result = fr_data['result']
                                        if result.get('response'):
                                            # Pass the tool_call_id so Claude can match results to the correct calls
                                            # This is essential when there are multiple calls to the same function
                                            tool_call_id = getattr(fc, 'id', None)
                                            function_response_content = self._create_function_response_content(
                                                fc.name,
                                                result['response'],
                                                tool_call_id=tool_call_id
                                            )
                                            contents.append(function_response_content)
                                            self.logger.debug(f"✅ Function response added for {fc.name} (id: {tool_call_id})")
                                    
                                    self.logger.debug(f"✅ All {len(function_results)} function responses added (model: {current_model})")
                                    
                                except Exception as e:
                                    self.logger.error(f"❌ Error preparing function responses: {e}")
                                    raise  # Re-raise to trigger retry
                            
                            else:
                                self.logger.warning(f"❌ No function call in response (iteration {iteration + 1})")
                                break
                                
                        except Exception as e:
                            self.logger.error(f"❌ Error handling function call (iteration {iteration + 1}): {e}")
                            raise  # Re-raise to trigger retry
                            
                    except Exception as e:
                        self.logger.error(f"❌ Error in batch iteration {iteration + 1}: {e}")
                        raise  # Re-raise to trigger retry
                
                # Step 10: Convert matched products to result format
                try:
                    self.logger.debug("🔄 Converting matched products to result format")
                    matched_rows = []
                    for term_dict in term_dicts:
                        search_term = str(term_dict.get("unclear_term", "")).strip()
                        if search_term in self.matched_products:
                            match_info = self.matched_products[search_term]
                            matched_rows.append({
                                "unclear_term": search_term,
                                "matched_product_code": match_info["product_code"],
                                "matched_product_name": match_info["product_name"],
                                "email_subject": term_dict.get("email_subject", ""),
                                "email_date": term_dict.get("email_date"),
                                "quantity": term_dict.get("quantity", "1"),  # PRESERVE QUANTITY from input
                                "explanation": term_dict.get("explanation", ""),  # PRESERVE EXPLANATION from input
                                "ai_reasoning": match_info.get("reasoning") or "Tuote valittu hakutulosten perusteella",  # ADD AI REASONING with fallback
                                "ai_confidence": match_info.get("confidence", 0),  # ADD AI CONFIDENCE if available
                            })
                        elif self.usage_tracker.get(search_term, {}).get("status") == "no_match":
                            # Use 9000 fallback for no matches - preserve the original term name
                            matched_rows.append({
                                "unclear_term": search_term,
                                "matched_product_code": "9000",
                                "matched_product_name": search_term if search_term else "Tuote puuttuu hinnoittelusta",  # Use the original term as product name
                                "email_subject": term_dict.get("email_subject", ""),
                                "email_date": term_dict.get("email_date"),
                                "quantity": term_dict.get("quantity", "1"),  # PRESERVE QUANTITY from input
                                "explanation": term_dict.get("explanation", ""),  # PRESERVE EXPLANATION from input
                                "ai_reasoning": "No matching product found in catalog",  # ADD AI REASONING for no match
                                "ai_confidence": 0,  # No confidence for no match
                            })

                    # If we hard-stopped due to repetition, close out all remaining pending terms with 9000 fallback
                    if self._forced_stop_due_to_repetition:
                        self.logger.warning("⚠️ Forced-stop due to repetition detected – closing out remaining pending terms with 9000 fallback")
                        for term_dict in term_dicts:
                            search_term = str(term_dict.get("unclear_term", "")).strip()
                            if search_term and search_term not in self.matched_products and self.usage_tracker.get(search_term, {}).get("status") not in ["matched", "no_match"]:
                                matched_rows.append({
                                    "unclear_term": search_term,
                                    "matched_product_code": "9000",
                                    "matched_product_name": search_term if search_term else "Tuote puuttuu hinnoittelusta",
                                    "email_subject": term_dict.get("email_subject", ""),
                                    "email_date": term_dict.get("email_date"),
                                    "quantity": term_dict.get("quantity", "1"),
                                    "explanation": term_dict.get("explanation", ""),
                                    "ai_reasoning": "Batch stopped to prevent infinite loop; assigning 9000 fallback",
                                    "ai_confidence": 0,
                                })
                    
                    self.logger.info(f"✅ Successfully processed {len(matched_rows)} products on attempt {retry_attempt + 1}")
                    return matched_rows
                    
                except Exception as e:
                    self.logger.error(f"❌ Error converting results to output format: {e}")
                    raise  # Re-raise to trigger retry
                    
            except Exception as e:
                self.logger.error(f"❌ Batch agentic match failed on attempt {retry_attempt + 1}/{max_retries}: {e}")
                
                if retry_attempt < max_retries - 1:
                    self.logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    self.logger.error(f"❌ All {max_retries} attempts failed. Returning mixed results (preserving successful matches).")
                    
                    # Return mixed results: preserve successful matches, use 9000 fallback only for unmatched terms
                    fallback_rows = []
                    for term_dict in term_dicts:
                        search_term = str(term_dict.get("unclear_term", "")).strip()
                        
                        # Check if this term was successfully matched before the failure
                        if search_term in self.matched_products:
                            # Preserve the successful match
                            match_info = self.matched_products[search_term]
                            fallback_rows.append({
                                "unclear_term": search_term,
                                "matched_product_code": match_info["product_code"],
                                "matched_product_name": match_info["product_name"],
                                "email_subject": term_dict.get("email_subject", ""),
                                "email_date": term_dict.get("email_date"),
                                "quantity": term_dict.get("quantity", "1"),
                                "explanation": term_dict.get("explanation", ""),
                                "ai_reasoning": match_info.get("reasoning") or "Tuote valittu hakutulosten perusteella",
                                "ai_confidence": match_info.get("confidence", 0),
                            })
                            self.logger.info(f"✅ Preserved successful match: '{search_term}' → {match_info['product_code']}")
                        elif self.usage_tracker.get(search_term, {}).get("status") == "no_match":
                            # Use 9000 fallback for confirmed no matches
                            fallback_rows.append({
                                "unclear_term": search_term,
                                "matched_product_code": "9000",
                                "matched_product_name": search_term if search_term else "Tuote puuttuu hinnoittelusta",
                                "email_subject": term_dict.get("email_subject", ""),
                                "email_date": term_dict.get("email_date"),
                                "quantity": term_dict.get("quantity", "1"),
                                "explanation": term_dict.get("explanation", ""),
                                "ai_reasoning": "No matching product found in catalog",
                                "ai_confidence": 0,
                            })
                            self.logger.info(f"🔶 Confirmed no match: '{search_term}' → 9000")
                    # Log summary of preserved vs fallback results
                    successful_matches = len([r for r in fallback_rows if r["matched_product_code"] != "9000"])
                    fallback_matches = len([r for r in fallback_rows if r["matched_product_code"] == "9000"])
                    self.logger.info(f"📊 Final results: {successful_matches} preserved matches, {fallback_matches} fallback (9000) codes")
                    
                    return fallback_rows
    
    def _is_gemini_3_model(self, model_name: str = None) -> bool:
        """Check if using a Gemini 3.x model that requires thought signatures."""
        model = model_name or os.getenv('GEMINI_MODEL_ITERATION', '')
        return 'gemini-3' in model.lower()
    
    def _convert_content_with_signature(self, content: types.Content, is_gemini_3: bool = None) -> types.Content:
        """
        Convert Content to SDK format with thought_signature on PART level (not inside function_call).
        
        This follows the exact pattern from gemini.py:
            genai_client.types.Part(
                function_call=function_call,
                thought_signature=signature  # ON THE PART, not inside function_call!
            )
        """
        # CRITICAL: Import fresh inside function like gemini.py does
        from google import genai as genai_client
        
        DUMMY_SIGNATURE = "context_engineering_is_the_way_to_go"
        
        if is_gemini_3 is None:
            is_gemini_3 = self._is_gemini_3_model()
        
        try:
            if not hasattr(content, 'parts') or not content.parts:
                return content
            
            new_parts = []
            first_function_call = True
            
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    new_parts.append(genai_client.types.Part(text=part.text))
                    
                elif hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    
                    # Try to get existing signature from part (NOT from function_call!)
                    sig = getattr(part, 'thought_signature', None) or getattr(part, 'thoughtSignature', None)
                    
                    # Create FunctionCall without thought_signature
                    function_call_obj = genai_client.types.FunctionCall(
                        name=fc.name,
                        args=dict(fc.args) if fc.args else {}
                    )
                    
                    # For Gemini 3.x, first function call in a turn needs signature ON THE PART
                    if is_gemini_3 and first_function_call:
                        if sig:
                            self.logger.debug(f"✅ Using existing thought_signature for {fc.name}")
                            new_parts.append(genai_client.types.Part(
                                function_call=function_call_obj,
                                thought_signature=sig
                            ))
                        else:
                            self.logger.info(f"🔧 Adding dummy thought_signature for {fc.name} (Gemini 3.x)")
                            new_parts.append(genai_client.types.Part(
                                function_call=function_call_obj,
                                thought_signature=DUMMY_SIGNATURE
                            ))
                        first_function_call = False
                    else:
                        # Not Gemini 3 or not first function call
                        if sig:
                            new_parts.append(genai_client.types.Part(
                                function_call=function_call_obj,
                                thought_signature=sig
                            ))
                        else:
                            new_parts.append(genai_client.types.Part(function_call=function_call_obj))
                            
                elif hasattr(part, 'function_response') and part.function_response:
                    fr = part.function_response
                    new_parts.append(genai_client.types.Part(
                        function_response=genai_client.types.FunctionResponse(
                            name=fr.name,
                            response=dict(fr.response) if fr.response else {}
                        )
                    ))
                else:
                    # Keep original part
                    new_parts.append(part)
            
            return genai_client.types.Content(role=content.role, parts=new_parts)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error converting content with signature: {e}")
            import traceback
            self.logger.warning(f"Traceback: {traceback.format_exc()}")
            return content
    
    def _create_function_response_content(self, function_name: str, response_data: dict, tool_call_id: str = None) -> types.Content:
        """Create SDK Content for function response.
        
        Args:
            function_name: Name of the function that was called
            response_data: The response data from the function
            tool_call_id: The tool_call_id from the original function call (required for Claude compatibility
                         when there are multiple calls to the same function)
        """
        # CRITICAL: Import fresh inside function like gemini.py does
        from google import genai as genai_client
        
        # Include tool_call_id in response if provided (for OpenRouter/Claude compatibility)
        # This is needed when there are multiple calls to the same function
        if tool_call_id:
            response_with_id = {"__tool_call_id__": tool_call_id, **response_data}
        else:
            response_with_id = response_data
        
        return genai_client.types.Content(
            role="user",
            parts=[genai_client.types.Part(
                function_response=genai_client.types.FunctionResponse(
                    name=function_name,
                    response=response_with_id
                )
            )]
        )
    
    def _estimate_message_tokens(self, content: types.Content) -> int:
        """Estimate token count for a message.
        
        Uses simple heuristic: ~4 characters per token for text.
        Handles SDK Content objects.
        """
        try:
            token_count = 0
            
            # Handle SDK Content objects
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        token_count += len(part.text) // 4
                    elif hasattr(part, 'function_call') and part.function_call:
                        func_str = str(part.function_call)
                        token_count += len(func_str) // 4
                    elif hasattr(part, 'function_response') and part.function_response:
                        resp_str = str(part.function_response)
                        token_count += len(resp_str) // 4
                    else:
                        token_count += 50
            
            # Add overhead for message metadata
            token_count += 10
            
            return token_count
            
        except Exception as e:
            self.logger.warning(f"Error estimating tokens: {e}, using default estimate")
            return 1000  # Conservative default estimate
    
    def _manage_conversation_context(self, contents: List[types.Content], max_tokens: int = 7000) -> List[types.Content]:
        """Manage conversation context to stay within token limits.
        
        Implements a sliding window approach:
        - Always keeps the initial message
        - Removes oldest message pairs when approaching token limit
        - Preserves most recent messages for context continuity
        
        Args:
            contents: Current conversation messages
            max_tokens: Maximum allowed tokens (default 250k)
            
        Returns:
            Pruned contents list within token limits
        """
        if not contents or len(contents) <= 1:
            return contents
        
        # Estimate total tokens
        total_tokens = sum(self._estimate_message_tokens(msg) for msg in contents)
        
        # If under limit, return as-is
        if total_tokens <= max_tokens:
            return contents
        
        self.logger.warning(f"⚠️ Context size ({total_tokens} tokens) exceeds limit ({max_tokens} tokens), truncating...")
        # Log previews of the latest 4 messages to aid debugging
        try:
            preview_count = 4
            recent_messages = contents[-preview_count:] if len(contents) >= preview_count else contents[:]
            def _snippet_from_content(msg):
                snippets = []
                # Handle SDK Content objects
                if hasattr(msg, 'parts') and msg.parts:
                    for part in msg.parts:
                        if getattr(part, 'text', None):
                            snippets.append(part.text)
                        elif getattr(part, 'function_call', None):
                            fc = part.function_call
                            name = getattr(fc, 'name', '')
                            args = getattr(fc, 'args', {})
                            snippets.append(f"[CALL:{name} {args}]")
                        elif getattr(part, 'function_response', None):
                            fr = part.function_response
                            name = getattr(fr, 'name', '')
                            resp = getattr(fr, 'response', {})
                            snippets.append(f"[RESP:{name} {resp}]")
                summary = " ".join(snippets) if snippets else str(msg)
                summary = summary.replace("\n", " ")
                return summary[:100]
            for i, msg in enumerate(recent_messages[-preview_count:], 1):
                self.logger.info(f"🧵 Truncation preview {i}/{len(recent_messages)}: {_snippet_from_content(msg)}")
        except Exception as e:
            self.logger.debug(f"Truncation preview logging failed: {e}")
        
        # Keep first message and work backwards from most recent
        pruned_contents = [contents[0]]  # Always keep the initial trigger message
        pruned_tokens = self._estimate_message_tokens(contents[0])
        
        # Add messages from the end, working backwards
        # CRITICAL: For Claude/batch function calls, we must keep entire "turns" together:
        # - One assistant message with N tool_calls
        # - Followed by N function_response messages (one per tool_call)
        # If we split these, Claude gets "unexpected tool_use_id" errors
        i = len(contents) - 1
        temp_blocks = []
        
        def _is_function_response(msg):
            """Check if message contains a function_response"""
            if hasattr(msg, 'parts') and msg.parts:
                return any(getattr(p, 'function_response', None) for p in msg.parts)
            return False
        
        def _is_function_call(msg):
            """Check if message contains function_calls (tool_uses)"""
            if hasattr(msg, 'parts') and msg.parts:
                return any(getattr(p, 'function_call', None) for p in msg.parts)
            return False
        
        while i > 0:
            current_msg = contents[i]
            
            # Check if this is a function_response message
            if _is_function_response(current_msg):
                # Collect ALL consecutive function_response messages (they belong to one turn)
                turn_messages = []
                turn_tokens = 0
                
                # Walk backwards collecting all function_responses
                while i > 0 and _is_function_response(contents[i]):
                    turn_messages.insert(0, contents[i])
                    turn_tokens += self._estimate_message_tokens(contents[i])
                    i -= 1
                
                # Now i should point to the assistant message with tool_calls
                if i > 0 and _is_function_call(contents[i]):
                    assistant_msg = contents[i]
                    assistant_tokens = self._estimate_message_tokens(assistant_msg)
                    turn_messages.insert(0, assistant_msg)
                    turn_tokens += assistant_tokens
                    i -= 1
                
                # Check if adding this entire turn would exceed limit
                if pruned_tokens + turn_tokens > max_tokens * 0.9:
                    break
                
                # Add entire turn as one atomic block
                temp_blocks.append(turn_messages)
                pruned_tokens += turn_tokens
            else:
                # Single message (user message or other)
                current_tokens = self._estimate_message_tokens(current_msg)
                if pruned_tokens + current_tokens > max_tokens * 0.9:
                    break
                    
                temp_blocks.append([current_msg])
                pruned_tokens += current_tokens
                i -= 1
        
        # Add blocks in chronological order (reverse block order, keep internal order)
        for block in reversed(temp_blocks):
            pruned_contents.extend(block)
        
        removed_count = len(contents) - len(pruned_contents)
        self.logger.info(f"✂️ Truncated {removed_count} messages, keeping {len(pruned_contents)} messages ({pruned_tokens} tokens)")
        
        return pruned_contents
    
    def _build_products_context_prompt(self) -> str:
        """Build a context string showing all products to be matched."""
        context = "\n📋 PRODUCTS TO MATCH (Full Context):\n"
        context += "=" * 50 + "\n\n"
        
        # Show current mode
        context += f"🔍 CURRENT MODE: {self.current_mode}\n"
        if self.current_group:
            context += f"📁 CURRENT GROUP: {self.current_group}\n"
        context += "\n"
        
        # Count matched and unmatched
        matched = [t for t in self.all_products_context if t in self.matched_products]
        unmatched = [t for t in self.all_products_context if t not in self.matched_products]
        
        context += f"✅ MATCHED ({len(matched)}/{len(self.all_products_context)}):\n"
        for term in matched:
            info = self.matched_products[term]
            usage = self.usage_tracker.get(term, {})
            context += f"  • {term} → {info['product_code']} ({usage.get('calls', 0)} iterations used)\n"
        
        context += f"\n❌ NOT MATCHED YET ({len(unmatched)}/{len(self.all_products_context)}):\n"
        for term in unmatched:
            usage = self.usage_tracker.get(term, {})
            search_count = len(usage.get("searches", []))
            search_types = usage.get("search_types", [])
            search_types_str = ", ".join(search_types) if search_types else "none"
            context += f"  • {term} ({usage.get('calls', 0)}/{usage.get('max_calls', 20)} iterations, {search_count} searches: {search_types_str})\n"

        context += "\n" + "=" * 50 + "\n"
        return context
    
    def _get_batch_search_functions(self) -> List[Dict]:
        """Get enhanced function declarations for batch matching."""
        # Start with all existing functions
        functions = [
            {
                "name": "search_by_product_codes",
                "description": "Search for products by their exact product codes. Use when you have specific product codes to look up (e.g., from customer inquiry). Returns full product details for each code found.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_codes": {
                            "type": "array",
                            "description": "List of product codes to search for (e.g., ['12345', '67890'])",
                            "items": {"type": "string"}
                        },
                        "for_terms": {
                            "type": "array",
                            "description": "Optional: specific unclear terms this search is for",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["product_codes"]
                }
            },
            {
                "name": "wildcard_search",
                "description": "Perform wildcard search in GLOBAL product catalog using patterns like %pump%, %venttiili%. NOTE: Automatically exits any product group to search globally.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search pattern with % wildcards (e.g., %kiertovesi%, %pump%25%)"
                        },
                        "for_terms": {
                            "type": "array",
                            "description": "Optional: specific unclear terms this search is for",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "semantic_search",
                "description": "Perform semantic search using OpenAI embeddings. ONLY AVAILABLE IN GLOBAL MODE - will fail in group mode!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Descriptive search term (e.g., kiertovesipumppu, lämmönvaihdin)"
                        },
                        "for_terms": {
                            "type": "array",
                            "description": "Optional: specific unclear terms this search is for",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "google_search",
                "description": "Search Google for product names. Available in both modes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Product term to search on Google"
                        }
                    },
                    "required": ["search_term"]
                }
            },
            {
                "name": "select_product_group",
                "description": "Enter a product group for focused searching. Do NOT select main groups (101, 102, 103).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_code": {
                            "type": "integer",
                            "description": "Group code ID (not 101, 102, or 103)"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Why this group was selected"
                        }
                    },
                    "required": ["group_code", "reasoning"]
                }
            },
            {
                "name": "search_products_in_group",
                "description": "Search within current group. Must select_product_group first!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name_filter": {
                            "type": "string",
                            "description": "Filter term for name/extra_name/searchcode"
                        },
                        "sku_filter": {
                            "type": "string",
                            "description": "Filter by SKU/product code"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "sort_products_in_group",
                "description": "Sort and display products from a specific group. Shows top 100 sorted by name, price, or SKU.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_code": {
                            "type": "integer",
                            "description": "Group code ID to sort products from"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["name", "price", "sku"],
                            "description": "Field to sort products by"
                        }
                    },
                    "required": ["group_code", "sort_by"]
                }
            },
            {
                "name": "exit_to_global",
                "description": "Exit group and return to GLOBAL mode",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "match_product_codes",
                "description": "Match multiple products at once. Use for EXACT matches AND CLOSEST matches when no exact match exists. System will calculate confidence automatically (15-30% = closest match needing review, 70%+ = good match, 90%+ = exact match).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "matches": {
                            "type": "array",
                            "description": "Array of product matches (exact or closest available)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "unclear_term": {
                                        "type": "string",
                                        "description": "The original unclear term"
                                    },
                                    "product_code": {
                                        "type": "string",
                                        "description": "Matched product code (best available option)"
                                    },
                                    "reasoning": {
                                        "type": "string",
                                        "description": "Why this match was selected"
                                    },
                                    "confidence": {
                                        "type": "integer",
                                        "description": "Confidence score for the match"
                                    }
                                },
                                "required": ["unclear_term", "product_code", "reasoning", "confidence"]
                            }
                        }
                    },
                    "required": ["matches"]
                }
            },
            {
                "name": "use_fallback_9000",
                "description": "Use 9000 fallback code for products that cannot be matched",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "unclear_terms": {
                            "type": "array",
                            "description": "Terms to assign 9000 code",
                            "items": {"type": "string"}
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Why these couldn't be matched"
                        }
                    },
                    "required": ["unclear_terms", "reasoning"]
                }
            }
        ]
        
        # Add group-based matcher functions if available
        if self.group_based_matcher:
            functions.append({
                "name": "switch_product_group",
                "description": "Switch to different product group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "group_code": {
                            "type": "integer",
                            "description": "New group code (not 101, 102, or 103)"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Reason for switching"
                        }
                    },
                    "required": ["group_code", "reasoning"]
                }
            })
        
        return functions
    
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
    
    async def _execute_batch_function(self, function_name: str, function_args: Dict) -> Dict:
        """Execute functions in batch context with usage tracking."""
        # Build deterministic signature and block immediate repetitions; hard-stop after 5th identical call
        try:
            canonical_args = json.dumps(function_args or {}, sort_keys=True, ensure_ascii=False)
        except Exception:
            canonical_args = str(function_args)
        current_signature = f"{function_name}:{canonical_args}"

        if getattr(self, '_last_batch_function_signature', None) == current_signature:
            # Increment repeat counter on exact consecutive duplicate
            self._last_batch_function_repeat_count = getattr(self, '_last_batch_function_repeat_count', 0) + 1
            if self._last_batch_function_repeat_count >= 5:
                # Hard stop the batch gracefully
                self._forced_stop_due_to_repetition = True
                return {
                    "response": {
                        "result": "HARD STOP: SAME FUNCTION WITH SAME PARAMETERS CALLED 5 TIMES IN A ROW. STOP NOW AND SWITCH STRATEGY."
                    },
                    "batch_complete": True
                }
            return {"response": {"result": "REPETITION NOTICED! ATTENTION: SWITCH FUNCTION IMMEDIATELY; YOU ARE CALLING THE SAME FUNCTION OVER AND OVER AGAIN, CALL SOME OTHER FUNCTION TO PREVENT INFINITE LOOP"}}
        else:
            # New signature: reset counter and record
            self._last_batch_function_signature = current_signature
            self._last_batch_function_repeat_count = 1

        # Track usage for specific terms if provided
        for_terms = function_args.get("for_terms", [])
        for term in for_terms:
            if term in self.usage_tracker:
                self.usage_tracker[term]["calls"] += 1

        # Track search attempts for validation (for all search functions)
        if function_name in ["search_by_product_codes", "wildcard_search", "semantic_search", "google_search", "search_products_in_group"]:
            for term in for_terms:
                if term in self.usage_tracker:
                    self.usage_tracker[term]["searches"].append(function_name)
                    if function_name not in self.usage_tracker[term]["search_types"]:
                        self.usage_tracker[term]["search_types"].append(function_name)

        # Handle search functions
        if function_name == "search_by_product_codes":
            product_codes = function_args.get("product_codes", [])
            self.logger.info(f"🔢 Batch product code search: {len(product_codes)} codes")
            
            # Product code search works in both GLOBAL and GROUP modes
            results_df = await self._search_by_product_codes(product_codes)
            if results_df is not None and not results_df.empty:
                results_text = self._format_df_results(results_df.head(20))
                not_found_count = len(product_codes) - len(results_df)
                status_msg = f"Found {len(results_df)}/{len(product_codes)} products"
                if not_found_count > 0:
                    status_msg += f" ({not_found_count} codes not found)"
                return {"response": {"result": f"{status_msg}:\n{results_text}"}}
            
            return {"response": {"result": f"No products found for the provided {len(product_codes)} product codes"}}
        
        elif function_name == "wildcard_search":
            query = function_args.get("query", "")
            self.logger.info(f"🔍 Batch wildcard search: '{query}'")
            
            # Always exit to global mode for wildcard search
            mode_change_msg = ""
            if self.current_mode != "GLOBAL":
                previous_group = self.current_group
                previous_mode = self.current_mode
                self.current_mode = "GLOBAL"
                self.current_group = None
                mode_change_msg = f"📍 AUTO-EXITED from {previous_mode} to GLOBAL mode for wildcard search.\n"
                self.logger.info(f"🌍 Auto-exited {previous_mode} for wildcard search")
            
            # Always do global search (never search within group for wildcard)
            results_df = await self._local_wildcard_search(query)
            if results_df is not None and not results_df.empty:
                results_text = self._format_df_results(results_df.head(20))
                return {"response": {"result": mode_change_msg + f"Found {len(results_df)} products:\n{results_text}"}}
            
            return {"response": {"result": mode_change_msg + f"No results for '{query}'"}}
        
        elif function_name == "semantic_search":
            if self.current_mode != "GLOBAL":
                return {"response": {"result": "❌ semantic_search is NOT available in group mode! Use wildcard_search or exit_to_global first."}}
            
            query = function_args.get("query", "")
            self.logger.info(f"🧠 Batch semantic search: '{query}'")
            
            results_df = self._semantic_search_product_catalogue(query, top_k=15)
            if results_df is not None and not results_df.empty:
                results_text = self._format_df_results(results_df.head(10))
                return {"response": {"result": f"Found {len(results_df)} semantic matches:\n{results_text}"}}
            
            return {"response": {"result": f"No semantic matches for '{query}'"}}
        
        elif function_name == "select_product_group":
            if not self.group_based_matcher:
                return {"response": {"result": "Group navigation not available"}}
            
            group_code = function_args.get("group_code")
            reasoning = function_args.get("reasoning", "")
            
            # Load product groups if needed
            if not hasattr(self, 'product_groups'):
                self.product_groups = self.group_based_matcher._load_product_groups()
            
            # Validate and set group
            group_info = self.group_based_matcher._get_group_info_by_code(group_code)
            if group_info:
                self.current_group = group_code
                self.current_mode = f"GROUP_{group_code}"
                self.logger.info(f"📁 Entered group {group_code}: {group_info['name']}")
                
                # Fetch initial products
                results = await self.group_based_matcher._fetch_products_from_group(group_code, limit=200)
                if results and results.get('success'):
                    products = results.get('products', [])
                    display_products = products[:100]
                    results_text = self._format_search_results(display_products)
                    
                    # Check if there are more products than displayed
                    total_products = len(products)
                    if total_products > 100:
                        prefix = f"Showing only first 100 products, {total_products - 100} more products exist in this group.\n\n"
                    else:
                        prefix = ""
                    
                    return {"response": {"result": f"Entered group {group_info['name']}. {total_products} products available:\n{prefix}{results_text}"}}
            
            return {"response": {"result": f"Invalid group code {group_code}"}}
        
        elif function_name == "search_products_in_group":
            if not self.current_group or not self.group_based_matcher:
                return {"response": {"result": "No group selected. Use select_product_group first."}}
            
            name_filter = function_args.get("name_filter")
            sku_filter = function_args.get("sku_filter")
            
            results = await self.group_based_matcher._fetch_products_from_group(
                self.current_group,
                limit=200,
                name_filter=name_filter,
                sku_filter=sku_filter
            )
            
            if results and results.get('success'):
                products = results.get('products', [])
                display_products = products[:200]
                results_text = self._format_search_results(display_products)
                
                # Check if there are more products than displayed
                total_products = len(products)
                if total_products > 200:
                    prefix = f"Showing only first 200 products, {total_products - 200} more products exist in this group.\n\n"
                else:
                    prefix = ""
                
                return {"response": {"result": f"Found {total_products} products in group:\n{prefix}{results_text}"}}
            
            return {"response": {"result": "No products found with those filters"}}
        
        elif function_name == "sort_products_in_group":
            if not self.group_based_matcher:
                return {"response": {"result": "Group-based sorting not available"}}
            
            group_code = function_args.get("group_code")
            sort_by = function_args.get("sort_by", "name")
            
            self.logger.info(f"📊 Sorting products in group {group_code} by {sort_by}")
            
            # Use _fetch_products_from_group which routes to repository or legacy automatically
            result = await self.group_based_matcher._fetch_products_from_group(
                group_code, limit=200, sort_by=sort_by
            )
            sorted_products = result.get('products', []) if result.get('success') else []
            
            if sorted_products:
                display_products = sorted_products[:100]
                results_text = self._format_search_results(display_products)
                
                # Check if there are more products than displayed
                total_products = len(sorted_products)
                if total_products > 100:
                    prefix = f"Showing only first 100 products, {total_products - 100} more products exist in this group.\n\n"
                else:
                    prefix = ""
                
                total_text = f"Top {total_products} products in group {group_code} sorted by {sort_by}:\n{prefix}{results_text}"
                return {"response": {"result": total_text}}
            else:
                return {"response": {"result": f"No products found in group {group_code}"}}
        
        elif function_name == "exit_to_global":
            if self.current_mode == "GLOBAL":
                self.logger.info("🌍 Already in GLOBAL mode – preventing redundant exit_to_global")
                return {"response": {"result": "ALREADY IN GLOBAL MODE. DO NOT CALL exit_to_global AGAIN. Choose another tool (wildcard_search, semantic_search, select_product_group, match_product_codes)."}}
            self.current_mode = "GLOBAL"
            self.current_group = None
            self.logger.info("🌍 Returned to GLOBAL mode")
            return {"response": {"result": "Exited group. Now in GLOBAL mode - semantic_search is available again."}}
        
        elif function_name == "match_product_codes":
            matches = function_args.get("matches", [])
            self.logger.info(f"🎯 Batch matching {len(matches)} products")
            
            # Log all products being attempted for transparency
            for i, match in enumerate(matches, 1):
                unclear_term = match.get("unclear_term", "unknown")
                product_code = match.get("product_code", "unknown")
                self.logger.info(f"   {i}. Attempting: '{unclear_term}' → {product_code}")
            
            successful_matches = []
            failed_matches = []
            
            for match in matches:
                unclear_term = match.get("unclear_term")
                product_code = match.get("product_code")
                reasoning = match.get("reasoning") or "Tuote valittu hakutulosten perusteella"
                confidence = match.get("confidence", 0)
                print(f"Confidence in match_product_codes for product code {product_code}: {confidence}")
                if unclear_term in self.all_products_context:
                    # Check if already matched
                    if unclear_term in self.matched_products:
                        continue  # Skip already matched products

                    # Validate product exists
                    validation = await self._validate_product_code(product_code)
                    if validation:
                        # Accept ALL matches, but flag low confidence ones for review
                        self.matched_products[unclear_term] = {
                            "product_code": product_code,
                            "product_name": validation.get("name", ""),
                            "reasoning": reasoning,
                            "confidence": confidence
                        }
                        self.usage_tracker[unclear_term]["status"] = "matched"
                        successful_matches.append(unclear_term)

                        # Log with appropriate emoji based on confidence
                        if confidence >= 90:
                            self.logger.info(f"✅ EXACT MATCH ({confidence}%): {unclear_term} → {product_code}")
                        elif confidence >= 70:
                            self.logger.info(f"✅ GOOD MATCH ({confidence}%): {unclear_term} → {product_code}")
                        elif confidence >= 50:
                            self.logger.warning(f"⚠️ CLOSEST MATCH ({confidence}%) - NEEDS REVIEW: {unclear_term} → {product_code}")
                        else:
                            self.logger.warning(f"⚠️ LOW CONFIDENCE ({confidence}%) - MANUAL CHECK REQUIRED: {unclear_term} → {product_code}")
                    else:
                        failed_matches.append(f"{unclear_term} → {product_code}")
                        self.logger.info(f"❌ Validation failed: {unclear_term} → {product_code}")
            
            # Update context
            context = self._build_products_context_prompt()
            
            # Provide feedback about failures
            result_msg = f"✅ Matched {len(successful_matches)} products successfully."
            if failed_matches:
                result_msg += f"\n❌ {len(failed_matches)} matches failed validation - try different search strategies for: {', '.join(failed_matches)}"
            
            return {"response": {"result": f"{result_msg}\n{context}"}}
        
        elif function_name == "use_fallback_9000":
            unclear_terms = function_args.get("unclear_terms", [])
            reasoning = function_args.get("reasoning") or "Tuotetta ei löytynyt luettelosta"

            # VALIDATION: Enforce minimum search requirements before allowing fallback
            blocked_terms = []
            for term in unclear_terms:
                if term in self.usage_tracker:
                    tracker = self.usage_tracker[term]
                    search_count = len(tracker.get("searches", []))
                    unique_search_types = len(tracker.get("search_types", []))

                    # Require at least 3 searches AND at least 2 different search types
                    if search_count < 3:
                        blocked_terms.append(f"{term} (only {search_count}/3 searches)")
                    elif unique_search_types < 2:
                        blocked_terms.append(f"{term} (only {unique_search_types}/2 search types)")

            if blocked_terms:
                error_msg = (
                    f"❌ FALLBACK BLOCKED - Insufficient search attempts:\n"
                    f"{', '.join(blocked_terms)}\n\n"
                    f"REQUIREMENTS:\n"
                    f"• Minimum 3 different searches per product\n"
                    f"• Minimum 2 different search types (wildcard, semantic, google)\n\n"
                    f"CONTINUE SEARCHING with different strategies before using fallback!"
                )
                self.logger.warning(f"⚠️ Blocked premature fallback for: {blocked_terms}")
                context = self._build_products_context_prompt()
                return {"response": {"result": f"{error_msg}\n\n{context}"}}

            # Validation passed - proceed with fallback
            for term in unclear_terms:
                if term in self.all_products_context:
                    # Use the original term as product name instead of hardcoded Finnish text
                    self.matched_products[term] = {
                        "product_code": "9000",
                        "product_name": term if term else "Tuote puuttuu hinnoittelusta",  # Use the AI-provided/original term name
                        "reasoning": reasoning
                    }
                    self.usage_tracker[term]["status"] = "no_match"
                    self.logger.info(f"🔶 Fallback 9000: {term}")
            
            context = self._build_products_context_prompt()
            return {"response": {"result": f"Applied 9000 fallback to {len(unclear_terms)} products.\n{context}"}}
        
        elif function_name == "google_search":
            # Reuse existing Google search implementation
            search_term = function_args.get("search_term", "")
            self.logger.info(f"Google searching for '{search_term}' in Finnish market")
            google_result = self._google_search_product(search_term)
            
            if google_result.get("success"):
                results_data = google_result.get("results", {})
                organic_count = results_data.get("organic_count", 0)
                top_results = results_data.get("top_results", [])
                related_terms = results_data.get("related_terms", [])
                
                if organic_count > 0:
                    results_text = f"Google found {organic_count} results for '{search_term}':\n\n"
                    
                    # Show top results with snippets
                    if top_results:
                        results_text += "TOP RESULTS:\n"
                        for i, result in enumerate(top_results[:3], 1):
                            title = result.get("title", "")
                            snippet = result.get("snippet", "")[:100] + "..." if len(result.get("snippet", "")) > 100 else result.get("snippet", "")
                            results_text += f"{i}. {title}\n   {snippet}\n"
                        results_text += "\n"
                    
                    # Show related terms
                    if related_terms:
                        results_text += "RELATED TERMS:\n"
                        for term in related_terms:
                            results_text += f"- {term}\n"
                    
                    self.logger.info(f"Google found {organic_count} organic results for '{search_term}'")
                    return {"response": {"result": results_text}}
            
            return {"response": {"result": "No Google results found"}}
        
        else:
            return {"response": {"result": f"Unknown function: {function_name}"}}
    
    def _format_search_results(self, products: List[Dict]) -> str:
        """Format product search results for display, including stock and sales data."""
        if not products:
            return "No products"
        
        results = []
        for p in products:
            sku = p.get('sku', p.get('product_code', 'N/A'))
            name = p.get('name', p.get('product_name', 'N/A'))
            extra = p.get('extra_name', '')
            
            line = f"- {sku} | {name}"
            if extra:
                line += f" | {extra}"
            
            # Add stock and sales indicators if data is available and > 0
            total_stock = p.get('total_stock')
            yearly_sales = p.get('yearly_sales_qty')
            
            indicators = []
            if yearly_sales is not None and yearly_sales > 0:
                indicators.append(f"Sales: {int(yearly_sales)} pcs/year")
            if total_stock is not None and total_stock > 0:
                indicators.append(f"Stock: {int(total_stock)} pcs")
            
            if indicators:
                line += f" [{', '.join(indicators)}]"
            
            results.append(line)
        
        return "\n".join(results)
    
    def _format_df_results(self, df) -> str:
        """Format DataFrame results for display, including stock, sales, and all CSV fields.
        
        When 'all_fields' column is present (from CSV wildcard search), shows complete
        column:value pairs so the agent can see which column contains which value.
        """
        if df is None or df.empty:
            return "No results"
        
        results = []
        
        # Check if we have 'all_fields' column (from CSV search with full column info)
        has_all_fields = 'all_fields' in df.columns
        
        for _, row in df.iterrows():
            sku = row.get('sku', row.get('Tuotekoodi', 'N/A'))
            name = row.get('name', row.get('Tuotenimi', 'N/A'))
            
            # Build the line with stock and sales info if available and > 0
            line = f"- {sku} | {name}"
            
            # Include stock and sales data if available and > 0
            total_stock = row.get('total_stock')
            yearly_sales = row.get('yearly_sales_qty')
            
            indicators = []
            if yearly_sales is not None and yearly_sales > 0:
                indicators.append(f"Sales: {int(yearly_sales)} pcs/year")
            if total_stock is not None and total_stock > 0:
                indicators.append(f"Stock: {int(total_stock)} pcs")
            
            if indicators:
                line += f" [{', '.join(indicators)}]"
            
            # If all_fields is available, add it on a new line for full visibility
            if has_all_fields and row.get('all_fields'):
                line += f"\n    📋 {row['all_fields']}"
            
            results.append(line)
        
        return "\n".join(results)
    
    async def _ensure_lemonsoft_initialized(self):
        """Ensure Lemonsoft client is initialized before API calls."""
        if not hasattr(self.lemonsoft_client, 'client') or self.lemonsoft_client.client is None:
            self.logger.info("Initializing Lemonsoft API client...")
            await self.lemonsoft_client.initialize()
            self.logger.info("Lemonsoft API client initialized successfully")
        else:
            # Ensure token is valid and refresh if needed
            try:
                await self.lemonsoft_client.ensure_ready()
            except Exception as e:
                self.logger.info(f"Lemonsoft ensure_ready failed: {e}, re-initializing…")
                await self.lemonsoft_client.initialize()

    async def _validate_product_code(self, product_code: str) -> Optional[Dict]:
        """Validate that a product code exists in the database.
        
        Routes to product_repository if available (ERP-agnostic),
        otherwise falls back to Lemonsoft API/SQL.
        """
        try:
            # Use product repository if available (ERP-agnostic approach)
            if self.product_repository:
                try:
                    self.logger.debug(f"🔍 Validating product code via repository: {product_code}")
                    product = await self.product_repository.get_by_code(product_code)
                    if product:
                        self.logger.debug(f"✅ Product found via repository: {product.code}")
                        return {
                            'id': product.code,
                            'sku': product.code,
                            'name': product.name or '',
                            'extra_name': product.extra_name if hasattr(product, 'extra_name') else '',
                            'price': product.unit_price if hasattr(product, 'unit_price') else 0.0,
                        }
                    else:
                        self.logger.debug(f"❌ Product not found via repository: {product_code}")
                        return None
                except Exception as e:
                    self.logger.warning(f"Product repository validation failed for {product_code}: {e}")
                    # Fall through to legacy methods if repository fails
            
            # Legacy: Ensure Lemonsoft client is initialized
            if self.lemonsoft_client:
                await self._ensure_lemonsoft_initialized()

                # Try API validation (with one retry on auth failure)
                for attempt in range(2):
                    try:
                        response = await self.lemonsoft_client.get('/api/products', params={'filter.sku': product_code})
                        status = getattr(response, 'status_code', None)
                        if status == 200:
                            try:
                                data = response.json()
                            except Exception as e:
                                self.logger.info(f"Validation JSON parse error for {product_code}: {e}")
                                data = None
                            if isinstance(data, dict):
                                results = data.get('results', []) or []
                                if results:
                                    # API confirms existence
                                    return results[0]
                            # 200 but empty results → break to fallback
                            break
                        elif status in (401, 403):
                            # Re-auth once
                            self.logger.info(f"Validation API auth failed ({status}) for {product_code}, re-initializing and retrying…")
                            await self.lemonsoft_client.initialize()
                            continue
                        else:
                            # Non-200 → break to fallback
                            try:
                                preview = response.text[:200] if hasattr(response, 'text') and isinstance(response.text, str) else ''
                            except Exception:
                                preview = ''
                            self.logger.info(f"Validation API returned status {status} for {product_code}. Preview: {preview}")
                            break
                    except Exception as api_e:
                        self.logger.info(f"Validation API error for {product_code}: {type(api_e).__name__}: {api_e}")
                        # Retry only once (attempt==0). On second failure, fall back to SQL
                        continue

            # Fallback to direct SQL existence check (only if not using product_repository)
            if not self.product_repository:
                try:
                    query = (
                        "SELECT TOP 1 p.product_id, p.product_code, p.product_description, p.product_description2 "
                        "FROM products p WHERE p.product_code = ?"
                    )
                    rows = await self._execute_sql_query(query, [product_code])
                    if rows:
                        row = rows[0]
                        # Construct minimal product dict compatible with callers
                        return {
                            'id': row.get('product_id', ''),
                            'sku': row.get('product_code', product_code),
                            'name': row.get('product_description', ''),
                            'extra_name': row.get('product_description2', ''),
                        }
                except Exception as sql_e:
                    self.logger.info(f"Validation SQL error for {product_code}: {type(sql_e).__name__}: {sql_e}")

        except Exception as e:
            self.logger.error(f"Failed to validate product code {product_code}: {e}")

        return None

    # --------------------------- fallback system ---------------------------
    def _load_filtered_products(self):
        """Load filtered products CSV and embeddings for fallback matching."""
        if self.filtered_products_df is not None:
            return  # Already loaded
        
        # Load filtered products CSV
        if not os.path.exists(self.filtered_products_csv_path):
            self.logger.warning(f"⚠️ Filtered products CSV not found: {self.filtered_products_csv_path}")
            return
        
        self.logger.info(f"📂 Loading fallback products from {self.filtered_products_csv_path}")
        self.filtered_products_df = pd.read_csv(self.filtered_products_csv_path, encoding="utf-8")
        
        # Clean product names and add lowercase column for searching
        self.filtered_products_df = self.filtered_products_df.dropna(subset=['product_name'])
        self.filtered_products_df['product_name'] = self.filtered_products_df['product_name'].astype(str).str.strip()
        self.filtered_products_df = self.filtered_products_df[self.filtered_products_df['product_name'] != '']
        self.filtered_products_df['product_name_lower'] = self.filtered_products_df['product_name'].str.lower()
        
        self.logger.info(f"✅ Loaded {len(self.filtered_products_df)} fallback products")
        
        # Load embeddings
        embeddings_path = f"{self.filtered_products_csv_path.with_suffix('')}.openai_embeddings.npy"
        if os.path.exists(embeddings_path):
            try:
                self.filtered_product_embeddings = np.load(embeddings_path)
                self.logger.info(f"✅ Loaded fallback embeddings with shape: {self.filtered_product_embeddings.shape}")
                
                # Verify alignment
                if len(self.filtered_products_df) != self.filtered_product_embeddings.shape[0]:
                    self.logger.warning(f"⚠️ Mismatch in fallback data: {len(self.filtered_products_df)} products vs {self.filtered_product_embeddings.shape[0]} embeddings")
                    # Align to minimum
                    min_len = min(len(self.filtered_products_df), self.filtered_product_embeddings.shape[0])
                    self.filtered_products_df = self.filtered_products_df.head(min_len)
                    self.filtered_product_embeddings = self.filtered_product_embeddings[:min_len]
                    self.logger.info(f"🔧 Aligned fallback data to {min_len} items")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load fallback embeddings: {e}")
                self.filtered_product_embeddings = None
        else:
            self.logger.warning(f"⚠️ Fallback embeddings not found: {embeddings_path}")

    async def _fallback_wildcard_search(self, pattern: str):
        """Search in filtered products using wildcard pattern."""
        self._load_filtered_products()
        
        if self.filtered_products_df is None or pattern is None:
            return None

        # Convert simple "*" wildcard to regex
        regex = (
            "^" + re.escape(pattern.lower()).replace("\\*", ".*") if "*" in pattern else f".*{re.escape(pattern.lower())}.*"
        )
        try:
            return self.filtered_products_df[
                self.filtered_products_df["product_name_lower"].str.match(regex, na=False)
            ]
        except re.error as e:
            self.logger.debug(f"Regex error for fallback pattern '{pattern}': {e}")
            return None

    def _fallback_semantic_search(self, search_term: str, top_k: int = 10, min_similarity: float = 0.6):
        """Search in filtered products using semantic similarity with higher confidence threshold."""
        self._load_filtered_products()
        
        if (self.filtered_products_df is None or 
            self.filtered_product_embeddings is None or 
            not search_term):
            return None

        try:
            # Get query embedding
            query_embeddings = self._get_openai_embedding([search_term])
            query_emb = query_embeddings[0]
        except Exception as e:
            self.logger.error(f"Failed to get fallback query embedding for '{search_term}': {e}")
            return None

        query_vec = np.asarray(query_emb, dtype="float32")
        
        # Calculate cosine similarities
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        product_norms = self.filtered_product_embeddings / (
            np.linalg.norm(self.filtered_product_embeddings, axis=1, keepdims=True) + 1e-8
        )
        similarities = np.dot(product_norms, query_norm)

        # Get top-k indices
        top_idx = similarities.argsort()[::-1][:top_k]
        
        # Apply high confidence threshold for fallback
        valid_indices = [i for i in top_idx if similarities[i] >= min_similarity]
        
        if len(valid_indices) == 0:
            self.logger.debug(f"❌ No fallback semantic matches above {min_similarity:.3f} threshold for '{search_term}'")
            return None

        result_df = self.filtered_products_df.iloc[valid_indices].copy()
        result_df["similarity"] = similarities[valid_indices]
        result_df = result_df.sort_values('similarity', ascending=False)

        max_sim = similarities[valid_indices[0]] if len(valid_indices) > 0 else 0.0
        self.logger.debug(f"🔍 Fallback semantic search for '{search_term}': max similarity = {max_sim:.3f}")

        return result_df

    async def _fallback_match(self, search_term: str, usage_context: Optional[str] = None):
        """Try to match using filtered products as fallback with high confidence requirements."""
        self.logger.info(f"🔄 Trying fallback matching for: '{search_term}'")
        
        # First try with high-confidence agentic search on filtered products
        fallback_candidates = await self._agentic_fallback_search(search_term, usage_context)
        
        if fallback_candidates is not None and not fallback_candidates.empty:
            # Found match in filtered products
            if len(fallback_candidates) == 1:
                row = fallback_candidates.iloc[0]
                result = {
                    "matched_product_code": self.fallback_product_code,
                    "matched_product_name": str(row["product_name"]).strip(),
                }
                self.logger.info(f"✅ Fallback match found: {result['matched_product_code']} - {result['matched_product_name']}")
                return result
            else:
                # Multiple candidates, ask Gemini to select best
                best_name = self._gemini_select_best_fallback(search_term, fallback_candidates, usage_context)
                if best_name:
                    result = {
                        "matched_product_code": self.fallback_product_code,
                        "matched_product_name": best_name,
                    }
                    self.logger.info(f"✅ Fallback match selected: {result['matched_product_code']} - {result['matched_product_name']}")
                    return result
        
        # Final fallback: generate new product name
        self.logger.info(f"🎯 Generating new product name for: '{search_term}'")
        generated_name = self._generate_product_name(search_term, usage_context)
        if generated_name:
            result = {
                "matched_product_code": self.fallback_product_code,
                "matched_product_name": generated_name,
            }
            self.logger.info(f"✅ Generated product: {result['matched_product_code']} - {result['matched_product_name']}")
            return result
        
        return None

    async def _agentic_fallback_search(self, search_term: str, usage_context: Optional[str] = None):
        """Agentic search using filtered products with high confidence requirements."""
        max_iterations = max(3, self.get_dynamic_iteration_limit(search_term, usage_context) // 2)  # Half of main search iterations, min 3
        searched_queries = set()
        
        system_instruction = (
            "Sinä olet LVI-tuotehakurobotti joka käyttää varakatalogia. "
            "Ole ERITTÄIN VAROVAINEN - valitse tuote vain jos olet VARMA että se on sama tuote! "
            "Vastaa TARKASTI yhteen näistä:\n"
            "SEARCH:<haku> - tee wildcard-haku varakatalogista\n"
            "SEMANTIC:<haku> - tee semanttinen haku (vaatii korkea varmuus >0.6)\n"
            "MATCH:<product_name> - valitse tuotteen nimi tuloksista (vain jos VARMA)\n"
            "STOP - lopeta jos et ole VARMA mistään tuotteesta\n\n"
            "TÄRKEÄÄ: Valitse vain jos tuote on selvästi sama! Epävarmuus = STOP.\n"
        )

        conversation_history = f"{system_instruction}\n\nTermi: {search_term}\n"
        if usage_context:
            conversation_history += f"\nKonteksti: {usage_context[:3000]}\n"
        
        for iteration in range(max_iterations):
            self.logger.debug(f"🔄 Fallback iteration {iteration + 1}/{max_iterations} for: {search_term}")
            
            try:
                self.api_calls_made += 1
                config = types.GenerateContentConfig(temperature=0.4)  # Lower temperature for more conservative choices
                response = self._retry_llm_request(
                    self.gemini_client.models.generate_content,
                    model=Config.GEMINI_MODEL,
                    contents=conversation_history,
                    config=config,
                )

                if not response or not response.text:
                    break

                agent_reply = response.text.strip()
                if agent_reply.startswith("Agent:"):
                    agent_reply = agent_reply[6:].strip()
                
                self.logger.debug(f"💬 Fallback agent reply: {agent_reply}")
                
                # Parse agent response
                if agent_reply.startswith("SEARCH:"):
                    query = agent_reply[7:].strip()
                    signature = f"wildcard:{query}"
                    if signature in searched_queries:
                        continue
                    searched_queries.add(signature)
                    
                    results_df = await self._fallback_wildcard_search(query)
                    if results_df is None or results_df.empty:
                        conversation_history += f"Agent: {agent_reply}\nUser: Ei tuloksia varakatalogista haulle '{query}'. STOP jos et löydä sopivaa.\n"
                    else:
                        limited_results = results_df.head(8)  # Fewer results for fallback
                        results_text = "\n".join(
                            f"- {row.product_name}" for _, row in limited_results.iterrows()
                        )
                        conversation_history += (
                            f"Agent: {agent_reply}\nUser: Varakatalogitulokset '{query}':\n{results_text}\n"
                            "MATCH:<product_name> vain jos VARMA että sama tuote!\n"
                        )
                
                elif agent_reply.startswith("SEMANTIC:"):
                    query = agent_reply[9:].strip()
                    signature = f"semantic:{query}"
                    if signature in searched_queries:
                        continue
                    searched_queries.add(signature)

                    results_df = self._fallback_semantic_search(query, top_k=8, min_similarity=0.6)
                    if results_df is None or results_df.empty:
                        conversation_history += f"Agent: {agent_reply}\nUser: Ei korkean varmuuden semanttisia tuloksia '{query}'. STOP.\n"
                    else:
                        limited_results = results_df.head(5)
                        results_text = "\n".join(
                            f"- {row.product_name} (similarity: {row.similarity:.3f})" 
                            for _, row in limited_results.iterrows()
                        )
                        conversation_history += (
                            f"Agent: {agent_reply}\nUser: Korkean varmuuden tulokset '{query}':\n{results_text}\n"
                            "MATCH:<product_name> vain jos similarity >0.6 JA VARMA!\n"
                        )
                
                elif agent_reply.startswith("MATCH:"):
                    product_name = agent_reply[6:].strip()
                    
                    # Validate the product name exists in filtered catalogue
                    matching_row = self.filtered_products_df[
                        self.filtered_products_df["product_name"].str.strip() == product_name
                    ]
                    
                    if not matching_row.empty:
                        self.logger.debug(f"✅ Valid fallback match found: {product_name}")
                        return matching_row.iloc[0:1]  # Return as DataFrame
                    else:
                        conversation_history += f"Agent: {agent_reply}\nUser: Tuote '{product_name}' ei löydy varakatalogista. Tarkista nimi tai STOP.\n"
                
                elif agent_reply.upper().strip() == "STOP":
                    self.logger.debug(f"🛑 Fallback agent decided to stop for: {search_term}")
                    break
                
                else:
                    conversation_history += f"Agent: {agent_reply}\nUser: Epäkelpo vastaus. Käytä SEARCH/SEMANTIC/MATCH/STOP.\n"

            except Exception as e:
                self.logger.error(f"Error in fallback search iteration {iteration + 1}: {e}")
                break

        return None

    def _gemini_select_best_fallback(self, search_term: str, candidates_df, usage_context: Optional[str] = None):
        """Ask Gemini to pick the best product name from fallback candidates with high confidence."""
        product_list = "\n".join(f"- {row.product_name}" for _, row in candidates_df.iterrows())

        context_info = f" (konteksti: '{usage_context}')" if usage_context else ""
        prompt = (
            f"Hakutermi '{search_term}'{context_info}. "
            f"Ole ERITTÄIN VAROVAINEN! Valitse tuote vain jos olet VARMA että se on sama tuote. "
            f"Jos mikään ei ole selvästi sama tuote, vastaa 'NONE'.\n\n"
            f"Varatuotteet:\n{product_list}\n\n"
            f"Vastaa tuotteen nimellä tai 'NONE'."
        )

        try:
            self.api_calls_made += 1
            config = types.GenerateContentConfig(temperature=0.1)
            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            if not response or not response.text:
                return None

            text = response.text.strip()
            if text.upper() == "NONE":
                return None

            # Validate the selected name exists in candidates
            for _, row in candidates_df.iterrows():
                if row.product_name.strip() == text.strip():
                    return text.strip()

            return None
        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"Gemini fallback selection error: {e}")
            return None

    def _generate_product_name(self, search_term: str, usage_context: Optional[str] = None):
        """Generate a new product name following the style of filtered products."""
        self._load_filtered_products()
        
        if self.filtered_products_df is None:
            return search_term.upper()  # Simple fallback

        # Get sample product names for style reference
        sample_names = self.filtered_products_df['product_name'].head(20).tolist()
        sample_text = "\n".join(f"- {name}" for name in sample_names)

        context_info = f" (konteksti: '{usage_context}')" if usage_context else ""
        prompt = (
            f"Luo uusi tuotenimi termille '{search_term}'{context_info}. "
            f"Noudata alla olevien esimerkkien tyyliä ja konventioita. "
            f"Käytä suomea, ole tekninen ja tarkka. "
            f"Vastaa vain tuotenimellä.\n\n"
            f"Esimerkkejä olemassa olevista tuotenimistä:\n{sample_text}\n\n"
            f"Uusi tuotenimi termille '{search_term}':"
        )

        try:
            self.api_calls_made += 1
            config = types.GenerateContentConfig(temperature=0.3)
            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            if not response or not response.text:
                return search_term.upper()

            generated_name = response.text.strip()
            # Clean up and validate the generated name
            generated_name = re.sub(r'[^\w\s\-\.\,\(\)\/]', '', generated_name)
            
            if len(generated_name) > 100:
                generated_name = generated_name[:100]
            
            return generated_name if generated_name else search_term.upper()

        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"Product name generation error: {e}")
            return search_term.upper()

    # ----------------------- match quality validation --------------------
    async def _validate_match_quality(self, search_term: str, product_code: str, usage_context: Optional[str] = None) -> Dict:
        """
        Ask AI to validate if the proposed match is actually a good match.
        Returns dict with 'is_valid', 'confidence', and 'reason' fields.
        """
        try:
            # Get product details for the proposed match
            validation_response = await self.lemonsoft_client.get('/api/products', params={'filter.sku': product_code})
            if not validation_response or validation_response.status_code != 200:
                return {'is_valid': False, 'confidence': 0, 'reason': 'Product not found in database'}
            
            validation_data = validation_response.json()
            validation_results = validation_data.get('results', [])
            
            if not validation_results:
                return {'is_valid': False, 'confidence': 0, 'reason': 'Product not found in database'}
            
            product = validation_results[0]
            product_name = product.get('name', '')
            product_extra = product.get('extra_name', '')
            
            context_info = f"\nKonteksti: {usage_context[:500]}" if usage_context else ""
            
            quality_prompt = f"""Arvioi tuotevastaavuuden laatu asteikolla 0-100%.

ASIAKKAAN TERMI: "{search_term}"{context_info}

EHDOTETTU TUOTE:
Koodi: {product_code}
Nimi: {product_name}
Lisänimi: {product_extra}

ARVIOINTI KRITEERIT:
- Onko tuote täsmälleen sama kuin asiakas pyysi? (90-100%)
- Onko tuote hyvin samankaltainen/korvaava? (70-89%) 
- Onko tuote samasta kategoriasta mutta eri koko/malli? (50-69%)
- Onko tuote täysin eri kategoriasta? (0-49%)

ERITYISHUOMIOT:
- Koot ja mitat ovat kriittisiä (DN25 ≠ DN50)
- Jänniteet ja tehot ovat kriittisiä (230V ≠ 400V)
- Materiaalit voivat olla kriittisiä (kupari ≠ alumiini)
- Funktio on tärkeämpi kuin merkki

Vastaa JSON-muodossa:
{{
  "confidence": 85,
  "is_good_match": true,
  "reasoning": "Lyhyt selitys miksi on hyvä/huono vastaavuus"
}}

Jos confidence < 70%, aseta is_good_match: false."""

            self.api_calls_made += 1
            config = types.GenerateContentConfig(temperature=0.1)
            response = self.gemini_client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=quality_prompt,
                config=config,
            )
            print(f"Response confidence: {response}")

            if not response or not response.text:
                return {'is_valid': True, 'confidence': 0, 'reason': 'Could not validate, accepting by default'}

            # Parse JSON response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]

            try:
                import json
                result = json.loads(text)
                
                confidence = int(result.get('confidence', 0))
                is_good_match = result.get('is_good_match', confidence >= 70)
                reasoning = result.get('reasoning', 'AI quality check')
                
                return {
                    'is_valid': is_good_match and confidence >= 70,
                    'confidence': confidence,
                    'reason': reasoning
                }
                
            except (json.JSONDecodeError, ValueError):
                # Fallback parsing
                if 'false' in text.lower() or 'huono' in text.lower() or 'poor' in text.lower():
                    return {'is_valid': False, 'confidence': 0, 'reason': 'AI indicated poor match'}
                else:
                    return {'is_valid': True, 'confidence': 0, 'reason': 'AI quality check (fallback parsing)'}

        except Exception as e:
            self.logger.error(f"Error in match quality validation: {e}")
            # Default to accepting matches to avoid breaking the system
            return {'is_valid': True, 'confidence': 0, 'reason': f'Validation error: {str(e)}'}

    # ----------------------- gemini best selection --------------------
    def _gemini_select_best(self, search_term: str, candidates_df, usage_context: Optional[str] = None):
        """Ask Gemini to pick the single best product code from candidates.

        Returns structured data with reasoning and confidence, or None."""
        catalogue_snippet = "\n".join(
            f"{row.Tuotekoodi}; {row.Tuotenimi}" for _, row in candidates_df.iterrows()
        )

        context_info = f" (konteksti: '{usage_context}')" if usage_context else ""
        prompt = f"""Hakutermi '{search_term}'{context_info}. 

Valitse alla olevasta listasta tarkalleen yksi tuote, joka vastaa parhaiten hakutermille.

Lista (tuotekoodi; nimi):
{catalogue_snippet}

Vastaa JSON-muodossa seuraavasti:
{{
  "selected_code": "tuotekoodi tai NONE",
  "reasoning": "Lyhyt selitys miksi tämä tuote valittiin hakutermille",
  "confidence": 85,
  "original_term": "{search_term}"
}}

Jos mikään vaihtoehto ei sovi selvästi, vastaa "selected_code": "NONE" ja selitä syy reasoning-kentässä.
Confidence on prosenttiluku 0-100."""

        try:
            self.api_calls_made += 1
            config = types.GenerateContentConfig(temperature=0.1)
            response = self._retry_llm_request(
                self.gemini_client.models.generate_content,
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

            if not response or not response.text:
                return None

            # Parse JSON response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            
            try:
                import json
                result = json.loads(text)
                
                selected_code = result.get("selected_code", "").strip()
                if selected_code.upper() == "NONE" or not selected_code:
                    return None
                
                # Validate that the code exists in candidates
                code_match = re.search(r"\d+", selected_code)
                if not code_match:
                    return None
                    
                final_code = code_match.group(0)
                
                # Return structured result for enhanced matching
                return {
                    "code": final_code,
                    "reasoning": result.get("reasoning", "AI selected this as best match"),
                    "confidence": min(100, max(0, int(result.get("confidence", 0)))),
                    "original_term": search_term
                }
                
            except (json.JSONDecodeError, ValueError) as parse_error:
                self.logger.warning(f"Failed to parse JSON response, falling back to simple extraction: {parse_error}")
                # Fallback to old behavior
                text_upper = text.upper()
                if "NONE" in text_upper:
                    return None
                    
                code_match = re.search(r"\d+", text)
                if not code_match:
                    return None
                    
                return {
                    "code": code_match.group(0),
                    "reasoning": "AI selected this product (fallback parsing)",
                    "confidence": 0,
                    "original_term": search_term
                }

        except Exception as e:
            self.api_errors += 1
            self.logger.error(f"Gemini best-selection error: {e}")
            return None
    
    async def close(self):
        """Close the product matcher and clean up resources."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        if self.lemonsoft_client:
            await self.lemonsoft_client.close() 