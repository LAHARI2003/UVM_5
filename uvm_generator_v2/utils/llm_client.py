"""
LLM Client for UVM code generation - V2 (Improved)

Key Improvements:
- Exponential backoff for rate limiting
- Better error handling and logging
- Support for more models
- Token counting awareness
- Response validation
"""

import os
import re
import time
import logging
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM errors"""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded"""
    pass


class TokenLimitError(LLMError):
    """Token limit exceeded"""
    pass


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        pass
    
    def extract_code(self, response: str) -> str:
        """Extract SystemVerilog code from LLM response"""
        if not response:
            return ""
        
        code = response
        
        # Remove markdown code blocks - handle multiple formats
        code_block_patterns = [
            (r'```systemverilog\s*\n(.*?)```', 1),
            (r'```sv\s*\n(.*?)```', 1),
            (r'```verilog\s*\n(.*?)```', 1),
            (r'```\s*\n(.*?)```', 1),
        ]
        
        for pattern, group in code_block_patterns:
            match = re.search(pattern, code, re.DOTALL)
            if match:
                code = match.group(group)
                break
        
        # Remove any remaining markdown artifacts
        code = re.sub(r'^```\w*\s*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
        
        # Remove common LLM artifacts
        code = re.sub(r'^Here\'s the.*?:\s*$', '', code, flags=re.MULTILINE | re.IGNORECASE)
        code = re.sub(r'^Here is the.*?:\s*$', '', code, flags=re.MULTILINE | re.IGNORECASE)
        code = re.sub(r'^\s*Note:.*$', '', code, flags=re.MULTILINE | re.IGNORECASE)
        
        return code.strip()
    
    def validate_systemverilog(self, code: str) -> List[str]:
        """Basic validation of SystemVerilog code"""
        issues = []
        
        if not code:
            issues.append("Empty code generated")
            return issues
        
        # Check for common required elements
        if 'class' not in code and 'interface' not in code and 'module' not in code:
            issues.append("No class, interface, or module declaration found")
        
        # Check balanced blocks
        opens = code.count('begin')
        closes = code.count('end')
        # Note: 'end' can also appear in 'endclass', 'endfunction', etc.
        
        # Check for unclosed class
        class_count = len(re.findall(r'\bclass\b', code))
        endclass_count = len(re.findall(r'\bendclass\b', code))
        if class_count != endclass_count:
            issues.append(f"Unbalanced class/endclass: {class_count} class vs {endclass_count} endclass")
        
        # Check for unclosed function/task
        func_count = len(re.findall(r'\bfunction\b', code))
        endfunc_count = len(re.findall(r'\bendfunction\b', code))
        if func_count != endfunc_count:
            issues.append(f"Unbalanced function/endfunction: {func_count} vs {endfunc_count}")
        
        task_count = len(re.findall(r'\btask\b', code))
        endtask_count = len(re.findall(r'\bendtask\b', code))
        if task_count != endtask_count:
            issues.append(f"Unbalanced task/endtask: {task_count} vs {endtask_count}")
        
        return issues


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY env var or pass api_key.")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            raw_response = response.content[0].text
            return self.extract_code(raw_response)
            
        except Exception as e:
            error_str = str(e).lower()
            if 'rate' in error_str or '429' in error_str:
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif 'token' in error_str or 'context' in error_str:
                raise TokenLimitError(f"Token limit exceeded: {e}")
            raise LLMError(f"Anthropic API error: {e}")


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT API client"""
    
    # Models that use max_completion_tokens instead of max_tokens
    NEW_MODELS = ['gpt-5', 'gpt-4.5', 'gpt-4.1', 'o1', 'o3', 'gpt-4o']
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env var or pass api_key.")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def _is_new_model(self) -> bool:
        """Check if model uses new API parameters"""
        model_lower = self.model.lower()
        return any(x in model_lower for x in self.NEW_MODELS)
    
    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        try:
            messages = [
                {"role": "system", "content": "You are a UVM verification expert. Generate clean, compilable SystemVerilog code. Output ONLY the code, no explanations."},
                {"role": "user", "content": prompt}
            ]
            
            if self._is_new_model():
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_completion_tokens=max_tokens,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages
                )
            
            raw_response = response.choices[0].message.content
            return self.extract_code(raw_response)
            
        except Exception as e:
            error_str = str(e).lower()
            if 'rate' in error_str or '429' in str(e):
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif 'token' in error_str or 'context' in error_str or 'length' in error_str:
                raise TokenLimitError(f"Token limit exceeded: {e}")
            raise LLMError(f"OpenAI API error: {e}")


class LLMClient:
    """
    Factory class for LLM clients with retry logic
    
    Usage:
        client = LLMClient(provider="anthropic", api_key="...")
        code = client.generate_with_retry(prompt)
    """
    
    def __init__(self, provider: str = "anthropic", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider.lower()
        
        if self.provider == "anthropic":
            model = model or "claude-sonnet-4-20250514"
            self.client = AnthropicClient(api_key=api_key, model=model)
        elif self.provider == "openai":
            model = model or "gpt-4-turbo"
            self.client = OpenAIClient(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai'.")
        
        self.model = model
    
    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        """Generate code using the configured LLM"""
        return self.client.generate(prompt, max_tokens)
    
    def generate_with_retry(
        self, 
        prompt: str, 
        max_tokens: int = 8192, 
        retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        validate: bool = True
    ) -> str:
        """
        Generate with exponential backoff retry on failure
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            retries: Number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            validate: Whether to validate generated code
        """
        last_error = None
        delay = base_delay
        
        for attempt in range(retries):
            try:
                code = self.generate(prompt, max_tokens)
                
                # Optional validation
                if validate:
                    issues = self.client.validate_systemverilog(code)
                    if issues:
                        logger.warning(f"Code validation warnings: {issues}")
                
                return code
                
            except RateLimitError as e:
                last_error = e
                wait_time = min(delay * (2 ** attempt), max_delay)
                logger.warning(f"Rate limited. Waiting {wait_time:.1f}s before retry {attempt + 1}/{retries}")
                time.sleep(wait_time)
                
            except TokenLimitError as e:
                # Don't retry token limit errors - need to reduce prompt size
                logger.error(f"Token limit exceeded: {e}")
                raise
                
            except LLMError as e:
                last_error = e
                wait_time = min(delay * (2 ** attempt), max_delay)
                logger.warning(f"LLM error: {e}. Retrying in {wait_time:.1f}s ({attempt + 1}/{retries})")
                time.sleep(wait_time)
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        
        raise LLMError(f"Failed after {retries} attempts. Last error: {last_error}")
