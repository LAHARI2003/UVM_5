"""
LLM Client for UVM code generation
Supports Anthropic (Claude) and OpenAI APIs
"""

import os
import re
from typing import Dict, Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        pass
    
    def extract_code(self, response: str) -> str:
        """Extract SystemVerilog code from LLM response"""
        code = response
        
        # Remove markdown code blocks
        if "```systemverilog" in code:
            code = code.split("```systemverilog")[1].split("```")[0]
        elif "```sv" in code:
            code = code.split("```sv")[1].split("```")[0]
        elif "```verilog" in code:
            code = code.split("```verilog")[1].split("```")[0]
        elif "```" in code:
            # Generic code block
            parts = code.split("```")
            if len(parts) >= 2:
                code = parts[1]
                # Remove language identifier if present on first line
                lines = code.split('\n')
                if lines and lines[0].strip() in ['systemverilog', 'sv', 'verilog', '']:
                    code = '\n'.join(lines[1:])
        
        return code.strip()


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
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_response = response.content[0].text
        return self.extract_code(raw_response)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT API client"""
    
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
    
    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        # Check if model is a newer version that uses max_completion_tokens
        is_new_model = any(x in self.model.lower() for x in ['gpt-5', 'gpt-4.5', 'o1', 'o3'])
        
        if is_new_model:
            # Newer models use max_completion_tokens
            response = self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "You are a UVM verification expert. Generate clean, compilable SystemVerilog code."},
                    {"role": "user", "content": prompt}
                ]
            )
        else:
            # Older models use max_tokens
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "You are a UVM verification expert. Generate clean, compilable SystemVerilog code."},
                    {"role": "user", "content": prompt}
                ]
            )
        
        raw_response = response.choices[0].message.content
        return self.extract_code(raw_response)


class LLMClient:
    """Factory class for LLM clients"""
    
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
    
    def generate(self, prompt: str, max_tokens: int = 8192) -> str:
        """Generate code using the configured LLM"""
        return self.client.generate(prompt, max_tokens)
    
    def generate_with_retry(self, prompt: str, max_tokens: int = 8192, retries: int = 3) -> str:
        """Generate with retry on failure"""
        last_error = None
        for attempt in range(retries):
            try:
                return self.generate(prompt, max_tokens)
            except Exception as e:
                last_error = e
                print(f"  Attempt {attempt + 1} failed: {e}")
        raise last_error
