"""
OpenAI LLM Client for UVM Generation.
Handles all interactions with the OpenAI API.
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from config import OpenAIConfig

console = Console()


@dataclass
class LLMResponse:
    """Structured response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class UVMGeneratorLLM:
    """LLM client specialized for UVM code generation."""
    
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            organization=config.org_id
        )
        self.conversation_history: List[Dict[str, str]] = []
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for UVM generation."""
        return """You are an expert SystemVerilog and UVM (Universal Verification Methodology) engineer.
Your task is to generate high-quality, synthesizable, and lint-clean UVM testbench code.

Follow these guidelines:
1. Use proper UVM methodology and coding standards
2. Include all necessary `uvm_component_utils` and `uvm_object_utils` macros
3. Use proper phase methods (build_phase, connect_phase, run_phase, etc.)
4. Generate parameterized code where appropriate
5. Include meaningful comments explaining the code
6. Follow the coding style of the provided example files exactly
7. Ensure all class names, file names, and references are consistent
8. Use proper SystemVerilog syntax and UVM base classes

When generating code:
- Output ONLY the SystemVerilog code
- Do NOT include markdown code fences or explanations
- Start directly with the code (comments or class definition)
- End with the closing endclass or endmodule statement"""

    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        examples: Optional[List[str]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate UVM code using the LLM.
        
        Args:
            prompt: The main generation prompt
            context: Additional context (block yaml, vplan, etc.)
            examples: Example files for few-shot learning
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLMResponse with generated code
        """
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        
        # Add context if provided
        if context:
            messages.append({
                "role": "user",
                "content": f"Here is the context for generation:\n\n{context}"
            })
            messages.append({
                "role": "assistant", 
                "content": "I understand the context. I'm ready to generate UVM code based on this information."
            })
        
        # Add examples for few-shot learning
        if examples:
            example_text = "\n\n---\n\n".join(examples)
            messages.append({
                "role": "user",
                "content": f"Here are example files to follow for style and structure:\n\n{example_text}"
            })
            messages.append({
                "role": "assistant",
                "content": "I've analyzed the example files. I will follow their coding style, structure, and conventions."
            })
        
        # Add the main prompt
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            console.print(f"[red]Error calling OpenAI API: {e}[/red]")
            raise

    def generate_with_retry(
        self,
        prompt: str,
        context: Optional[str] = None,
        examples: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> LLMResponse:
        """Generate with automatic retry on failure."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.generate(prompt, context, examples)
            except Exception as e:
                last_error = e
                console.print(f"[yellow]Attempt {attempt + 1} failed, retrying...[/yellow]")
        raise last_error


def extract_code_from_response(response: str) -> str:
    """
    Extract clean code from LLM response.
    Removes markdown code fences if present.
    """
    lines = response.strip().split('\n')
    
    # Remove markdown code fences if present
    if lines[0].startswith('```'):
        lines = lines[1:]
    if lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    
    return '\n'.join(lines)
