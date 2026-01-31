"""
Centralized LLM Handler
Provides a unified interface for all LLM operations across different providers
"""
import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .llm_config import ModelConfig, ModelProvider, get_model_config


try:
    from .mcp_tool_manager import get_mcp_tools_for_llm, execute_mcp_function_call, is_mcp_function
except ImportError:
    get_mcp_tools_for_llm = None
    execute_mcp_function_call = None
    is_mcp_function = None

# Import OpenRouter handler for routing
try:
    from .openrouter_handler import get_openrouter_handler
except ImportError:
    get_openrouter_handler = None

logger = logging.getLogger(__name__)

USE_OPENROUTER = os.getenv("USE_OPENROUTER") == "True"

@dataclass
class LLMRequest:
    """Request object for LLM operations"""
    prompt: str
    model: str = "gemini-2.5-flash"
    user_id: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    messages: Optional[List[Dict]] = None
    json_mode: bool = False
    tools: Optional[List[Dict]] = None
    stream: bool = False
    thinking: bool = False  # Enable thinking mode for compatible models
    thinking_budget: int = 16000  # Token budget for thinking (Claude)
    code_execution: bool = False  # Enable code execution for compatible models
    container_id: Optional[str] = None  # Claude container ID for reuse
    images: Optional[List[str]] = None  # Base64 encoded images
    files: Optional[List[Dict]] = None  # File attachments for Gemini
    uploaded_files: Optional[List[Dict]] = None  # Claude uploaded files
    file_uploads: Optional[List[Dict]] = None  # Files to upload (contains file paths/bytes)
    mcp_servers: Optional[List[Dict]] = None  # MCP server configurations
    timeout: int = 120  # seconds

@dataclass
class LLMResponse:
    """Response object from LLM operations"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict] = None
    function_calls: Optional[List[Dict]] = None
    finish_reason: Optional[str] = None
    thinking_content: Optional[str] = None  # Thinking content for thinking models
    container_id: Optional[str] = None  # Claude container ID for reuse
    code_executions: Optional[List[Dict]] = None  # Code execution results
    mcp_results: Optional[List[Dict]] = None  # MCP tool results
    error: Optional[str] = None

@dataclass
class LLMStreamChunk:
    """Streaming chunk from LLM operations"""
    type: str  # 'thinking', 'content', 'function_call', 'code_execution', 'code_result', 'error', 'done'
    content: str = ""
    model: str = ""
    provider: str = ""
    thinking_time: Optional[float] = None  # Time spent thinking
    function_call: Optional[Dict] = None
    code_execution: Optional[Dict] = None  # Code being executed
    code_result: Optional[Dict] = None  # Code execution result
    error: Optional[str] = None
    is_final: bool = False

class LLMHandler:
    """Centralized handler for all LLM operations"""
    
    def __init__(self):
        self._claude_client = None
        self._gemini_client = None
        self._openai_client = None
        self._openrouter_client = None
        self._claude_files_uploaded = {}  # Cache for Claude uploaded files
        self._gemini_files_uploaded = {}  # Cache for Gemini uploaded files
        
    def _get_claude_client(self):
        """Get or create Claude client"""
        if self._claude_client is None:
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")
                self._claude_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._claude_client
    
    def _get_gemini_client(self):
        """Get or create Gemini client"""
        if self._gemini_client is None:
            try:
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not found in environment")
                genai.configure(api_key=api_key)
                self._gemini_client = genai
            except ImportError:
                raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        return self._gemini_client
    
    async def _add_mcp_tools_to_request(self, request: LLMRequest, user_id: str = None) -> LLMRequest:
        """Add MCP tools to the request based on user's connected services"""
        try:
            if not get_mcp_tools_for_llm or not user_id:
                return request
            
            # Get user's available MCP tools
            mcp_tools = await get_mcp_tools_for_llm(user_id)
            
            if not mcp_tools:
                return request
            
            # Combine with existing tools
            existing_tools = request.tools or []
            all_tools = existing_tools + mcp_tools
            
            # Create new request with combined tools
            updated_request = LLMRequest(
                prompt=request.prompt,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                system_prompt=request.system_prompt,
                messages=request.messages,
                json_mode=request.json_mode,
                tools=all_tools,
                stream=request.stream,
                thinking=request.thinking,
                thinking_budget=request.thinking_budget,
                code_execution=request.code_execution,
                container_id=request.container_id,
                images=request.images,
                files=request.files,
                uploaded_files=request.uploaded_files,
                file_uploads=request.file_uploads,
                mcp_servers=request.mcp_servers,
                timeout=request.timeout
            )
            
            logger.info(f"Added {len(mcp_tools)} MCP tools to request for user {user_id}")
            return updated_request
            
        except Exception as e:
            logger.error(f"Error adding MCP tools to request: {e}")
            return request
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using specified model"""
        try:
            
            config = get_model_config(request.model)
            
            if config.provider == ModelProvider.CLAUDE:
                return await self._generate_claude(request, config)
            elif config.provider == ModelProvider.GEMINI:
                return await self._generate_gemini(request, config)
            elif config.provider == ModelProvider.OPENAI:
                # OpenAI models are routed through OpenRouter
                return await self._generate_openai(request, config)
            else:
                raise ValueError(f"Provider {config.provider} not implemented")
                
        except Exception as e:
            logger.error(f"Error generating response with {request.model}: {str(e)}")
            return LLMResponse(
                content="",
                model=request.model,
                provider=config.provider.value if 'config' in locals() else "unknown",
                error=str(e)
            )
    
    async def generate_stream(self, request: LLMRequest):
        """Generate streaming response with thinking support"""
        try:
            config = get_model_config(request.model)
            
            if config.provider == ModelProvider.CLAUDE:
                async for chunk in self._generate_claude_stream(request, config):
                    yield chunk
            elif config.provider == ModelProvider.GEMINI:
                # DEBUG MCP: before generating, log MCP tool count if present
                try:
                    tool_names = []
                    if request.tools:
                        for t in request.tools:
                            if isinstance(t, dict):
                                if 'function' in t:
                                    tool_names.append(t['function'].get('name'))
                            else:
                                tool_names.append(str(type(t)))
                    logger.info(f"[MCP DEBUG] LLM request has {len(request.tools or [])} tools before streaming: {tool_names}")
                except Exception as dbg_e:
                    logger.warning(f"[MCP DEBUG] Failed to list tool names: {dbg_e}")
                async for chunk in self._generate_gemini_stream(request, config):
                    yield chunk
            elif config.provider == ModelProvider.OPENAI:
                # OpenAI models are routed through OpenRouter
                async for chunk in self._generate_openai_stream(request, config):
                    yield chunk
            else:
                raise ValueError(f"Provider {config.provider} not implemented")
                
        except Exception as e:
            logger.error(f"Error streaming response with {request.model}: {str(e)}")
            yield LLMStreamChunk(
                type="error",
                error=str(e),
                model=request.model,
                provider=config.provider.value if 'config' in locals() else "unknown"
            )
    
    async def _generate_claude(self, request: LLMRequest, config: ModelConfig) -> LLMResponse:
        """Generate response using Claude"""
        client = self._get_claude_client()
        
        # Prepare messages
        messages = []
        
        if request.messages:
            messages = request.messages.copy()
        else:
            # Convert single prompt to messages format
            content = []
            
            # Add text
            content.append({"type": "text", "text": request.prompt})
            
            # Add images if provided
            if request.images:
                for image_b64 in request.images:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",  # Assume JPEG for now
                            "data": image_b64
                        }
                    })
            
            messages = [{"role": "user", "content": content}]
        
        # Prepare request parameters
        params = {
            "model": config.model_id,
            "max_tokens": request.max_tokens or config.max_tokens,
            "temperature": request.temperature if request.temperature is not None else config.default_temperature,
            "messages": messages
        }
        
        if request.system_prompt:
            params["system"] = request.system_prompt
            
        # Handle tools and code execution
        tools_to_add = []
        if request.tools:
            tools_to_add.extend(request.tools)
            
        if request.code_execution:
            # Add Claude code execution tool
            tools_to_add.append({
                "type": "code_execution_20250522",
                "name": "code_execution"
            })
            
        if tools_to_add:
            params["tools"] = tools_to_add
            
        # Add container ID for reuse
        if request.container_id:
            params["container"] = request.container_id
            
        # Handle MCP servers
        if request.mcp_servers:
            params["mcp_servers"] = request.mcp_servers
            
        # Handle file uploads for Claude
        if request.file_uploads:
            # Upload files to Claude Files API first
            claude_files = await self._upload_files_to_claude(request.file_uploads)
            if claude_files:
                # Add files to messages content
                if isinstance(messages[-1]["content"], str):
                    # Convert string content to list format
                    messages[-1]["content"] = [{"type": "text", "text": messages[-1]["content"]}]
                elif not isinstance(messages[-1]["content"], list):
                    messages[-1]["content"] = [messages[-1]["content"]]
                    
                # Add file content blocks
                for claude_file in claude_files:
                    file_type = self._get_claude_file_content_type(claude_file)
                    if file_type == "document":
                        messages[-1]["content"].append({
                            "type": "document",
                            "source": {
                                "type": "file",
                                "file_id": claude_file["file_id"]
                            }
                        })
                    elif file_type == "image":
                        messages[-1]["content"].append({
                            "type": "image",
                            "source": {
                                "type": "file",
                                "file_id": claude_file["file_id"]
                            }
                        })
                    elif file_type == "container_upload":
                        messages[-1]["content"].append({
                            "type": "container_upload",
                            "file_id": claude_file["file_id"]
                        })
            
        try:
            # ============================================================
            # OPENROUTER ROUTING: Route through OpenRouter if enabled
            # ============================================================
            if USE_OPENROUTER and get_openrouter_handler:
                logger.info(f"[OPENROUTER] Routing _generate_claude to OpenRouter for model: {request.model}")
                openrouter = get_openrouter_handler()
                
                result = await openrouter.generate(
                    model=request.model,
                    prompt=request.prompt,
                    messages=request.messages,
                    system_prompt=request.system_prompt,
                    tools=request.tools,
                    images=request.images,
                    temperature=request.temperature if request.temperature is not None else config.default_temperature,
                    max_tokens=request.max_tokens or config.max_tokens,
                    thinking=request.thinking,
                    thinking_budget=request.thinking_budget
                )
                
                return LLMResponse(
                    content=result.get("content", ""),
                    model=request.model,
                    provider="openrouter",
                    usage=result.get("usage"),
                    function_calls=result.get("function_calls"),
                    thinking_content=result.get("thinking_content"),
                    finish_reason=result.get("finish_reason")
                )
            # ============================================================
            # END OPENROUTER ROUTING
            # ============================================================
            
            # Use beta client for code execution, files, or MCP
            needs_beta = request.code_execution or request.uploaded_files or request.file_uploads or request.mcp_servers
            if needs_beta:
                # Add beta headers for features
                beta_headers = []
                if request.code_execution:
                    beta_headers.append("code-execution-2025-05-22")
                if request.uploaded_files or request.file_uploads:
                    beta_headers.append("files-api-2025-04-14")
                if request.mcp_servers:
                    beta_headers.append("mcp-client-2025-04-04")
                
                # Use beta client
                response = await asyncio.to_thread(
                    client.beta.messages.create,
                    betas=beta_headers,
                    **params
                )
            else:
                # Regular client
                response = await asyncio.to_thread(
                    client.messages.create,
                    **params
                )
            
            # Extract content
            content = ""
            function_calls = []
            code_executions = []
            mcp_results = []
            
            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    # Guard function calls to only allowed names derived from tools
                    allowed_function_names = self._extract_allowed_function_names(params.get("tools")) if isinstance(params, dict) else []
                    if (not allowed_function_names) or (block.name in allowed_function_names):
                        function_calls.append({
                            "id": block.id,
                            "name": block.name,
                            "arguments": block.input
                        })
                    else:
                        logger.warning(f"[TOOLS GUARD] Suppressed disallowed Claude tool_use: {block.name}")
                elif block.type == "server_tool_use" and block.name == "code_execution":
                    # Code execution tool use
                    code_executions.append({
                        "type": "execution",
                        "id": block.id,
                        "code": block.input.get("code", "")
                    })
                elif block.type == "code_execution_tool_result":
                    # Code execution result
                    result_content = block.content
                    if result_content.type == "code_execution_result":
                        code_executions.append({
                            "type": "result",
                            "tool_use_id": block.tool_use_id,
                            "stdout": result_content.stdout,
                            "stderr": result_content.stderr,
                            "return_code": result_content.return_code,
                            "files": getattr(result_content, 'content', [])  # Created files
                        })
                    elif result_content.type == "code_execution_tool_result_error":
                        code_executions.append({
                            "type": "error",
                            "tool_use_id": block.tool_use_id,
                            "error_code": result_content.error_code
                        })
                elif block.type == "mcp_tool_use":
                    # MCP tool use
                    function_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "server_name": block.server_name,
                        "arguments": block.input,
                        "type": "mcp"
                    })
                elif block.type == "mcp_tool_result":
                    # MCP tool result
                    mcp_results.append({
                        "tool_use_id": block.tool_use_id,
                        "is_error": block.is_error,
                        "content": block.content
                    })
            
            return LLMResponse(
                content=content,
                model=request.model,
                provider="claude",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                function_calls=function_calls if function_calls else None,
                code_executions=code_executions if code_executions else None,
                mcp_results=mcp_results if mcp_results else None,
                container_id=getattr(response, 'container', {}).get('id') if hasattr(response, 'container') else None,
                finish_reason=response.stop_reason
            )
            
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise
    
    async def _generate_gemini(self, request: LLMRequest, config: ModelConfig) -> LLMResponse:
        """Generate response using Gemini"""
        genai = self._get_gemini_client()
        
        # Prepare generation config
        generation_config = {
            "temperature": request.temperature if request.temperature is not None else config.default_temperature
        }
        
        if request.json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        # Create model
        model_params = {
            "generation_config": generation_config
        }
        
        if request.system_prompt:
            model_params["system_instruction"] = request.system_prompt
            
        # Handle tools and code execution - CRITICAL: Consolidate into SINGLE Tool object!
        # Using multiple Tool objects causes 150+ second latency with Gemini 3.0!
        tools_to_add = []
        if request.tools:
            from google import genai as genai_client
            
            # Collect all FunctionDeclarations first
            function_declarations = []
            other_tools = []  # For non-dict tools (already Tool objects)
            
            for tool in request.tools:
                try:
                    if isinstance(tool, dict):
                        # Convert to FunctionDeclaration (NOT a full Tool!)
                        func_decl = self._convert_dict_tool_to_function_declaration(tool)
                        if func_decl:
                            function_declarations.append(func_decl)
                    else:
                        # Already a Tool object - keep separate (e.g., code_execution tool)
                        other_tools.append(tool)
                except Exception as e:
                    logger.warning(f"Failed to convert tool to Gemini format: {e}")
            
            # Create ONE Tool object with ALL function declarations
            if function_declarations:
                consolidated_tool = genai_client.types.Tool(
                    function_declarations=function_declarations
                )
                tools_to_add.append(consolidated_tool)
                logger.info(f"[TOOLS] Consolidated {len(function_declarations)} functions into 1 Tool object")
            
            # Add any other tools (like code_execution)
            tools_to_add.extend(other_tools)
            
        # Add Gemini-specific tools if needed
        if request.code_execution:
            # Add Gemini code execution tool
            import google.genai.types as types
            coding_tool = types.Tool(code_execution=types.ToolCodeExecution())
            tools_to_add.append(coding_tool)
            
        if tools_to_add:
            model_params["tools"] = tools_to_add
        
        try:
            # ============================================================
            # OPENROUTER ROUTING: Route through OpenRouter if enabled
            # ============================================================
            if USE_OPENROUTER and get_openrouter_handler:
                logger.info(f"[OPENROUTER] Routing _generate_gemini to OpenRouter for model: {request.model}")
                openrouter = get_openrouter_handler()
                
                result = await openrouter.generate(
                    model=request.model,
                    prompt=request.prompt,
                    messages=request.messages,
                    system_prompt=request.system_prompt,
                    tools=request.tools,
                    images=request.images,
                    temperature=request.temperature if request.temperature is not None else config.default_temperature,
                    max_tokens=request.max_tokens or config.max_tokens,
                    thinking=request.thinking,
                    thinking_budget=request.thinking_budget
                )
                
                return LLMResponse(
                    content=result.get("content", ""),
                    model=request.model,
                    provider="openrouter",
                    usage=result.get("usage"),
                    function_calls=result.get("function_calls"),
                    thinking_content=result.get("thinking_content"),
                    finish_reason=result.get("finish_reason")
                )
            # ============================================================
            # END OPENROUTER ROUTING
            # ============================================================
            
            # Handle different model ID formats
            model_id = config.model_id
            model = genai.GenerativeModel(model_id, **model_params)
            
            # Prepare content
            content_parts = []
            

            content_parts = request.prompt

                    
            # Handle file uploads for Gemini
            if request.file_uploads:
                gemini_files = await self._upload_files_to_gemini(request.file_uploads)
                if gemini_files:
                    content_parts.extend(gemini_files)
            
            response = await asyncio.to_thread(model.generate_content, content_parts)
            
            # Extract function calls and code executions if any
            function_calls = []
            code_executions = []
            # Derive allowed names from tools to guard any returned function calls
            allowed_function_names = self._extract_allowed_function_names(tools_to_add)
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Extract function calls
                if hasattr(candidate, 'function_calls') and candidate.function_calls:
                    for call in candidate.function_calls:
                        try:
                            call_name = getattr(call, 'name', None)
                            if (not allowed_function_names) or (call_name in allowed_function_names):
                                function_calls.append({
                                    "name": call_name,
                                    "arguments": dict(getattr(call, 'args', {}) or {})
                                })
                            else:
                                logger.warning(f"[TOOLS GUARD] Suppressed disallowed function_call (non-streaming gemini): {call_name}")
                        except Exception:
                            # Fallback to best-effort capture
                            function_calls.append({
                                "name": getattr(call, 'name', None),
                                "arguments": dict(getattr(call, 'args', {}) or {})
                            })
                
                # Extract code executions from content parts
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'executable_code') and part.executable_code:
                            code_executions.append({
                                "type": "execution",
                                "code": part.executable_code.code,
                                "language": getattr(part.executable_code, 'language', 'python')
                            })
                        elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                            result = part.code_execution_result
                            code_executions.append({
                                "type": "result",
                                "outcome": getattr(result, 'outcome', None),
                                "output": getattr(result, 'output', "")
                            })
            
            return LLMResponse(
                content=response.text if hasattr(response, 'text') else str(response),
                model=request.model,
                provider="gemini",
                usage={
                    "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0
                },
                function_calls=function_calls if function_calls else None,
                code_executions=code_executions if code_executions else None,
                finish_reason=getattr(response.candidates[0], 'finish_reason', None) if hasattr(response, 'candidates') and response.candidates else None
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def _generate_claude_stream(self, request: LLMRequest, config: ModelConfig):
        """Generate streaming response using Claude with thinking support"""
        client = self._get_claude_client()
        
        # Prepare messages (same as non-streaming)
        messages = []
        
        if request.messages:
            messages = request.messages.copy()
        else:
            # Convert single prompt to messages format
            content = []
            
            # Add text
            content.append({"type": "text", "text": request.prompt})
            
            # Add images if provided
            if request.images:
                for image_b64 in request.images:
                    content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",  # Assume JPEG for now
                            "data": image_b64
                        }
                    })
            
            messages = [{"role": "user", "content": content}]
        
        # Prepare request parameters
        params = {
            "model": config.model_id,
            "max_tokens": request.max_tokens or config.max_tokens,
            "temperature": request.temperature if request.temperature is not None else config.default_temperature,
            "messages": messages,
            "stream": True
        }
        
        if request.system_prompt:
            params["system"] = request.system_prompt
            
        if request.tools:
            params["tools"] = request.tools
            
        # Add thinking configuration if enabled
        if request.thinking:
            params["thinking"] = {
                "type": "enabled",
                "budget_tokens": request.thinking_budget
            }
        
        try:
            import time
            thinking_start_time = time.time()
            thinking_content = ""
            content = ""
            function_calls = []
            has_ended_thinking = False
            
            # ============================================================
            # OPENROUTER ROUTING: Route through OpenRouter if enabled
            # ============================================================
            if USE_OPENROUTER and get_openrouter_handler:
                logger.info(f"[OPENROUTER] Routing _generate_claude_stream to OpenRouter for model: {request.model}")
                openrouter = get_openrouter_handler()
                
                async for chunk in openrouter.generate_stream(
                    model=request.model,
                    prompt=request.prompt,
                    messages=request.messages,
                    system_prompt=request.system_prompt,
                    tools=request.tools,
                    images=request.images,
                    temperature=request.temperature if request.temperature is not None else config.default_temperature,
                    max_tokens=request.max_tokens or config.max_tokens,
                    thinking=request.thinking,
                    thinking_budget=request.thinking_budget
                ):
                    chunk_type = chunk.get("type", "")
                    
                    if chunk_type == "plan_thinking_chunk":
                        # Thinking/reasoning content
                        thinking_content += chunk.get("content", "")
                        yield LLMStreamChunk(
                            type="thinking",
                            content=chunk.get("content", ""),
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "content_chunk":
                        # Regular content
                        if thinking_content and not has_ended_thinking:
                            has_ended_thinking = True
                            thinking_time = time.time() - thinking_start_time
                            yield LLMStreamChunk(
                                type="thinking_done",
                                content=f"Thought for {thinking_time:.1f} seconds",
                                model=request.model,
                                provider="openrouter",
                                thinking_time=thinking_time
                            )
                        
                        content += chunk.get("content", "")
                        yield LLMStreamChunk(
                            type="content",
                            content=chunk.get("content", ""),
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "function_call":
                        # Function call
                        fc = chunk.get("function_call", {})
                        yield LLMStreamChunk(
                            type="function_call",
                            content="",
                            function_call=fc,
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "complete":
                        yield LLMStreamChunk(
                            type="done",
                            content=content,
                            model=request.model,
                            provider="openrouter",
                            is_final=True
                        )
                    elif chunk_type == "error":
                        yield LLMStreamChunk(
                            type="error",
                            error=chunk.get("content", "Unknown error"),
                            model=request.model,
                            provider="openrouter"
                        )
                    
                    await asyncio.sleep(0)
                
                # Return early - OpenRouter handled the request
                return
            # ============================================================
            # END OPENROUTER ROUTING
            # ============================================================
            
            # Make streaming call
            stream = await asyncio.to_thread(
                client.messages.create,
                **params
            )
            
            for event in stream:
                if event.type == "content_block_start":
                    # Starting a new content block
                    continue
                    
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, 'thinking') and event.delta.thinking:
                        # This is thinking content
                        thinking_content += event.delta.thinking
                        yield LLMStreamChunk(
                            type="thinking",
                            content=event.delta.thinking,
                            model=request.model,
                            provider="claude"
                        )
                    elif hasattr(event.delta, 'text') and event.delta.text:
                        # This is regular content
                        if thinking_content:  # We were in thinking mode
                            thinking_time = time.time() - thinking_start_time
                            yield LLMStreamChunk(
                                type="thinking_done",
                                content=f"Thought for {thinking_time:.1f} seconds",
                                model=request.model,
                                provider="claude",
                                thinking_time=thinking_time
                            )
                            thinking_content = ""
                        
                        content += event.delta.text
                        yield LLMStreamChunk(
                            type="content",
                            content=event.delta.text,
                            model=request.model,
                            provider="claude"
                        )
                        
                elif event.type == "content_block_stop":
                    # Content block finished
                    continue
                    
                elif event.type == "message_delta":
                    # Message finished
                    yield LLMStreamChunk(
                        type="done",
                        content=content,
                        model=request.model,
                        provider="claude",
                        is_final=True
                    )
                    break
                    
                await asyncio.sleep(0)  # Allow other tasks to run
                
        except Exception as e:
            logger.error(f"Claude streaming API error: {str(e)}")
            raise
    
    async def _generate_openai(self, request: LLMRequest, config: ModelConfig) -> LLMResponse:
        """Generate response using OpenAI models via OpenRouter"""
        if not get_openrouter_handler:
            raise ValueError("OpenRouter handler not available - required for OpenAI models")
        
        logger.info(f"[OPENAI] Routing to OpenRouter for model: {request.model}")
        openrouter = get_openrouter_handler()
        
        try:
            result = await openrouter.generate(
                model=request.model,
                prompt=request.prompt,
                messages=request.messages,
                system_prompt=request.system_prompt,
                tools=request.tools,
                images=request.images,
                temperature=request.temperature if request.temperature is not None else config.default_temperature,
                max_tokens=request.max_tokens or config.max_tokens,
                thinking=request.thinking,
                thinking_budget=request.thinking_budget
            )
            
            return LLMResponse(
                content=result.get("content", ""),
                model=request.model,
                provider="openai",
                usage=result.get("usage"),
                function_calls=result.get("function_calls"),
                thinking_content=result.get("thinking_content"),
                finish_reason=result.get("finish_reason")
            )
        except Exception as e:
            logger.error(f"OpenAI (via OpenRouter) API error: {str(e)}")
            raise
    
    async def _generate_openai_stream(self, request: LLMRequest, config: ModelConfig):
        """Generate streaming response using OpenAI models via OpenRouter"""
        if not get_openrouter_handler:
            raise ValueError("OpenRouter handler not available - required for OpenAI models")
        
        logger.info(f"[OPENAI] Streaming via OpenRouter for model: {request.model}")
        openrouter = get_openrouter_handler()
        
        import time
        thinking_start_time = time.time()
        thinking_content = ""
        content = ""
        has_ended_thinking = False
        
        try:
            async for chunk in openrouter.generate_stream(
                model=request.model,
                prompt=request.prompt,
                messages=request.messages,
                system_prompt=request.system_prompt,
                tools=request.tools,
                images=request.images,
                temperature=request.temperature if request.temperature is not None else config.default_temperature,
                max_tokens=request.max_tokens or config.max_tokens,
                thinking=request.thinking,
                thinking_budget=request.thinking_budget
            ):
                chunk_type = chunk.get("type", "")
                
                if chunk_type == "plan_thinking_chunk":
                    # Thinking/reasoning content
                    thinking_content += chunk.get("content", "")
                    yield LLMStreamChunk(
                        type="thinking",
                        content=chunk.get("content", ""),
                        model=request.model,
                        provider="openai"
                    )
                elif chunk_type == "content_chunk":
                    # Regular content
                    if thinking_content and not has_ended_thinking:
                        has_ended_thinking = True
                        thinking_time = time.time() - thinking_start_time
                        yield LLMStreamChunk(
                            type="thinking_done",
                            content=f"Thought for {thinking_time:.1f} seconds",
                            model=request.model,
                            provider="openai",
                            thinking_time=thinking_time
                        )
                    
                    content += chunk.get("content", "")
                    yield LLMStreamChunk(
                        type="content",
                        content=chunk.get("content", ""),
                        model=request.model,
                        provider="openai"
                    )
                elif chunk_type == "function_call":
                    # Function call
                    fc = chunk.get("function_call", {})
                    yield LLMStreamChunk(
                        type="function_call",
                        content="",
                        function_call=fc,
                        model=request.model,
                        provider="openai"
                    )
                elif chunk_type == "complete":
                    yield LLMStreamChunk(
                        type="done",
                        content=content,
                        model=request.model,
                        provider="openai",
                        is_final=True
                    )
                elif chunk_type == "error":
                    yield LLMStreamChunk(
                        type="error",
                        error=chunk.get("content", "Unknown error"),
                        model=request.model,
                        provider="openai"
                    )
                
                await asyncio.sleep(0)
                
        except Exception as e:
            logger.error(f"OpenAI streaming (via OpenRouter) API error: {str(e)}")
            raise
    
    async def _generate_gemini_stream(self, request: LLMRequest, config: ModelConfig):
        """Generate streaming response using Gemini with thinking support"""
        genai = self._get_gemini_client()
        
        # Prepare generation config
        generation_config = {
            "temperature": request.temperature if request.temperature is not None else config.default_temperature
        }
        
        if request.json_mode:
            generation_config["response_mime_type"] = "application/json"
        
        # Create model config
        model_params = {
            "generation_config": generation_config
        }
        
        if request.system_prompt:
            model_params["system_instruction"] = request.system_prompt
            
        # Handle tools and code execution - CRITICAL: Consolidate into SINGLE Tool object!
        # Using multiple Tool objects causes 150+ second latency with Gemini 3.0!
        tools_to_add = []
        if request.tools:
            from google import genai as genai_client
            
            # Collect all FunctionDeclarations first
            function_declarations = []
            other_tools = []  # For non-dict tools (already Tool objects)
            
            for tool in request.tools:
                try:
                    if isinstance(tool, dict):
                        # Convert to FunctionDeclaration (NOT a full Tool!)
                        func_decl = self._convert_dict_tool_to_function_declaration(tool)
                        if func_decl:
                            function_declarations.append(func_decl)
                    else:
                        # Already a Tool object - keep separate (e.g., code_execution tool)
                        other_tools.append(tool)
                except Exception as e:
                    logger.warning(f"Failed to convert tool to Gemini format: {e}")
            
            # Create ONE Tool object with ALL function declarations
            # This is the FIX for the 150+ second latency issue!
            if function_declarations:
                consolidated_tool = genai_client.types.Tool(
                    function_declarations=function_declarations
                )
                tools_to_add.append(consolidated_tool)
                logger.info(f"[TOOLS] Consolidated {len(function_declarations)} functions into 1 Tool object")
            
            # Add any other tools (like code_execution)
            tools_to_add.extend(other_tools)
            
        # Add Gemini-specific tools if needed
        if request.code_execution:
            # Add Gemini code execution tool
            import google.genai.types as types
            coding_tool = types.Tool(code_execution=types.ToolCodeExecution())
            tools_to_add.append(coding_tool)
            
        # Handle MCP servers for Gemini
        if request.mcp_servers:
            for mcp_server in request.mcp_servers:
                # Create MCP tool configuration for Gemini
                from mcp import ClientSession, StdioServerParameters
                # Note: This would need the MCP client session setup
                # For now, we'll add it as a regular tool placeholder
                logger.warning("MCP server support for Gemini requires additional implementation")
            
        if tools_to_add:
            model_params["tools"] = tools_to_add
        
        # Add thinking config if enabled and using a thinking model
        thinking_config = None
        if request.thinking:
            from google import genai as genai_client
            thinking_config = genai_client.types.ThinkingConfig(include_thoughts=True)
        
        try:
            import time
            
            # Handle different model ID formats
            model_id = config.model_id
            # Check if we're using Gemini 3.0 which requires thought_signature
            # Define at function scope so it's accessible throughout
            is_gemini_3 = "gemini-3" in request.model.lower() if request.model else False
            
            # Prepare content
            # For Gemini 3.0, we must preserve the full conversation history structure
            # including function calls with thought_signature fields
            # Check if prompt is a conversation history (list of dicts with role/parts)
            prompt_is_conversation = (
                isinstance(request.prompt, list) and 
                len(request.prompt) > 0 and 
                isinstance(request.prompt[0], dict) and 
                "role" in request.prompt[0]
            )
            
            if request.messages or prompt_is_conversation:
                # Pass the structured conversation history directly
                # This preserves thought_signature fields in function_call parts
                from google import genai as genai_client
                
                # Use messages if available, otherwise use prompt as conversation history
                conversation_history = request.messages if request.messages else request.prompt

                content_parts = []
                function_call_counter = 0

                def _convert_part(part_obj, role: str):
                    nonlocal function_call_counter
                    if isinstance(part_obj, dict):
                        if "text" in part_obj:
                            return genai_client.types.Part(text=part_obj["text"])
                        if "function_call" in part_obj:
                            fc = part_obj["function_call"] or {}
                            fc_kwargs = {
                                "name": fc.get("name"),
                                "args": fc.get("args", {})
                            }
                            signature = fc.get("thought_signature")
                            function_call_counter += 1
                            function_call = genai_client.types.FunctionCall(
                                name=fc_kwargs.get("name"),
                                args=fc_kwargs.get("args", {})
                            )

                            # CRITICAL: For Gemini 3.0, use dummy signature when migrating from other models
                            # Per Google docs: when transferring conversation from other models or injecting
                            # custom function calls, use dummy string to bypass strict validation
                            if signature:
                                # Real signature from Gemini 3.0
                                return genai_client.types.Part(
                                    function_call=function_call,
                                    thought_signature=signature
                                )
                            elif is_gemini_3:
                                # Dummy signature for migration from other models
                                logger.info(f"[THOUGHT_SIG] Adding dummy signature for function call {fc_kwargs.get('name')} (migrating to Gemini 3.0)")
                                return genai_client.types.Part(
                                    function_call=function_call,
                                    thought_signature="context_engineering_is_the_way_to_go"
                                )
                            else:
                                # Other models - no signature needed
                                return genai_client.types.Part(
                                    function_call=function_call
                                )
                        if "function_response" in part_obj:
                            fr = part_obj["function_response"] or {}
                            return genai_client.types.Part(
                                function_response=genai_client.types.FunctionResponse(
                                    name=fr.get("name"),
                                    response=fr.get("response", {})
                                )
                            )
                    else:
                        fc_obj = getattr(part_obj, "function_call", None)
                        if fc_obj:
                            fc_kwargs = {
                                "name": getattr(fc_obj, "name", None),
                                "args": dict(getattr(fc_obj, "args", {}) or {})
                            }
                            signature = getattr(fc_obj, "thought_signature", None)
                            part_signature = getattr(part_obj, "thought_signature", None)
                            # Use part signature if available, otherwise fall back to function_call signature
                            if not part_signature:
                                part_signature = signature
                            function_call_counter += 1

                            # CRITICAL: For Gemini 3.0, use dummy signature when migrating from other models
                            # Per Google docs: when transferring conversation from other models or injecting
                            # custom function calls, use dummy string to bypass strict validation
                            if part_signature:
                                # Real signature from Gemini 3.0
                                return genai_client.types.Part(
                                    function_call=genai_client.types.FunctionCall(
                                        name=fc_kwargs.get("name"),
                                        args=fc_kwargs.get("args", {})
                                    ),
                                    thought_signature=part_signature
                                )
                            elif is_gemini_3:
                                # Dummy signature for migration from other models
                                logger.info(f"[THOUGHT_SIG] Adding dummy signature for function call {fc_kwargs.get('name')} (migrating to Gemini 3.0)")
                                return genai_client.types.Part(
                                    function_call=genai_client.types.FunctionCall(
                                        name=fc_kwargs.get("name"),
                                        args=fc_kwargs.get("args", {})
                                    ),
                                    thought_signature="context_engineering_is_the_way_to_go"
                                )
                            else:
                                # Other models - no signature needed
                                return genai_client.types.Part(
                                    function_call=genai_client.types.FunctionCall(
                                        name=fc_kwargs.get("name"),
                                        args=fc_kwargs.get("args", {})
                                    )
                                )
                    return part_obj

                for msg in conversation_history:
                    try:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            parts = msg.get("parts", [])

                            sdk_parts = []
                            for part in parts:
                                converted = _convert_part(part, role)
                                if converted:
                                    sdk_parts.append(converted)

                            if sdk_parts:
                                content_parts.append(genai_client.types.Content(
                                    role=role,
                                    parts=sdk_parts
                                ))
                        else:
                            role = getattr(msg, "role", "user")
                            # Convert the Part objects inside existing Content as needed
                            sdk_parts = []
                            for part in getattr(msg, "parts", []):
                                converted = _convert_part(part, role)
                                if converted:
                                    sdk_parts.append(converted)
                            if sdk_parts:
                                content_parts.append(genai_client.types.Content(
                                    role=role,
                                    parts=sdk_parts
                                ))
                            else:
                                content_parts.append(msg)
                    except Exception as e:
                        logger.error(f"Error converting message to SDK format: {e}")
                        # Fallback: try to extract text
                        if isinstance(msg, dict) and msg.get("parts"):
                            text_content = " ".join([p.get("text", "") for p in msg.get("parts", []) if p.get("text")])
                            if text_content:
                                content_parts.append(genai_client.types.Content(
                                    role=msg.get("role", "user"),
                                    parts=[genai_client.types.Part(text=text_content)]
                                ))
            else:
                # No conversation history, just use the prompt
                content_parts = request.prompt
            
                
            # Handle file uploads for Gemini streaming
            if request.file_uploads:
                gemini_files = await self._upload_files_to_gemini(request.file_uploads)
                if gemini_files:
                    content_parts.extend(gemini_files)
            
            # Handle images for Gemini - add as inline_data parts
            if request.images:
                import base64
                from google import genai as genai_client
                
                logger.info(f"[GEMINI_IMAGES] Adding {len(request.images)} image(s) to Gemini request")
                
                # Create a new user message with the images if content_parts is a list
                if isinstance(content_parts, list):
                    image_parts = []
                    for i, img_base64 in enumerate(request.images):
                        try:
                            # Decode base64 to bytes
                            img_bytes = base64.b64decode(img_base64)
                            
                            # Detect MIME type from image data (simple detection based on magic bytes)
                            if img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                                mime_type = 'image/png'
                            elif img_bytes[:2] == b'\xff\xd8':
                                mime_type = 'image/jpeg'
                            elif img_bytes[:6] in (b'GIF87a', b'GIF89a'):
                                mime_type = 'image/gif'
                            elif img_bytes[:4] == b'RIFF' and img_bytes[8:12] == b'WEBP':
                                mime_type = 'image/webp'
                            else:
                                mime_type = 'image/jpeg'  # Default to JPEG
                            
                            # Create Gemini inline_data part
                            image_part = genai_client.types.Part(
                                inline_data=genai_client.types.Blob(
                                    mime_type=mime_type,
                                    data=img_bytes
                                )
                            )
                            image_parts.append(image_part)
                            logger.info(f"[GEMINI_IMAGES] Added image {i+1} ({mime_type}, {len(img_bytes):,} bytes)")
                        except Exception as e:
                            logger.error(f"[GEMINI_IMAGES] Error processing image {i+1}: {e}")
                    
                    if image_parts:
                        # Add images as a user message at the end of the conversation
                        # This ensures the model "sees" them with the latest context
                        image_content = genai_client.types.Content(
                            role="user",
                            parts=[genai_client.types.Part(text="[Image file(s) attached above. Please analyze the image(s) as requested.]")] + image_parts
                        )
                        content_parts.append(image_content)
                        logger.info(f"[GEMINI_IMAGES] Successfully added {len(image_parts)} image(s) to conversation")
            
            # Use the new Gemini streaming API with thinking
            from google import genai as genai_client
            client = genai_client.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            thinking_start_time = time.time()
            thinking_content = ""
            content = ""
            has_ended_thinking = False
            
            # Configure request - use the exact format from working example
            from google import genai as genai_client
            
            # Derive allowed function names from provided tools and enforce at API level
            allowed_function_names = self._extract_allowed_function_names(tools_to_add)

            stream_config = genai_client.types.GenerateContentConfig(
                system_instruction=request.system_prompt,
                tools=tools_to_add if tools_to_add else None,
                temperature=request.temperature if request.temperature is not None else config.default_temperature,
            )
            if allowed_function_names:
                try:
                    stream_config.tool_config = genai_client.types.ToolConfig(
                        function_calling_config=genai_client.types.FunctionCallingConfig(
                            mode='ANY',
                            allowed_function_names=allowed_function_names
                        )
                    )
                except Exception as e:
                    logger.warning(f"[TOOLS GUARD] Failed to set allowed_function_names: {e}")
            
            if thinking_config:
                stream_config.thinking_config = thinking_config

            # ============================================================
            # OPENROUTER ROUTING: Route through OpenRouter if enabled
            # ============================================================
            if USE_OPENROUTER and get_openrouter_handler:
                logger.info(f"[OPENROUTER] Routing _generate_gemini_stream to OpenRouter for model: {request.model}")
                openrouter = get_openrouter_handler()
                
                async for chunk in openrouter.generate_stream(
                    model=request.model,
                    prompt=request.prompt,
                    messages=request.messages,
                    system_prompt=request.system_prompt,
                    tools=request.tools,
                    images=request.images,
                    temperature=request.temperature if request.temperature is not None else config.default_temperature,
                    max_tokens=request.max_tokens or config.max_tokens,
                    thinking=request.thinking,
                    thinking_budget=request.thinking_budget,
                    is_gemini_3=is_gemini_3
                ):
                    chunk_type = chunk.get("type", "")
                    
                    if chunk_type == "plan_thinking_chunk":
                        # Thinking/reasoning content
                        thinking_content += chunk.get("content", "")
                        yield LLMStreamChunk(
                            type="thinking",
                            content=chunk.get("content", ""),
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "content_chunk":
                        # Regular content
                        if thinking_content and not has_ended_thinking:
                            has_ended_thinking = True
                            thinking_time = time.time() - thinking_start_time
                            yield LLMStreamChunk(
                                type="thinking_done",
                                content=f"Thought for {thinking_time:.1f} seconds",
                                model=request.model,
                                provider="openrouter",
                                thinking_time=thinking_time
                            )
                        
                        content += chunk.get("content", "")
                        yield LLMStreamChunk(
                            type="content",
                            content=chunk.get("content", ""),
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "function_call":
                        # Function call - preserve thought_signature for Gemini 3.0
                        fc = chunk.get("function_call", {})
                        yield LLMStreamChunk(
                            type="function_call",
                            content="",
                            function_call=fc,
                            model=request.model,
                            provider="openrouter"
                        )
                    elif chunk_type == "complete":
                        yield LLMStreamChunk(
                            type="done",
                            content=content,
                            model=request.model,
                            provider="openrouter",
                            is_final=True
                        )
                    elif chunk_type == "error":
                        yield LLMStreamChunk(
                            type="error",
                            error=chunk.get("content", "Unknown error"),
                            model=request.model,
                            provider="openrouter"
                        )
                    
                    await asyncio.sleep(0)
                
                # Return early - OpenRouter handled the request
                return
            # ============================================================
            # END OPENROUTER ROUTING
            # ============================================================
            
            # Stream the response
            for chunk in client.models.generate_content_stream(
                model=model_id,
                contents=content_parts,
                config=stream_config
            ):
                if (hasattr(chunk, 'candidates') and chunk.candidates and 
                    hasattr(chunk.candidates[0], 'content') and 
                    hasattr(chunk.candidates[0].content, 'parts') and
                    chunk.candidates[0].content.parts is not None):
                    
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            # This is thinking content
                            try:
                                if hasattr(part, 'text') and part.text is not None:
                                    thinking_content += part.text
                                    yield LLMStreamChunk(
                                        type="thinking",
                                        content=part.text,
                                        model=request.model,
                                        provider="gemini"
                                    )
                            except AttributeError:
                                pass
                        elif hasattr(part, 'function_call') and part.function_call:
                            # Emit function_call as a dedicated chunk (do not leak as thinking content)
                            try:
                                fc = part.function_call
                                fc_payload = {
                                    "name": getattr(fc, 'name', None),
                                    "arguments": dict(getattr(fc, 'args', {}) or {})
                                }
                                # CRITICAL: Capture thought_signature for Gemini 3.0
                                # Try multiple possible attribute names (snake_case and camelCase)
                                part_thought_sig = (
                                    getattr(part, 'thought_signature', None) or 
                                    getattr(part, 'thoughtSignature', None) or
                                    getattr(fc, 'thought_signature', None) or
                                    getattr(fc, 'thoughtSignature', None)
                                )
                                
                                # Debug: Log all Part attributes to find where thought_signature is
                                try:
                                    part_attrs = [attr for attr in dir(part) if not attr.startswith('_')]
                                    fc_attrs = [attr for attr in dir(fc) if not attr.startswith('_')]
                                except Exception:
                                    pass
                                
                                if part_thought_sig:
                                    fc_payload["thought_signature"] = part_thought_sig
                                else:
                                    # For Gemini 3.0, we need a thought_signature even if not provided
                                    # Use dummy signature for migration compatibility
                                    if is_gemini_3:
                                        fc_payload["thought_signature"] = "context_engineering_is_the_way_to_go"
                                        logger.info(f"[THOUGHT_SIG] Added dummy signature for Gemini 3.0 compatibility for {fc_payload.get('name')}")
                                    else:
                                        logger.warning(f"[THOUGHT_SIG] No thought_signature found on Part or FunctionCall for {fc_payload.get('name')}")
                            except Exception as e:
                                logger.warning(f"[THOUGHT_SIG] Error capturing function_call: {e}")
                                fc_payload = {"name": None, "arguments": {}}
                                # Add dummy signature for Gemini 3.0 even on error
                                if is_gemini_3:
                                    fc_payload["thought_signature"] = "context_engineering_is_the_way_to_go"
                            # Enforce allowed function names
                            if not allowed_function_names or fc_payload.get("name") in allowed_function_names:
                                yield LLMStreamChunk(
                                    type="function_call",
                                    content="",
                                    function_call=fc_payload,
                                    model=request.model,
                                    provider="gemini"
                                )
                            else:
                                logger.warning(f"[TOOLS GUARD] Suppressed disallowed function_call: {fc_payload.get('name')}")
                        elif hasattr(part, 'executable_code') and part.executable_code:
                            # Code execution in thinking or regular mode
                            code_execution = {
                                "code": part.executable_code.code,
                                "language": getattr(part.executable_code, 'language', 'python')
                            }
                            
                            if thinking_content:
                                # In thinking mode
                                yield LLMStreamChunk(
                                    type="thinking",
                                    content=f"\n\nExecuting code:\n```python\n{part.executable_code.code}\n```\n\n",
                                    model=request.model,
                                    provider="gemini"
                                )
                            else:
                                # Regular code execution
                                yield LLMStreamChunk(
                                    type="code_execution",
                                    content="",
                                    code_execution=code_execution,
                                    model=request.model,
                                    provider="gemini"
                                )
                        elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                            # Handle code execution results
                            result = part.code_execution_result
                            code_result = {
                                "outcome": getattr(result, 'outcome', None),
                                "output": getattr(result, 'output', "")
                            }
                            
                            if thinking_content:
                                # In thinking mode
                                output_text = getattr(result, 'output', "")
                                if output_text:
                                    yield LLMStreamChunk(
                                        type="thinking",
                                        content=f"\n\nCode output:\n{output_text}\n\n",
                                        model=request.model,
                                        provider="gemini"
                                    )
                            else:
                                # Regular code result
                                yield LLMStreamChunk(
                                    type="code_result",
                                    content="",
                                    code_result=code_result,
                                    model=request.model,
                                    provider="gemini"
                                )
                            
                            await asyncio.sleep(0)
                        else:
                            # Regular content
                            if thinking_content and not has_ended_thinking:
                                has_ended_thinking = True
                                thinking_time = time.time() - thinking_start_time
                                yield LLMStreamChunk(
                                    type="thinking_done",
                                    content=f"Thought for {thinking_time:.1f} seconds",
                                    model=request.model,
                                    provider="gemini",
                                    thinking_time=thinking_time
                                )
                            
                            # This is the actual content
                            try:
                                if hasattr(part, 'text') and part.text is not None:
                                    content += part.text
                                    yield LLMStreamChunk(
                                        type="content",
                                        content=part.text,
                                        model=request.model,
                                        provider="gemini"
                                    )
                            except AttributeError:
                                pass
                        
                        await asyncio.sleep(0)  # Allow other tasks to run
            
            # Final chunk
            yield LLMStreamChunk(
                type="done",
                content=content,
                model=request.model,
                provider="gemini",
                is_final=True
            )
                    
        except Exception as e:
            logger.error(f"Gemini streaming API error: {str(e)}")
            raise
    
    async def _upload_files_to_claude(self, file_uploads: List[Dict]) -> List[Dict]:
        """Upload files to Claude Files API"""
        client = self._get_claude_client()
        uploaded_files = []
        
        for file_upload in file_uploads:
            try:
                file_path = file_upload.get('path')
                file_bytes = file_upload.get('bytes')
                file_name = file_upload.get('name', 'uploaded_file')
                
                # Check cache first
                cache_key = f"{file_name}_{hash(str(file_upload))}"
                if cache_key in self._claude_files_uploaded:
                    uploaded_files.append(self._claude_files_uploaded[cache_key])
                    continue
                
                if file_path:
                    # Upload from file path
                    file_object = await asyncio.to_thread(
                        client.beta.files.upload,
                        file=open(file_path, "rb")
                    )
                elif file_bytes:
                    # Upload from bytes
                    import io
                    file_like = io.BytesIO(file_bytes)
                    file_object = await asyncio.to_thread(
                        client.beta.files.upload,
                        file=(file_name, file_like)
                    )
                else:
                    logger.warning(f"File upload missing both path and bytes: {file_upload}")
                    continue
                
                file_info = {
                    "file_id": file_object.id,
                    "name": file_name,
                    "mime_type": getattr(file_object, 'mime_type', 'application/octet-stream')
                }
                
                # Cache the result
                self._claude_files_uploaded[cache_key] = file_info
                uploaded_files.append(file_info)
                
                logger.info(f"Successfully uploaded {file_name} to Claude Files API: {file_object.id}")
                
            except Exception as e:
                logger.error(f"Failed to upload file to Claude: {e}")
                continue
                
        return uploaded_files
    
    async def _upload_files_to_gemini(self, file_uploads: List[Dict]) -> List[object]:
        """Upload files to Gemini Files API"""
        genai = self._get_gemini_client()
        uploaded_files = []
        
        for file_upload in file_uploads:
            try:
                file_path = file_upload.get('path')
                file_bytes = file_upload.get('bytes')
                file_name = file_upload.get('name', 'uploaded_file')
                
                # Check cache first
                cache_key = f"{file_name}_{hash(str(file_upload))}"
                if cache_key in self._gemini_files_uploaded:
                    uploaded_files.append(self._gemini_files_uploaded[cache_key])
                    continue
                
                if file_path:
                    # Upload from file path
                    import os
                    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                    uploaded_file = client.files.upload(file=file_path)
                elif file_bytes:
                    # Create temporary file for Gemini upload
                    import tempfile
                    import os
                    
                    file_extension = ''
                    if '.' in file_name:
                        file_extension = '.' + file_name.rsplit('.', 1)[-1].lower()
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                        temp_file.write(file_bytes)
                        temp_file_path = temp_file.name
                    
                    try:
                        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                        uploaded_file = client.files.upload(file=temp_file_path)
                    finally:
                        os.unlink(temp_file_path)
                else:
                    logger.warning(f"File upload missing both path and bytes: {file_upload}")
                    continue
                
                # Cache the result
                self._gemini_files_uploaded[cache_key] = uploaded_file
                uploaded_files.append(uploaded_file)
                
                logger.info(f"Successfully uploaded {file_name} to Gemini Files API: {uploaded_file.uri}")
                
            except Exception as e:
                logger.error(f"Failed to upload file to Gemini: {e}")
                continue
                
        return uploaded_files
    
    def _get_claude_file_content_type(self, file_info: Dict) -> str:
        """Determine Claude content block type based on file MIME type"""
        mime_type = file_info.get('mime_type', '').lower()
        
        if mime_type in ['application/pdf', 'text/plain']:
            return 'document'
        elif mime_type.startswith('image/'):
            return 'image'
        else:
            # For datasets and other files, use container_upload for code execution
            return 'container_upload'
    
    def _convert_dict_tool_to_function_declaration(self, tool_dict: Dict) -> Optional[object]:
        """Convert dictionary tool definition to Gemini FunctionDeclaration (NOT a full Tool).
        
        IMPORTANT: Returns FunctionDeclaration, not Tool. Multiple FunctionDeclarations
        should be consolidated into a SINGLE Tool object to avoid Gemini 3.0 latency issues.
        Using multiple Tool objects causes 150+ second delays!
        """
        try:
            from google import genai as genai_client
            
            # Handle different dictionary formats
            if "function" in tool_dict:
                # OpenAPI format: {"type": "function", "function": {...}}
                func_def = tool_dict["function"]
                tool_name = func_def["name"]
                tool_description = func_def["description"]
                tool_parameters = func_def.get("parameters", {})
            else:
                # Gemini dictionary format: {"name": "...", "description": "...", "parameters": {...}}
                tool_name = tool_dict["name"]
                tool_description = tool_dict["description"]
                tool_parameters = tool_dict.get("parameters", {})
            
            # Convert parameters to Gemini schema format
            gemini_parameters = self._convert_parameters_to_gemini_schema(tool_parameters)
            
            # Validate array items for cc/bcc if present
            try:
                from google import genai as genai_client
                props = gemini_parameters.get('properties', {})
                for list_field in ['cc', 'bcc', 'to_recipients', 'cc_recipients', 'bcc_recipients', 'label_ids']:
                    if list_field in props:
                        field_type = props[list_field].get('type')
                        # Handle both string "array" and genai_client.types.Type.ARRAY
                        if (field_type == genai_client.types.Type.ARRAY or field_type == "array") and 'items' not in props[list_field]:
                            props[list_field]['items'] = {'type': genai_client.types.Type.STRING}
            except Exception as e:
                pass

            # Create Gemini FunctionDeclaration (NOT a full Tool!)
            function_declaration = genai_client.types.FunctionDeclaration(
                name=tool_name,
                description=tool_description,
                parameters=gemini_parameters
            )
            
            return function_declaration
            
        except Exception as e:
            logger.error(f"Error converting tool to Gemini FunctionDeclaration: {e}")
            return None

    def _convert_dict_tool_to_gemini_tool(self, tool_dict: Dict) -> Optional[object]:
        """DEPRECATED: Use _convert_dict_tool_to_function_declaration instead.
        
        This method creates a separate Tool object per function which causes
        150+ second latency with Gemini 3.0. Kept for backwards compatibility.
        """
        try:
            from google import genai as genai_client
            func_decl = self._convert_dict_tool_to_function_declaration(tool_dict)
            if func_decl:
                return genai_client.types.Tool(function_declarations=[func_decl])
            return None
        except Exception as e:
            logger.error(f"Error converting tool to Gemini format: {e}")
            return None
    
    def _convert_parameters_to_gemini_schema(self, parameters: Dict) -> Dict:
        """Convert tool parameters to Gemini schema format"""
        try:
            from google import genai
            
            if not parameters:
                return {}
            
            # Handle both OpenAPI and Gemini parameter formats
            if "properties" in parameters:
                # Already has properties structure
                gemini_schema = {
                    "type": genai.types.Type.OBJECT,
                    "properties": {}
                }
                
                for param_name, param_def in parameters["properties"].items():
                    gemini_param = {}
                    
                    # Convert parameter type
                    param_type = param_def.get("type", "STRING").upper()
                    if param_type == "STRING":
                        gemini_param["type"] = genai.types.Type.STRING
                    elif param_type == "INTEGER" or param_type == "NUMBER":
                        gemini_param["type"] = genai.types.Type.NUMBER
                    elif param_type == "BOOLEAN":
                        gemini_param["type"] = genai.types.Type.BOOLEAN
                    elif param_type == "ARRAY":
                        gemini_param["type"] = genai.types.Type.ARRAY
                        # CRITICAL: Gemini 3.0 REQUIRES items field for all arrays
                        if "items" in param_def:
                            # Convert items type from original definition
                            items_def = param_def["items"]
                            if isinstance(items_def, dict) and "type" in items_def:
                                items_type = items_def["type"].upper()
                                if items_type == "STRING":
                                    gemini_param["items"] = {"type": genai.types.Type.STRING}
                                elif items_type == "INTEGER" or items_type == "NUMBER":
                                    gemini_param["items"] = {"type": genai.types.Type.NUMBER}
                                elif items_type == "BOOLEAN":
                                    gemini_param["items"] = {"type": genai.types.Type.BOOLEAN}
                                elif items_type == "OBJECT":
                                    # CRITICAL: For OBJECT items, recursively convert nested properties and required fields
                                    if "properties" in items_def:
                                        nested_properties = {}
                                        for nested_name, nested_def in items_def["properties"].items():
                                            nested_prop = {}
                                            nested_prop_type = nested_def.get("type", "STRING").upper()
                                            if nested_prop_type == "STRING":
                                                nested_prop["type"] = genai.types.Type.STRING
                                            elif nested_prop_type == "INTEGER" or nested_prop_type == "NUMBER":
                                                nested_prop["type"] = genai.types.Type.NUMBER
                                            elif nested_prop_type == "BOOLEAN":
                                                nested_prop["type"] = genai.types.Type.BOOLEAN
                                            elif nested_prop_type == "ARRAY":
                                                nested_prop["type"] = genai.types.Type.ARRAY
                                                # Handle nested array items
                                                if "items" in nested_def:
                                                    nested_items_type = nested_def["items"].get("type", "STRING").upper()
                                                    if nested_items_type == "STRING":
                                                        nested_prop["items"] = {"type": genai.types.Type.STRING}
                                                    else:
                                                        nested_prop["items"] = {"type": genai.types.Type.STRING}
                                                else:
                                                    nested_prop["items"] = {"type": genai.types.Type.STRING}
                                            elif nested_prop_type == "OBJECT":
                                                nested_prop["type"] = genai.types.Type.OBJECT
                                            else:
                                                nested_prop["type"] = genai.types.Type.STRING
                                            
                                            if "description" in nested_def:
                                                nested_prop["description"] = nested_def["description"]
                                            
                                            nested_properties[nested_name] = nested_prop
                                        
                                        gemini_param["items"] = {
                                            "type": genai.types.Type.OBJECT,
                                            "properties": nested_properties
                                        }
                                        
                                        # Add required fields for nested object if present
                                        if "required" in items_def:
                                            gemini_param["items"]["required"] = items_def["required"]
                                    else:
                                        gemini_param["items"] = {"type": genai.types.Type.OBJECT}
                                else:
                                    gemini_param["items"] = {"type": genai.types.Type.STRING}  # Default fallback
                            else:
                                gemini_param["items"] = {"type": genai.types.Type.STRING}  # Fallback for simplified format
                        else:
                            # No items defined - add default STRING items for Gemini 3.0 compatibility
                            gemini_param["items"] = {"type": genai.types.Type.STRING}
                    elif param_type == "OBJECT":
                        gemini_param["type"] = genai.types.Type.OBJECT
                    else:
                        gemini_param["type"] = genai.types.Type.STRING
                    
                    # Add description
                    if "description" in param_def:
                        gemini_param["description"] = param_def["description"]
                    
                    # Add enum values if present
                    if "enum" in param_def:
                        gemini_param["enum"] = param_def["enum"]
                    
                    gemini_schema["properties"][param_name] = gemini_param
                
                # Add required fields
                if "required" in parameters:
                    gemini_schema["required"] = parameters["required"]
                
                return gemini_schema
            else:
                # Direct parameter format - convert to properties structure
                return {
                    "type": genai.types.Type.OBJECT,
                    "properties": parameters
                }
                
        except Exception as e:
            logger.error(f"Error converting parameters schema: {e}")
            return {}

    def _generate_thought_signature(self, counter: int, role: Optional[str], function_name: Optional[str]) -> str:
        """Create deterministic fallback thought signatures for Gemini function calls.

        Gemini 3.0 requires every functionCall part to include a thought_signature.
        Older chat history entries might not have one recorded, so we synthesize a
        stable value to keep the API happy while still allowing responses to be
        associated with their originating calls.
        """
        safe_role = (role or "user").replace(" ", "_")
        safe_name = (function_name or "function_call").replace(" ", "_")
        return f"auto_sig_{safe_role}_{safe_name}_{counter}"

    def _extract_allowed_function_names(self, tools: Optional[List[Any]]) -> List[str]:
        """Extract a whitelist of function names from provided tools.

        Supports both dict-style tools (OpenAPI and Gemini-like) and SDK Tool objects
        that expose function_declarations.
        """
        allowed_names: List[str] = []
        try:
            for tool in tools or []:
                try:
                    # Dict tool formats
                    if isinstance(tool, dict):
                        if 'function' in tool and isinstance(tool.get('function'), dict):
                            name = tool['function'].get('name')
                            if name:
                                allowed_names.append(name)
                        else:
                            name = tool.get('name')
                            if name:
                                allowed_names.append(name)
                    else:
                        # SDK Tool with function_declarations
                        fds = getattr(tool, 'function_declarations', None)
                        if fds:
                            for fd in fds:
                                name = getattr(fd, 'name', None)
                                if name:
                                    allowed_names.append(name)
                except Exception:
                    # Continue extracting from other tools even if one fails
                    continue
        except Exception as e:
            logger.warning(f"[TOOLS GUARD] Failed to iterate tools for allowed names: {e}")
        # De-duplicate preserving order
        seen = set()
        unique_names: List[str] = []
        for n in allowed_names:
            if n and n not in seen:
                seen.add(n)
                unique_names.append(n)
        return unique_names

# Global handler instance
_handler = None

def get_llm_handler() -> LLMHandler:
    """Get global LLM handler instance"""
    global _handler
    if _handler is None:
        _handler = LLMHandler()
    return _handler

async def generate_response(
    prompt: str,
    model: str = "gemini-2.5-flash",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    system_prompt: Optional[str] = None,
    json_mode: bool = False,
    **kwargs
) -> str:
    """Convenience function for simple text generation"""
    handler = get_llm_handler()
    
    request = LLMRequest(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
        json_mode=json_mode,
        **kwargs
    )
    
    response = await handler.generate(request)
    
    if response.error:
        raise Exception(f"LLM generation failed: {response.error}")
    
    return response.content

async def generate_with_tools(
    prompt: str,
    tools: List[Dict],
    model: str = "gemini-2.5-flash",
    **kwargs
) -> LLMResponse:
    """Generate response with function calling support"""
    handler = get_llm_handler()
    
    request = LLMRequest(
        prompt=prompt,
        model=model,
        tools=tools,
        **kwargs
    )
    
    return await handler.generate(request)

async def generate_stream_with_thinking(request_or_prompt=None, **kwargs):
    """Generate streaming response with thinking and code execution support.

    Backward-compatible: accepts either an LLMRequest or the original keyword args.
    """
    handler = get_llm_handler()
    
    if isinstance(request_or_prompt, LLMRequest):
        request = request_or_prompt
    else:
        # Backward-compat path: build LLMRequest from kwargs
        prompt = request_or_prompt if request_or_prompt is not None else kwargs.get("prompt", "")
        request = LLMRequest(
            prompt=prompt,
            model=kwargs.get("model", "gemini-2.5-flash"),
            system_prompt=kwargs.get("system_prompt"),
            stream=True,
            thinking=kwargs.get("thinking", True),
            thinking_budget=kwargs.get("thinking_budget", 16000),
            messages=kwargs.get("chat_history"),
            tools=kwargs.get("tools"),
            code_execution=kwargs.get("code_execution", False),
            container_id=kwargs.get("container_id"),
        )
    
    async for chunk in handler.generate_stream(request):
        # Normalize chunk format for agent_loop expectations
        if hasattr(chunk, 'type'):
            if chunk.type == "thinking":
                yield {"type": "thinking_chunk", "content": chunk.content}
            elif chunk.type == "thinking_done":
                yield {"type": "plan_thinking_chunk", "content": chunk.content}
            elif chunk.type == "content":
                yield {"type": "content_chunk", "content": chunk.content}
            elif chunk.type == "done":
                yield {"type": "complete"}
            elif chunk.type == "error":
                yield {"type": "error", "content": chunk.error}
            elif chunk.type == "function_call" and getattr(chunk, 'function_call', None):
                yield {"type": "function_call", "function_call": chunk.function_call}
            else:
                # passthrough
                yield chunk
        else:
            yield chunk

async def generate_with_code_execution(
    prompt: str,
    model: str = "gemini-2.5-flash",
    system_prompt: Optional[str] = None,
    container_id: Optional[str] = None,
    files: Optional[List[Dict]] = None,
    **kwargs
) -> LLMResponse:
    """Generate response with code execution support"""
    handler = get_llm_handler()
    
    request = LLMRequest(
        prompt=prompt,
        model=model,
        system_prompt=system_prompt,
        code_execution=True,
        container_id=container_id,
        files=files,
        **kwargs
    )
    
    return await handler.generate(request)

# Convenience function that matches the existing plan generator interface
async def generate_plan_streaming(
    prompt: str,
    model: str = "gemini-2.5-pro",
    system_prompt: Optional[str] = None,
    attachments: Optional[List[Dict]] = None,
    tools: Optional[List[Dict]] = None,
    thinking: bool = True,
    code_execution: bool = True,
    container_id: Optional[str] = None,
    chat_history: Optional[List] = None,
    mcp_servers: Optional[List[Dict]] = None
):
    """Generate plan with streaming thinking and code execution - compatible with existing plan generator"""
    
    from .chat_history_converter import ChatHistoryConverter
    
    # Build full prompt with attachments if provided
    full_prompt = prompt
    if attachments:
        attachment_text = "\n\n# ATTACHED FILES:\n"
        for att in attachments:
            file_name = att.get('fileName', 'unknown')
            content = att.get('processed_content_for_llm', 'Content not available')
            attachment_text += f"## {file_name}\n{content}\n\n"
        full_prompt = f"{prompt}\n{attachment_text}"
    
    # Prepare chat history for the target model
    model_specific_history = None
    if prompt:
        model_specific_history = ChatHistoryConverter.prepare_chat_history_for_model(prompt, model)
    
    # Stream the response
    aggregated_content = ""
    async for chunk in generate_stream_with_thinking(
        prompt=model_specific_history,
        model=model,
        system_prompt=system_prompt,
        thinking=thinking,
        tools=tools,
        code_execution=code_execution,
        container_id=container_id,
    ):
        # Convert to the format expected by the existing plan generator
        if isinstance(chunk, dict):
            ctype = chunk.get("type")
            if ctype in ("thinking_chunk", "plan_thinking_chunk"):
                yield {"type": "plan_thinking_chunk", "content": chunk.get("content", "")}
            elif ctype == "content_chunk":
                content_text = chunk.get("content", "")
                if content_text:
                    aggregated_content += content_text
                    yield {"type": "plan_content_chunk", "content": content_text}
            elif ctype in ("complete", "done"):
                yield {"type": "plan_complete", "content": aggregated_content}
            elif ctype == "error":
                yield {"type": "plan_generation_error", "content": chunk.get("content") or "Generation failed"}
            # ignore other types
        else:
            # Handle LLMStreamChunk objects
            if chunk.type == "thinking":
                yield {"type": "plan_thinking_chunk", "content": chunk.content}
            elif chunk.type == "thinking_done":
                yield {"type": "plan_thinking_chunk", "content": chunk.content}
            elif chunk.type == "content":
                if chunk.content:
                    aggregated_content += chunk.content
                    yield {"type": "plan_content_chunk", "content": chunk.content}
            elif chunk.type == "done":
                yield {"type": "plan_complete", "content": aggregated_content if aggregated_content else chunk.content}
            elif chunk.type == "code_execution":
                yield {"type": "plan_thinking_chunk", "content": f"\n\nExecuting code:\n```python\n{chunk.code_execution.get('code', '')}\n```\n\n"}
            elif chunk.type == "code_result":
                output = chunk.code_result.get('output', '') if chunk.code_result else ''
                if output:
                    yield {"type": "plan_thinking_chunk", "content": f"\n\nCode output:\n{output}\n\n"}
            elif chunk.type == "error":
                yield {"type": "plan_generation_error", "content": chunk.error or "Generation failed"}


# MCP Tool Integration Functions

async def add_mcp_tools_to_request(request: LLMRequest, user_id: str) -> LLMRequest:
    """Add MCP tools to LLM request based on user's connected services"""
    handler = get_llm_handler()
    return await handler._add_mcp_tools_to_request(request, user_id)

async def get_mcp_tools_for_user(user_id: str) -> List[Dict]:
    """Get available MCP tools for a user"""
    if get_mcp_tools_for_llm:
        return await get_mcp_tools_for_llm(user_id)
    return []

async def execute_mcp_tool_call(function_name: str, arguments: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute an MCP tool function call"""
    if execute_mcp_function_call:
        return await execute_mcp_function_call(function_name, arguments, user_id)
    return {"error": "MCP function execution not available"}

def check_is_mcp_function(function_name: str) -> bool:
    """Check if a function name is an MCP function"""
    if is_mcp_function:
        return is_mcp_function(function_name)
    return function_name.startswith("gmail_") or function_name.startswith("outlook_")