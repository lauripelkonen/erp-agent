"""
Product Match Reviewer - Post-processing review of product matches for consistency.

This module uses LLM tool calling to review all matched products collectively
and re-evaluate specific matches as needed using sub-agent calls.
"""

import logging
import os
from typing import List, Dict, Optional
from google import genai
from google.genai import types


class ProductMatchReviewer:
    """
    Reviews and validates product matches for consistency using LLM tool calling.
    
    The LLM can call re_evaluate_match tools to re-process specific matches
    with custom instructions passed to the sub-agent.
    """
    
    def __init__(self, parent_matcher, logger: Optional[logging.Logger] = None):
        """
        Initialize the reviewer with reference to parent ProductMatcher.
        
        Args:
            parent_matcher: Instance of ProductMatcher for accessing methods and data
            logger: Optional logger instance
        """
        self.parent_matcher = parent_matcher
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuration for Gemini AI
        self.model_name = "gemini-1.5-flash-8b"
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        
        # Define the tool schema for LLM to call
        self.re_evaluate_tool = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="re_evaluate_match",
                    description="Re-evaluate a specific product match using a sub-agent with custom instructions",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "original_unclear_term": types.Schema(
                                type=types.Type.STRING,
                                description="The original unclear term that was matched"
                            ),
                            "current_product_code": types.Schema(
                                type=types.Type.STRING,
                                description="Current matched product code"
                            ),
                            "current_product_name": types.Schema(
                                type=types.Type.STRING,
                                description="Current matched product name"
                            ),
                            "instructions_for_sub_agent": types.Schema(
                                type=types.Type.STRING,
                                description="Specific instructions for the sub-agent on what to look for or how to approach the re-evaluation"
                            )
                        },
                        required=["original_unclear_term", "current_product_code", "current_product_name", "instructions_for_sub_agent"]
                    )
                )
            ]
        )
        
    async def review_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Review all matches collectively using LLM tool calling and re-evaluate as needed.
        
        Args:
            matches: List of match dictionaries from ProductMatcher.match_terms()
            
        Returns:
            List of reviewed and potentially updated matches
        """
        if not matches:
            return matches
            
        self.logger.info(f"🔍 Starting LLM-based review of {len(matches)} matches")
        
        # Prepare matches summary for LLM
        matches_summary = self._format_matches_for_review(matches)
        
        # System prompt for the reviewing LLM
        system_prompt = """You are a product matching quality assurance agent. 

Review the following product matches for consistency and accuracy. Look for:
1. Related products (same base product in different sizes/variants) that have inconsistent naming patterns
2. Products that seem semantically different but got matched to the same product code  
3. Matches that don't make logical sense when viewed together

For any problematic matches, call the re_evaluate_match tool with:
- The original unclear term
- Current match details  
- Specific instructions for the sub-agent on what to look for

Example issues to watch for:
- "muhviputki 110" and "muhviputki kulma 30" matched to completely different product families
- Multiple very different terms matched to the same product code inappropriately
- Size variants that should follow consistent naming but don't

Only call re_evaluate_match if you identify genuine consistency problems."""

        user_prompt = f"""Review these product matches for consistency:

{matches_summary}

Are there any consistency issues that need re-evaluation?"""

        try:
            # Make LLM call with tool calling capability
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=f"{system_prompt}\n\n{user_prompt}")]
                    )
                ],
                tools=[self.re_evaluate_tool],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfig.Mode.AUTO
                    )
                )
            )
            
            # Process the response and handle any tool calls
            updated_matches = await self._process_review_response(response, matches)
            
            self.logger.info(f"✅ Match review completed")
            return updated_matches
            
        except Exception as e:
            self.logger.error(f"❌ Error during match review: {e}")
            return matches  # Return original matches if review fails
            
    def _format_matches_for_review(self, matches: List[Dict]) -> str:
        """
        Format matches into a readable summary for the LLM.
        """
        lines = []
        for i, match in enumerate(matches):
            lines.append(
                f"{i+1}. '{match['unclear_term']}' -> "
                f"{match['matched_product_code']} ({match['matched_product_name']})"
            )
        return "\n".join(lines)
        
    async def _process_review_response(self, response, original_matches: List[Dict]) -> List[Dict]:
        """
        Process the LLM response and handle any re_evaluate_match tool calls.
        """
        updated_matches = original_matches.copy()
        
        if not response.candidates:
            return updated_matches
            
        candidate = response.candidates[0]
        
        # Check if there are function calls
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                
                if function_call.name == "re_evaluate_match":
                    # Extract parameters
                    args = function_call.args
                    unclear_term = args.get("original_unclear_term", "")
                    current_code = args.get("current_product_code", "")
                    current_name = args.get("current_product_name", "")
                    instructions = args.get("instructions_for_sub_agent", "")
                    
                    self.logger.info(f"🔄 LLM requested re-evaluation of '{unclear_term}' with instructions: {instructions}")
                    
                    # Find the match to update
                    match_idx = self._find_match_index(updated_matches, unclear_term, current_code)
                    
                    if match_idx is not None:
                        # Re-evaluate using sub-agent
                        new_match = await self._execute_re_evaluation(
                            updated_matches[match_idx], 
                            instructions, 
                            updated_matches
                        )
                        
                        if new_match:
                            self.logger.info(f"📝 Updated match for '{unclear_term}': "
                                           f"{current_code} -> {new_match['matched_product_code']}")
                            updated_matches[match_idx] = new_match
                        else:
                            self.logger.warning(f"⚠️ Re-evaluation failed for '{unclear_term}', keeping original")
                    else:
                        self.logger.warning(f"⚠️ Could not find match for re-evaluation: '{unclear_term}' with code {current_code}")
                        
        return updated_matches
        
    def _find_match_index(self, matches: List[Dict], unclear_term: str, product_code: str) -> Optional[int]:
        """
        Find the index of a match by unclear term and product code.
        """
        for i, match in enumerate(matches):
            if (match['unclear_term'] == unclear_term and 
                match['matched_product_code'] == product_code):
                return i
        return None
        
    async def _execute_re_evaluation(self, original_match: Dict, instructions: str, 
                                   all_matches: List[Dict]) -> Optional[Dict]:
        """
        Execute re-evaluation of a match using the parent matcher's agentic search
        with custom instructions from the reviewing LLM.
        """
        unclear_term = original_match['unclear_term']
        
        # Build context from other matches
        context_info = self._build_context_from_matches(all_matches, exclude_term=unclear_term)
        
        # Enhanced usage context with LLM's instructions and other matches context
        enhanced_context = f"""
{instructions}

CONTEXT FROM OTHER MATCHES:
{context_info}

Original match being re-evaluated:
- Term: {unclear_term}
- Current match: {original_match['matched_product_code']} - {original_match['matched_product_name']}

Please find the most appropriate product match considering the instructions above and consistency with other matches.
"""
        
        try:
            # Use parent matcher's agentic search with enhanced context
            new_candidates_df = await self.parent_matcher._agentic_iterative_match(
                unclear_term, 
                usage_context=enhanced_context
            )
            
            if new_candidates_df is None or new_candidates_df.empty:
                self.logger.warning(f"❌ Re-evaluation found no candidates for '{unclear_term}'")
                return None
                
            # Handle results based on candidate count
            if len(new_candidates_df) == 1:
                # Single candidate - validate and use
                row = new_candidates_df.iloc[0]
                product_code = str(row["Tuotekoodi"]).strip()
                product_name = str(row["Tuotenimi"]).strip()
                
                # Validate the new match
                quality_check = await self.parent_matcher._validate_match_quality(
                    unclear_term, product_code, enhanced_context
                )
                
                if quality_check.get('is_valid', True):
                    new_match = original_match.copy()
                    new_match.update({
                        'matched_product_code': product_code,
                        'matched_product_name': product_name
                    })
                    
                    self.logger.info(f"✅ Re-evaluation successful: {product_code} - {product_name}")
                    return new_match
                else:
                    self.logger.warning(f"⚠️ Re-evaluated match failed quality check: {quality_check.get('reason', 'Unknown')}")
                    
            else:
                # Multiple candidates - use Gemini selection
                selected_row = self.parent_matcher._gemini_select_best(
                    unclear_term, new_candidates_df, enhanced_context
                )
                if selected_row is not None:
                    row = selected_row.iloc[0] 
                    product_code = str(row["Tuotekoodi"]).strip()
                    product_name = str(row["Tuotenimi"]).strip()
                    
                    new_match = original_match.copy()
                    new_match.update({
                        'matched_product_code': product_code,
                        'matched_product_name': product_name
                    })
                    
                    self.logger.info(f"✅ Re-evaluation with selection successful: {product_code} - {product_name}")
                    return new_match
                    
        except Exception as e:
            self.logger.error(f"❌ Error during re-evaluation of '{unclear_term}': {e}")
            
        return None
        
    def _build_context_from_matches(self, matches: List[Dict], exclude_term: str) -> str:
        """
        Build context string from other matches to help with consistency.
        """
        context_lines = []
        for match in matches:
            if match['unclear_term'] != exclude_term:
                context_lines.append(
                    f"- '{match['unclear_term']}' -> {match['matched_product_code']} ({match['matched_product_name']})"
                )
                
        return "\n".join(context_lines[:10])  # Limit to 10 examples to avoid token limits