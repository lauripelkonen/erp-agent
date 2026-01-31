"""
Grok Handler
Routes LLM requests directly to xAI's API for Grok models.
Uses OpenAI SDK with xAI base URL for compatibility.

This handler bypasses OpenRouter for direct xAI API access,
providing lower latency and direct access to Grok-specific features.

Usage:
    handler = get_grok_handler()
    result = handler.generate(
        model="grok-4-1-fast-reasoning",
        prompt="Your prompt here",
        tools=[...],  # Optional
    )
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Grok models that should be routed through this handler
GROK_MODELS = {
    "grok-4-1-fast-reasoning",
    "grok-4.1-fast-reasoning",
    "grok-4.1",
    "grok-4.1-fast",
    "grok-4",
}


class GrokHandler:
    """Handler for direct xAI API requests"""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Get or create xAI client (OpenAI-compatible)"""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("XAI_API_KEY")
                if not api_key:
                    raise ValueError("XAI_API_KEY not found in environment")
                self._client = OpenAI(
                    base_url="https://api.x.ai/v1",
                    api_key=api_key
                )
                logger.info("[GROK] Initialized xAI client")
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")
        return self._client

    def _convert_messages_to_openai(
        self,
        prompt: Any,
        messages: Optional[List[Any]],
        system_prompt: Optional[str]
    ) -> List[Dict]:
        """Convert messages to OpenAI format.

        Handles Gemini SDK Content objects and dict messages.
        """
        openai_messages = []

        # Track function call IDs: function_name -> call_id
        function_call_ids: Dict[str, str] = {}

        # Add system message if provided
        if system_prompt:
            openai_messages.append({
                "role": "system",
                "content": system_prompt
            })

        if messages:
            # Convert existing messages
            for msg in messages:
                converted = self._convert_single_message(msg, function_call_ids)
                if converted:
                    openai_messages.append(converted)
        elif prompt:
            # Convert prompt to user message
            if isinstance(prompt, str):
                openai_messages.append({
                    "role": "user",
                    "content": prompt
                })
            elif isinstance(prompt, list):
                # Prompt is a conversation history
                for msg in prompt:
                    converted = self._convert_single_message(msg, function_call_ids)
                    if converted:
                        openai_messages.append(converted)

        return openai_messages

    def _convert_single_message(
        self,
        msg: Any,
        function_call_ids: Dict[str, str]
    ) -> Optional[Dict]:
        """Convert a single message to OpenAI format."""
        if isinstance(msg, dict):
            role = msg.get("role", "user")

            # Handle Gemini-style messages with parts
            if "parts" in msg:
                return self._convert_parts_message(msg, function_call_ids)

            # Handle standard message format
            content = msg.get("content", "")

            # Handle tool_calls in assistant messages
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
            # Handle SDK message objects (Gemini Content objects)
            role = getattr(msg, "role", "user")
            parts = getattr(msg, "parts", [])

            if parts:
                return self._convert_parts_to_openai(role, parts, function_call_ids)

            return None

    def _convert_parts_message(
        self,
        msg: Dict,
        function_call_ids: Dict[str, str]
    ) -> Optional[Dict]:
        """Convert Gemini-style message with parts to OpenAI format"""
        role = msg.get("role", "user")
        parts = msg.get("parts", [])
        return self._convert_parts_to_openai(role, parts, function_call_ids)

    def _convert_parts_to_openai(
        self,
        role: str,
        parts: List,
        function_call_ids: Dict[str, str]
    ) -> Optional[Dict]:
        """Convert Gemini parts to OpenAI message format."""
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
                    if func_name:
                        function_call_ids[func_name] = call_id
                    tool_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": json.dumps(fc.get("args", {}))
                        }
                    })
                elif "function_response" in part:
                    fr = part["function_response"]
                    func_name = fr.get("name")
                    response_data = fr.get("response", {})

                    # Check for __tool_call_id__ in response
                    if isinstance(response_data, dict) and "__tool_call_id__" in response_data:
                        call_id = response_data.pop("__tool_call_id__")
                    else:
                        call_id = function_call_ids.get(func_name, f"call_{func_name or 'unknown'}")

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
                    if func_name:
                        function_call_ids[func_name] = call_id
                    tool_calls.append({
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": json.dumps(dict(getattr(fc, "args", {}) or {}))
                        }
                    })
                elif hasattr(part, "function_response") and part.function_response:
                    fr = part.function_response
                    func_name = getattr(fr, "name", None)
                    raw_response = getattr(fr, "response", {}) or {}
                    response_data = dict(raw_response) if hasattr(raw_response, '__iter__') else {"value": str(raw_response)}

                    # Check for __tool_call_id__
                    if isinstance(response_data, dict) and "__tool_call_id__" in response_data:
                        call_id = response_data.pop("__tool_call_id__")
                    else:
                        call_id = function_call_ids.get(func_name, f"call_{func_name or 'unknown'}")

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

    def _convert_tools_to_openai(self, tools: Optional[List]) -> Optional[List[Dict]]:
        """Convert tools to OpenAI format"""
        if not tools:
            return None

        openai_tools = []

        for tool in tools:
            if isinstance(tool, dict):
                # Already in OpenAI format
                if "type" in tool and "function" in tool:
                    openai_tools.append(tool)
                elif "name" in tool and "description" in tool:
                    # Gemini-style tool definition
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool.get("parameters", {})
                        }
                    })
            else:
                # SDK Tool object - extract function declarations
                func_decls = getattr(tool, "function_declarations", None)
                if func_decls:
                    for fd in func_decls:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": getattr(fd, "name", None),
                                "description": getattr(fd, "description", ""),
                                "parameters": self._convert_parameters(fd)
                            }
                        })

        return openai_tools if openai_tools else None

    def _convert_parameters(self, func_decl) -> Dict:
        """Convert FunctionDeclaration parameters to OpenAI format"""
        params = getattr(func_decl, "parameters", None)
        if not params:
            return {"type": "object", "properties": {}}

        if isinstance(params, dict):
            return params

        # Convert Schema object to dict
        return self._schema_to_dict(params)

    def _schema_to_dict(self, schema) -> Dict:
        """Recursively convert Schema object to dict."""
        if schema is None:
            return {}

        if isinstance(schema, dict):
            return schema

        if isinstance(schema, (str, int, float, bool)):
            return schema

        if isinstance(schema, list):
            return [self._schema_to_dict(item) for item in schema]

        result = {}

        # Extract type
        schema_type = getattr(schema, "type", None) or getattr(schema, "type_", None)
        if schema_type:
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

        # Extract properties
        properties = getattr(schema, "properties", None)
        if properties:
            result["properties"] = {}
            if hasattr(properties, "items"):
                for key, value in properties.items():
                    result["properties"][key] = self._schema_to_dict(value)

        # Extract required fields
        required = getattr(schema, "required", None)
        if required:
            result["required"] = list(required)

        # Extract items (for array types)
        items = getattr(schema, "items", None)
        if items:
            result["items"] = self._schema_to_dict(items)

        if not result:
            result = {"type": "object", "properties": {}}

        return result

    def generate(
        self,
        model: str,
        prompt: Any = None,
        messages: Optional[List[Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        Generate a response via xAI API (synchronous).

        Args:
            model: Grok model name (e.g., "grok-4-1-fast-reasoning")
            prompt: Text prompt or conversation history
            messages: List of message dicts/objects (alternative to prompt)
            system_prompt: System instruction
            tools: List of tool/function definitions
            temperature: Sampling temperature
            max_tokens: Maximum output tokens

        Returns dict with:
        - content: str
        - function_calls: List[Dict] or None
        - usage: Dict
        - finish_reason: str
        - thinking_content: str or None (for reasoning models)
        """
        client = self._get_client()

        logger.info(f"[GROK] Generating with model: {model}")

        # Convert messages
        openai_messages = self._convert_messages_to_openai(prompt, messages, system_prompt)

        # Convert tools
        openai_tools = self._convert_tools_to_openai(tools)

        # Build request params
        params = {
            "model": model,
            "messages": openai_messages,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens:
            params["max_tokens"] = max_tokens
        if openai_tools:
            params["tools"] = openai_tools
            params["tool_choice"] = "auto"

        # Enable reasoning for Grok reasoning models
        if "reasoning" in model.lower() or "fast" in model.lower():
            params["extra_body"] = {"reasoning": {"enabled": True}}
            logger.info(f"[GROK] Enabling reasoning mode for {model}")

        try:
            response = client.chat.completions.create(**params)

            # Extract response
            message = response.choices[0].message
            content = message.content or ""
            function_calls = None
            thinking_content = None

            # Extract reasoning content if present
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

            logger.info(f"[GROK] Request completed successfully for model: {model}")

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
            logger.error(f"[GROK] API error: {str(e)}")
            raise


# Global handler instance
_grok_handler = None


def get_grok_handler() -> GrokHandler:
    """Get global Grok handler instance"""
    global _grok_handler
    if _grok_handler is None:
        _grok_handler = GrokHandler()
    return _grok_handler


def is_grok_model(model: str) -> bool:
    """Check if a model should be routed through the Grok handler."""
    model_lower = model.lower()
    # Check explicit model names
    if model in GROK_MODELS:
        return True
    # Check for grok pattern in name
    if 'grok' in model_lower:
        return True
    return False
