"""
OpenRouter Handler
Routes LLM requests through OpenRouter API for unified access to multiple providers
Supports Gemini, Claude, OpenAI, Grok (xAI), and other models via OpenRouter

Usage:
    You can use either short names (mapped below) or full OpenRouter model IDs:
    - Short name: "grok-4.1-fast" -> maps to "x-ai/grok-4.1-fast"
    - Full ID: "x-ai/grok-4.1-fast" -> used directly
    
    Full model IDs follow the format: "provider/model-name"
    See https://openrouter.ai/models for available models
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator

logger = logging.getLogger(__name__)

# OpenRouter model mappings - maps short names to full OpenRouter model IDs
# You can also use full OpenRouter model IDs directly (e.g., "x-ai/grok-4.1-fast")
OPENROUTER_MODEL_MAPPING = {
    # ============================================================
    # Gemini models (Google)
    # ============================================================
    "gemini-3-pro-preview": "google/gemini-3-pro-preview",
    "gemini-2.5-pro": "google/gemini-2.5-pro-preview",
    "gemini-2.5-flash": "google/gemini-2.5-flash-preview", 
    "gemini-2.0-flash": "google/gemini-2.0-flash-001",
    "gemini-pro": "google/gemini-pro",

    "openai-gpt-5.2": "openai/gpt-5.2",
    "openai-gpt-5": "openai/gpt-5",
    
    # ============================================================
    # Grok models (xAI)
    # ============================================================
    "grok-4.1": "x-ai/grok-4.1",
    "grok-4.1-fast": "x-ai/grok-4.1-fast",
    
    
    # ============================================================
    # Claude models (Anthropic)
    # ============================================================
    "claude-opus-4.5": "anthropic/claude-4.5-opus",
    "claude-sonnet-4.5": "anthropic/claude-4.5-sonnOPENROUTER] Functionet",
    
    # ============================================================
    # DeepSeek models
    # ============================================================
    "deepseek-v3.2": "deepseek/deepseek-v3.2",
    # ============================================================

    "kimi-k2": "moonshotai/kimi-k2",
    # Qwen models (Alibaba)  
    # ============================================================
    "qwen-2.5-72b": "qwen/qwen-2.5-72b-instruct",
    "qwen-2.5-coder-32b": "qwen/qwen-2.5-coder-32b-instruct",
    "qwq-32b": "qwen/qwq-32b-preview",
}

# Models that support reasoning/thinking mode
THINKING_CAPABLE_MODELS = {
    # Gemini thinking models
    "gemini-3-pro-preview", "google/gemini-3-pro-preview",
    "gemini-2.5-pro", "google/gemini-2.5-pro-preview",
    "gemini-2.5-flash", "google/gemini-2.5-flash-preview",
    # Claude with extended thinking (both naming conventions)
    "claude-opus-4.5", "claude-4.5-opus", "anthropic/claude-4.5-opus",
    "claude-sonnet-4.5", "claude-4.5-sonnet", "anthropic/claude-4.5-sonnet",
    # Grok models with reasoning (xAI)
    "grok-4.1", "x-ai/grok-4.1",
    "grok-4.1-fast", "x-ai/grok-4.1-fast",
    # Kimi K2
    "kimi-k2", "moonshotai/kimi-k2",
    # DeepSeek R1 (reasoning)
    "deepseek-r1", "deepseek/deepseek-r1",
    # Qwen QwQ (reasoning)
    "qwq-32b", "qwen/qwq-32b-preview",
}

# Models that use simple reasoning format: {"reasoning": {"enabled": True}}
# vs max_tokens format: {"reasoning": {"max_tokens": N}}
SIMPLE_REASONING_FORMAT_MODELS = {
    # Grok models use simple enabled: true format
    "grok-4.1", "x-ai/grok-4.1",
    "grok-4.1-fast", "x-ai/grok-4.1-fast"
}

# Models that support function calling / tools
TOOL_CAPABLE_MODELS = {
    # Most modern models support tools - list exceptions instead
    # This is used to skip tool conversion for models that don't support it
}


class OpenRouterHandler:
    """Handler for OpenRouter API requests"""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        """Get or create OpenRouter client (OpenAI-compatible)"""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENROUTER_API_KEY")
                if not api_key:
                    raise ValueError("OPENROUTER_API_KEY not found in environment")
                self._client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client
    
    def _get_openrouter_model_id(self, model_name: str) -> str:
        """Convert internal model name to OpenRouter model ID.
        
        If model_name is in OPENROUTER_MODEL_MAPPING, returns the mapped ID.
        Otherwise, assumes it's already a full OpenRouter model ID (provider/model).
        """
        if model_name in OPENROUTER_MODEL_MAPPING:
            mapped = OPENROUTER_MODEL_MAPPING[model_name]
            logger.debug(f"[OPENROUTER] Mapped '{model_name}' -> '{mapped}'")
            return mapped
        # If not in mapping, assume it's already an OpenRouter model ID
        # This allows direct use of any OpenRouter model like "x-ai/grok-4.1-fast"
        if "/" in model_name:
            logger.debug(f"[OPENROUTER] Using full model ID directly: '{model_name}'")
        else:
            logger.warning(f"[OPENROUTER] Unknown model '{model_name}' - passing through as-is")
        return model_name
    
    def _is_thinking_capable(self, model: str) -> bool:
        """Check if a model supports reasoning/thinking mode."""
        # Check both the original name and the mapped name
        if model in THINKING_CAPABLE_MODELS:
            return True
        mapped = self._get_openrouter_model_id(model)
        if mapped in THINKING_CAPABLE_MODELS:
            return True
        # Also check for known patterns
        model_lower = model.lower()
        if any(pattern in model_lower for pattern in ['gemini-2.5', 'gemini-3', 'o1', 'o3', 'deepseek-r1', 'qwq', 'grok-4', 'grok-3']):
            return True
        return False
    
    def _uses_simple_reasoning_format(self, model: str) -> bool:
        """Check if model uses simple reasoning format: {"reasoning": {"enabled": True}}.
        
        Some models (like Grok) use {"reasoning": {"enabled": True}}
        while others (like Gemini) use {"reasoning": {"max_tokens": N}}
        """
        if model in SIMPLE_REASONING_FORMAT_MODELS:
            return True
        mapped = self._get_openrouter_model_id(model)
        if mapped in SIMPLE_REASONING_FORMAT_MODELS:
            return True
        # Check for Grok pattern
        model_lower = model.lower()
        if 'grok' in model_lower or 'x-ai' in model_lower:
            return True
        return False
    
    def _build_reasoning_extra_body(self, model: str, thinking_budget: int = 8000) -> Dict:
        """Build the appropriate extra_body for reasoning based on model type."""
        if self._uses_simple_reasoning_format(model):
            # Grok-style: simple enabled flag
            return {"reasoning": {"enabled": True}}
        else:
            # Gemini/Claude style: max_tokens budget
            return {"reasoning": {"max_tokens": thinking_budget}}
    
    def _convert_messages_to_openrouter(
        self, 
        prompt: Any, 
        messages: Optional[List[Dict]], 
        system_prompt: Optional[str],
        images: Optional[List[str]] = None
    ) -> List[Dict]:
        """Convert messages to OpenRouter format with image support.
        
        Tracks function call IDs from assistant messages and uses them
        when converting tool responses.
        """
        openrouter_messages = []
        
        # Track function call IDs: function_name -> call_id
        # This is needed because Gemini SDK function_response only has 'name',
        # but OpenRouter needs 'tool_call_id' to match with the original call
        function_call_ids: Dict[str, str] = {}
        
        # Add system message if provided
        if system_prompt:
            openrouter_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        if messages:
            # Convert existing messages, tracking function call IDs
            for msg in messages:
                converted = self._convert_single_message(msg, function_call_ids=function_call_ids)
                if converted:
                    openrouter_messages.append(converted)
        elif prompt:
            # Convert prompt to user message
            if isinstance(prompt, str):
                user_content = self._build_user_content(prompt, images)
                openrouter_messages.append({
                    "role": "user",
                    "content": user_content
                })
            elif isinstance(prompt, list):
                # Prompt is a conversation history
                for msg in prompt:
                    converted = self._convert_single_message(msg, images, function_call_ids=function_call_ids)
                    if converted:
                        openrouter_messages.append(converted)
        
        return openrouter_messages
    
    def _build_user_content(self, text: str, images: Optional[List[str]] = None) -> Any:
        """Build user content with optional images"""
        if not images:
            return text
        
        # Multi-part content with images
        content = [{"type": "text", "text": text}]
        
        for img_base64 in images:
            # Detect mime type from base64 data
            mime_type = self._detect_image_mime_type(img_base64)
            data_url = f"data:{mime_type};base64,{img_base64}"
            
            content.append({
                "type": "image_url",
                "image_url": {"url": data_url}
            })
        
        return content
    
    def _detect_image_mime_type(self, base64_data: str) -> str:
        """Detect image MIME type from base64 data"""
        import base64
        try:
            # Decode just the first few bytes to detect type
            img_bytes = base64.b64decode(base64_data[:100] + "==")
            
            if img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                return 'image/png'
            elif img_bytes[:2] == b'\xff\xd8':
                return 'image/jpeg'
            elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):
                return 'image/gif'
            elif img_bytes[:4] == b'RIFF' and len(img_bytes) > 11 and img_bytes[8:12] == b'WEBP':
                return 'image/webp'
        except Exception:
            pass
        return 'image/jpeg'  # Default
    
    def _convert_single_message(
        self, 
        msg: Any, 
        images: Optional[List[str]] = None,
        function_call_ids: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """Convert a single message to OpenRouter format.
        
        Args:
            msg: Message to convert (dict or SDK object)
            images: Optional images to include
            function_call_ids: Dict to track function_name -> call_id mappings.
                              Updated when processing assistant messages with tool_calls,
                              used when processing tool responses.
        """
        if function_call_ids is None:
            function_call_ids = {}
            
        if isinstance(msg, dict):
            role = msg.get("role", "user")
            
            # Handle Gemini-style messages with parts
            if "parts" in msg:
                return self._convert_gemini_message(msg, images, function_call_ids)
            
            # Handle standard message format
            content = msg.get("content", "")
            
            # Handle tool_calls in assistant messages - track the IDs
            if role == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    func_name = tc.get("function", {}).get("name")
                    call_id = tc.get("id")
                    if func_name and call_id:
                        function_call_ids[func_name] = call_id
                return {
                    "role": "assistant",
                    "content": content if content else None,
                    "tool_calls": msg["tool_calls"]
                }
            
            # Handle tool results
            if role == "tool":
                return {
                    "role": "tool",
                    "tool_call_id": msg.get("tool_call_id"),
                    "content": msg.get("content", "")
                }
            
            return {
                "role": role,
                "content": content
            }
        else:
            # Handle SDK message objects
            role = getattr(msg, "role", "user")
            parts = getattr(msg, "parts", [])
            
            if parts:
                return self._convert_gemini_parts_to_openrouter(role, parts, images, function_call_ids)
            
            return None
    
    def _convert_gemini_message(
        self, 
        msg: Dict, 
        images: Optional[List[str]] = None,
        function_call_ids: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """Convert Gemini-style message with parts to OpenRouter format"""
        role = msg.get("role", "user")
        parts = msg.get("parts", [])
        
        return self._convert_gemini_parts_to_openrouter(role, parts, images, function_call_ids)
    
    def _convert_gemini_parts_to_openrouter(
        self, 
        role: str, 
        parts: List, 
        images: Optional[List[str]] = None,
        function_call_ids: Optional[Dict[str, str]] = None
    ) -> Optional[Dict]:
        """Convert Gemini parts to OpenRouter message format.
        
        Args:
            role: Message role (user, model, assistant)
            parts: List of message parts
            images: Optional images
            function_call_ids: Dict tracking function_name -> call_id.
                              Updated when processing function_call parts,
                              used when processing function_response parts.
        """
        if function_call_ids is None:
            function_call_ids = {}
            
        text_content = []
        tool_calls = []
        function_response = None
        
        for part in parts:
            if isinstance(part, dict):
                if "text" in part:
                    text_content.append(part["text"])
                elif "function_call" in part:
                    fc = part["function_call"]
                    call_id = fc.get("id", f"call_{len(tool_calls)}")
                    func_name = fc.get("name")
                    # Track the function call ID for later use in function_response
                    if func_name:
                        function_call_ids[func_name] = call_id
                    # Ensure args are JSON serializable
                    args_data = self._ensure_json_serializable(fc.get("args", {}))
                    # Preserve thought_signature for later reconstruction
                    tool_call = {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": json.dumps(args_data)
                        }
                    }
                    # Store thought_signature in metadata for reconstruction
                    if part.get("thought_signature"):
                        sig = part["thought_signature"]
                        # Ensure thought_signature is a string, not bytes
                        if isinstance(sig, bytes):
                            try:
                                sig = sig.decode('utf-8')
                            except UnicodeDecodeError:
                                sig = str(sig)
                        tool_call["_thought_signature"] = sig
                    tool_calls.append(tool_call)
                elif "function_response" in part:
                    fr = part["function_response"]
                    func_name = fr.get("name")
                    # Ensure response is JSON serializable (handle bytes, etc.)
                    raw_response = fr.get("response", {})
                    response_data = self._ensure_json_serializable(raw_response)
                    
                    # CRITICAL: Check for __tool_call_id__ in response (for multiple calls to same function)
                    # This is passed from product_matcher to ensure correct matching
                    if isinstance(response_data, dict) and "__tool_call_id__" in response_data:
                        call_id = response_data.pop("__tool_call_id__")
                    else:
                        # Fallback to tracked call_id from function_call_ids dict
                        call_id = function_call_ids.get(func_name, fr.get("id", f"call_{func_name or 'unknown'}"))
                    
                    try:
                        # Validate that we can actually serialize this before adding to message
                        json.dumps(response_data)
                    except TypeError as e:
                        logger.warning(f"Failed to serialize function response for {func_name}: {e}")
                        # Fallback to string representation
                        response_data = {"error": "Response not serializable", "value": str(raw_response)}
                    function_response = {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(response_data)
                    }
            else:
                # SDK Part object
                if hasattr(part, "text") and part.text:
                    text_content.append(part.text)
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    call_id = getattr(fc, "id", None) or f"call_{len(tool_calls)}"
                    func_name = getattr(fc, "name", None)
                    # Track the function call ID for later use in function_response
                    if func_name:
                        function_call_ids[func_name] = call_id
                    # Ensure args are JSON serializable
                    args_data = self._ensure_json_serializable(dict(getattr(fc, "args", {}) or {}))
                    tool_call = {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": json.dumps(args_data)
                        }
                    }
                    # Preserve thought_signature
                    sig = getattr(part, "thought_signature", None) or getattr(fc, "thought_signature", None)
                    if sig:
                        # Ensure thought_signature is a string, not bytes
                        if isinstance(sig, bytes):
                            try:
                                sig = sig.decode('utf-8')
                            except UnicodeDecodeError:
                                sig = str(sig)
                        tool_call["_thought_signature"] = sig
                    tool_calls.append(tool_call)
                elif hasattr(part, "function_response") and part.function_response:
                    fr = part.function_response
                    func_name = getattr(fr, "name", None)
                    # Ensure response is JSON serializable (handle bytes, etc.)
                    # Get the response object - it might be a dict, SDK object, or other type
                    raw_response = getattr(fr, "response", {}) or {}
                    # Convert to dict if needed, then ensure JSON serializable
                    if isinstance(raw_response, dict):
                        response_dict = raw_response
                    else:
                        try:
                            response_dict = dict(raw_response)
                        except (TypeError, ValueError):
                            # If dict() fails, try to convert the object to a serializable form first
                            response_dict = self._ensure_json_serializable(raw_response)
                            if not isinstance(response_dict, dict):
                                response_dict = {"value": response_dict}
                    response_data = self._ensure_json_serializable(response_dict)
                    
                    # CRITICAL: Check for __tool_call_id__ in response (for multiple calls to same function)
                    # This is passed from product_matcher to ensure correct matching
                    if isinstance(response_data, dict) and "__tool_call_id__" in response_data:
                        call_id = response_data.pop("__tool_call_id__")
                    else:
                        # Fallback to tracked call_id from function_call_ids dict
                        call_id = function_call_ids.get(func_name, getattr(fr, "id", None) or f"call_{func_name or 'unknown'}")
                    
                    try:
                        # Validate that we can actually serialize this before adding to message
                        json.dumps(response_data)
                    except TypeError as e:
                        logger.warning(f"Failed to serialize SDK function response for {func_name}: {e}")
                        # Fallback to string representation
                        response_data = {"error": "Response not serializable", "value": str(raw_response)}
                    function_response = {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(response_data)
                    }
        
        # Return function response directly if present
        if function_response and role == "user":
            return function_response
        
        # Build the message
        content = "\n".join(text_content) if text_content else None
        
        if role == "model":
            role = "assistant"
        
        if tool_calls and role == "assistant":
            return {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls
            }
        
        if content:
            return {
                "role": role,
                "content": content
            }
        
        return None
    
    def _is_openai_model(self, model: str) -> bool:
        """Check if the model is an OpenAI model that requires strict schema validation."""
        model_lower = model.lower()
        openrouter_id = self._get_openrouter_model_id(model)
        return 'openai' in model_lower or 'gpt' in model_lower or openrouter_id.startswith('openai/')

    def _fix_empty_properties_for_openai(self, params: Dict) -> Dict:
        """Fix empty properties object for OpenAI strict schema validation.

        OpenAI requires object schemas to have at least some properties defined,
        or use a dummy property. additionalProperties alone is not enough.
        """
        if not isinstance(params, dict):
            return params

        # If this is an object type with empty properties, add a dummy optional property
        # OpenAI strict schema validation requires properties to be non-empty
        if params.get("type") == "object":
            properties = params.get("properties", {})
            if isinstance(properties, dict) and len(properties) == 0:
                params = params.copy()
                params["properties"] = {
                    "_no_params": {
                        "type": "boolean",
                        "description": "This function takes no parameters. Ignore this field."
                    }
                }
                params["additionalProperties"] = False
                # Don't require the dummy property
                params["required"] = []
                logger.info(f"[OPENROUTER] Fixed empty properties schema for OpenAI function")

        return params

    def _convert_tools_to_openrouter(self, tools: Optional[List], model: str = "") -> Optional[List[Dict]]:
        """Convert tools to OpenRouter format"""
        if not tools:
            return None

        is_openai = self._is_openai_model(model)
        logger.info(f"[OPENROUTER] Converting tools for model '{model}', is_openai={is_openai}")
        openrouter_tools = []

        for tool in tools:
            if isinstance(tool, dict):
                # Already in OpenAI format
                if "type" in tool and "function" in tool:
                    converted_tool = tool.copy()
                    if is_openai and "function" in converted_tool:
                        func = converted_tool["function"].copy()
                        if "parameters" in func:
                            func["parameters"] = self._fix_empty_properties_for_openai(func["parameters"])
                        converted_tool["function"] = func
                    openrouter_tools.append(converted_tool)
                elif "name" in tool and "description" in tool:
                    # Gemini-style tool definition
                    params = tool.get("parameters", {})
                    if is_openai:
                        params = self._fix_empty_properties_for_openai(params)
                    openrouter_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": params
                        }
                    })
            else:
                # SDK Tool object - extract function declarations
                func_decls = getattr(tool, "function_declarations", None)
                logger.info(f"[OPENROUTER] SDK Tool object, func_decls type: {type(func_decls)}, count: {len(func_decls) if func_decls else 0}")
                if func_decls:
                    for fd in func_decls:
                        # Handle both SDK FunctionDeclaration objects and plain dicts
                        if isinstance(fd, dict):
                            func_name = fd.get("name")
                            func_desc = fd.get("description", "")
                        else:
                            func_name = getattr(fd, "name", None)
                            func_desc = getattr(fd, "description", "")
                        params = self._convert_gemini_parameters(fd)
                        if is_openai:
                            params = self._fix_empty_properties_for_openai(params)
                        openrouter_tools.append({
                            "type": "function",
                            "function": {
                                "name": func_name,
                                "description": func_desc,
                                "parameters": params
                            }
                        })

        return openrouter_tools if openrouter_tools else None
    
    def _convert_gemini_parameters(self, func_decl) -> Dict:
        """Convert Gemini FunctionDeclaration parameters to OpenAI format"""
        # Handle both SDK FunctionDeclaration objects and plain dicts
        if isinstance(func_decl, dict):
            params = func_decl.get("parameters", None)
        else:
            params = getattr(func_decl, "parameters", None)
        logger.debug(f"[OPENROUTER] _convert_gemini_parameters: func_decl type={type(func_decl)}, params type={type(params)}")
        if not params:
            return {"type": "object", "properties": {}}

        # If it's already a dict, return it
        if isinstance(params, dict):
            return self._ensure_json_serializable(params)

        # Convert Gemini Schema to dict recursively
        return self._schema_to_dict(params)
    
    def _schema_to_dict(self, schema) -> Dict:
        """Recursively convert Gemini Schema object to JSON-serializable dict."""
        if schema is None:
            return {}
        
        # If already a dict, ensure all values are serializable
        if isinstance(schema, dict):
            return self._ensure_json_serializable(schema)
        
        # If it's a primitive type, return as-is
        if isinstance(schema, (str, int, float, bool)):
            return schema
        
        # If it's a list, convert each element
        if isinstance(schema, list):
            return [self._schema_to_dict(item) for item in schema]
        
        result = {}
        
        # Extract type
        schema_type = getattr(schema, "type", None) or getattr(schema, "type_", None)
        if schema_type:
            # Handle enum types (e.g., Type.STRING -> "string")
            if hasattr(schema_type, "name"):
                result["type"] = schema_type.name.lower()
            elif hasattr(schema_type, "value"):
                result["type"] = str(schema_type.value).lower()
            else:
                result["type"] = str(schema_type).lower()
        
        # Extract description
        description = getattr(schema, "description", None)
        if description:
            result["description"] = str(description)
        
        # Extract enum values
        enum_values = getattr(schema, "enum", None)
        if enum_values:
            result["enum"] = list(enum_values)
        
        # Extract properties (for object types)
        properties = getattr(schema, "properties", None)
        if properties:
            result["properties"] = {}
            # Handle both dict-like and object properties
            if hasattr(properties, "items"):
                for key, value in properties.items():
                    result["properties"][key] = self._schema_to_dict(value)
            elif hasattr(properties, "__iter__"):
                for key in properties:
                    prop_value = properties[key] if hasattr(properties, "__getitem__") else getattr(properties, key, None)
                    if prop_value:
                        result["properties"][key] = self._schema_to_dict(prop_value)
        
        # Extract required fields
        required = getattr(schema, "required", None)
        if required:
            result["required"] = list(required)
        
        # Extract items (for array types)
        items = getattr(schema, "items", None)
        if items:
            result["items"] = self._schema_to_dict(items)
        
        # If we couldn't extract anything useful, try to convert to dict directly
        if not result:
            try:
                if hasattr(schema, "__dict__"):
                    result = self._ensure_json_serializable(schema.__dict__)
                elif hasattr(schema, "to_dict"):
                    result = schema.to_dict()
            except Exception:
                result = {"type": "object", "properties": {}}
        
        return result
    
    def _find_bytes_in_structure(self, obj, path="root"):
        """Debug helper: Find bytes objects in nested structure and log their location."""
        if isinstance(obj, bytes):
            logger.warning(f"[DEBUG] Found bytes at {path}: {obj[:50]}..." if len(obj) > 50 else f"[DEBUG] Found bytes at {path}: {obj}")
            return True
        elif isinstance(obj, bytearray):
            logger.warning(f"[DEBUG] Found bytearray at {path}: {obj[:50]}..." if len(obj) > 50 else f"[DEBUG] Found bytearray at {path}: {obj}")
            return True
        elif isinstance(obj, dict):
            found = False
            for k, v in obj.items():
                if self._find_bytes_in_structure(v, f"{path}.{k}"):
                    found = True
            return found
        elif isinstance(obj, (list, tuple)):
            found = False
            for i, item in enumerate(obj):
                if self._find_bytes_in_structure(item, f"{path}[{i}]"):
                    found = True
            return found
        return False

    def _ensure_json_serializable(self, obj) -> Any:
        """Ensure an object is JSON serializable by converting non-serializable types."""
        if obj is None:
            return None

        if isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle bytes - decode to string or base64
        if isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                import base64
                return base64.b64encode(obj).decode('ascii')

        # Handle bytearray (similar to bytes)
        if isinstance(obj, bytearray):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                import base64
                return base64.b64encode(obj).decode('ascii')

        if isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [self._ensure_json_serializable(item) for item in obj]

        # Handle enum types
        if hasattr(obj, "name") and not hasattr(obj, "__dict__"):
            return obj.name.lower()
        if hasattr(obj, "value") and not hasattr(obj, "__dict__"):
            return obj.value

        # Handle Schema objects
        if hasattr(obj, "type") or hasattr(obj, "properties"):
            return self._schema_to_dict(obj)

        # Try to convert to dict
        if hasattr(obj, "__dict__"):
            return self._ensure_json_serializable(obj.__dict__)
        if hasattr(obj, "to_dict"):
            try:
                dict_result = obj.to_dict()
                return self._ensure_json_serializable(dict_result)
            except Exception:
                pass

        # Last resort: convert to string
        return str(obj)
    
    async def generate(
        self,
        model: str,
        prompt: Any,
        messages: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        images: Optional[List[str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[bool] = None,  # None = auto-detect based on model
        thinking_budget: int = 8000,
        **kwargs
    ) -> Dict:
        """
        Generate a non-streaming response via OpenRouter
        
        Args:
            model: Model name (short name from mapping or full OpenRouter ID like "x-ai/grok-4.1-fast")
            prompt: Text prompt or conversation history
            messages: List of message dicts (alternative to prompt)
            system_prompt: System instruction
            tools: List of tool/function definitions
            images: List of base64-encoded images
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            thinking: Enable reasoning mode (None = auto-detect based on model capability)
            thinking_budget: Token budget for reasoning
        
        Returns dict with:
        - content: str
        - function_calls: List[Dict] or None
        - usage: Dict
        - finish_reason: str
        - thinking_content: str or None
        """
        client = self._get_client()
        openrouter_model = self._get_openrouter_model_id(model)
        
        logger.info(f"[OPENROUTER] Generating with model: {openrouter_model}")
        
        # Convert messages
        openrouter_messages = self._convert_messages_to_openrouter(
            prompt, messages, system_prompt, images
        )
        
        # Convert tools (pass model to handle OpenAI-specific schema requirements)
        openrouter_tools = self._convert_tools_to_openrouter(tools, model)

        # Build request params
        params = {
            "model": openrouter_model,
            "messages": openrouter_messages,
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens:
            params["max_tokens"] = max_tokens
        if openrouter_tools:
            params["tools"] = openrouter_tools
            params["tool_choice"] = "auto"
        
        # Auto-detect thinking capability if not explicitly set
        enable_thinking = thinking if thinking is not None else self._is_thinking_capable(model)

        # Add reasoning/thinking support for compatible models
        if enable_thinking:
            extra_body = self._build_reasoning_extra_body(model, thinking_budget)
            logger.info(f"[OPENROUTER] Enabling reasoning mode for {model}: {extra_body}")
            params["extra_body"] = extra_body

        # CRITICAL: Ensure all params are JSON serializable before API call
        # This catches any bytes objects that slipped through in messages/tools
        params = self._ensure_json_serializable(params)

        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                **params
            )
            
            # Extract response
            message = response.choices[0].message
            content = message.content or ""
            function_calls = None
            thinking_content = None
            
            # Extract thinking content if present
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                thinking_content = message.reasoning_content
            
            # Extract tool calls
            if message.tool_calls:
                function_calls = []
                for tc in message.tool_calls:
                    fc = {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {}
                    }
                    function_calls.append(fc)
            
            return {
                "content": content,
                "function_calls": function_calls,
                "thinking_content": thinking_content,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "output_tokens": response.usage.completion_tokens if response.usage else 0
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            raise
    
    async def generate_stream(
        self,
        model: str,
        prompt: Any,
        messages: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        images: Optional[List[str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: Optional[bool] = None,  # None = auto-detect based on model
        thinking_budget: int = 8000,
        is_gemini_3: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict, None]:
        """
        Generate a streaming response via OpenRouter
        
        Args:
            model: Model name (short name from mapping or full OpenRouter ID like "x-ai/grok-4.1-fast")
            prompt: Text prompt or conversation history
            messages: List of message dicts (alternative to prompt)
            system_prompt: System instruction
            tools: List of tool/function definitions
            images: List of base64-encoded images
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            thinking: Enable reasoning mode (None = auto-detect based on model capability)
            thinking_budget: Token budget for reasoning
            is_gemini_3: Add thought_signature for Gemini 3+ compatibility
        
        Yields dicts with type:
        - {"type": "plan_thinking_chunk", "content": str} - for reasoning/thinking
        - {"type": "content_chunk", "content": str} - for regular content
        - {"type": "function_call", "function_call": dict} - for tool calls
        - {"type": "complete"} - when done
        - {"type": "error", "content": str} - on error
        """
        client = self._get_client()
        openrouter_model = self._get_openrouter_model_id(model)
        
        logger.info(f"[OPENROUTER] Streaming with model: {openrouter_model}")
        
        # Convert messages
        openrouter_messages = self._convert_messages_to_openrouter(
            prompt, messages, system_prompt, images
        )
        
        # Convert tools (pass model to handle OpenAI-specific schema requirements)
        openrouter_tools = self._convert_tools_to_openrouter(tools, model)

        # Build request params
        params = {
            "model": openrouter_model,
            "messages": openrouter_messages,
            "stream": True
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens:
            params["max_tokens"] = max_tokens
        if openrouter_tools:
            params["tools"] = openrouter_tools
            params["tool_choice"] = "auto"
        
        # Auto-detect thinking capability if not explicitly set
        enable_thinking = thinking if thinking is not None else self._is_thinking_capable(model)

        # Add reasoning/thinking support for compatible models
        if enable_thinking:
            extra_body = self._build_reasoning_extra_body(model, thinking_budget)
            logger.info(f"[OPENROUTER] Enabling reasoning mode for {model}: {extra_body}")
            params["extra_body"] = extra_body

        # CRITICAL: Ensure all params are JSON serializable before API call
        # This catches any bytes objects that slipped through in messages/tools
        params = self._ensure_json_serializable(params)

        try:
            # Tool call accumulator (streaming tool calls come in chunks)
            tool_calls_accumulator: Dict[int, Dict] = {}
            content_buffer = ""

            stream = await asyncio.to_thread(
                client.chat.completions.create,
                **params
            )
            
            for chunk in stream:
                if not chunk.choices:
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Handle reasoning/thinking tokens
                if hasattr(delta, 'reasoning_details') and delta.reasoning_details:
                    for reasoning_detail in delta.reasoning_details:
                        if isinstance(reasoning_detail, dict):
                            reasoning_type = reasoning_detail.get('type', '')
                            if reasoning_type == 'reasoning.text':
                                text = reasoning_detail.get('text', '')
                                if text:
                                    yield {"type": "plan_thinking_chunk", "content": text}
                            # Skip encrypted reasoning blocks
                        else:
                            # Handle as object
                            reasoning_type = getattr(reasoning_detail, 'type', '')
                            if reasoning_type == 'reasoning.text':
                                text = getattr(reasoning_detail, 'text', '')
                                if text:
                                    yield {"type": "plan_thinking_chunk", "content": text}
                
                # Also check for reasoning_content (some models)
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    yield {"type": "plan_thinking_chunk", "content": delta.reasoning_content}
                
                # Handle regular content
                if hasattr(delta, 'content') and delta.content:
                    content_buffer += delta.content
                    yield {"type": "content_chunk", "content": delta.content}
                
                # Handle tool calls (accumulate chunks)
                if hasattr(delta, 'tool_calls') and delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        
                        if index not in tool_calls_accumulator:
                            tool_calls_accumulator[index] = {
                                'id': tool_call_delta.id or f"call_{index}",
                                'name': '',
                                'arguments': ''
                            }
                        
                        # Update function name if present
                        if hasattr(tool_call_delta, 'function'):
                            if hasattr(tool_call_delta.function, 'name') and tool_call_delta.function.name:
                                tool_calls_accumulator[index]['name'] = tool_call_delta.function.name
                            
                            # Accumulate arguments (they come in chunks)
                            if hasattr(tool_call_delta.function, 'arguments') and tool_call_delta.function.arguments:
                                tool_calls_accumulator[index]['arguments'] += tool_call_delta.function.arguments
                
                # Check for finish
                if chunk.choices[0].finish_reason:
                    break
                
                await asyncio.sleep(0)  # Allow other tasks to run
            
            # Emit accumulated tool calls at the end
            for index in sorted(tool_calls_accumulator.keys()):
                tc = tool_calls_accumulator[index]
                try:
                    args = json.loads(tc['arguments']) if tc['arguments'] else {}
                except json.JSONDecodeError:
                    args = {}
                
                function_call_payload = {
                    "id": tc['id'],
                    "name": tc['name'],
                    "arguments": args
                }
                
                # For Gemini 3.0 compatibility, add thought_signature
                if is_gemini_3:
                    function_call_payload["thought_signature"] = "context_engineering_is_the_way_to_go"
                    logger.info(f"[OPENROUTER] Added dummy thought_signature for Gemini 3.0 compatibility for {tc['name']}")
                
                yield {"type": "function_call", "function_call": function_call_payload}
            
            yield {"type": "complete"}
            
        except Exception as e:
            logger.error(f"OpenRouter streaming API error: {str(e)}")
            yield {"type": "error", "content": str(e)}


# Global handler instance
_openrouter_handler = None


def get_openrouter_handler() -> OpenRouterHandler:
    """Get global OpenRouter handler instance"""
    global _openrouter_handler
    if _openrouter_handler is None:
        _openrouter_handler = OpenRouterHandler()
    return _openrouter_handler
