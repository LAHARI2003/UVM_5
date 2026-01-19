"""
UVM Generator V2 - Prompts Module

All prompts are now dynamic and derived from input YAML files,
not hardcoded to a specific IP.
"""

from .ip_infra_prompts import (
    get_env_prompt,
    get_virtual_sequencer_prompt,
    get_interface_prompt,
    get_package_prompt,
    get_scoreboard_prompt
)

from .test_case_prompts import (
    get_test_prompt,
    get_vseq_prompt
)

__all__ = [
    'get_env_prompt',
    'get_virtual_sequencer_prompt',
    'get_interface_prompt',
    'get_package_prompt',
    'get_scoreboard_prompt',
    'get_test_prompt',
    'get_vseq_prompt'
]
