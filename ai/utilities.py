from typing import List
from ai.agents import DialogueAgent

def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:
    idx = (step) % len(agents)
    return idx