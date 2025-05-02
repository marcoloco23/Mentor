"""
agent.py
CLI entry point for the Mentor agent.
"""

from src.mentor import Mentor
from boot import memory_manager, llm_client

if __name__ == "__main__":
    mentor = Mentor(memory_manager, llm_client, user_id="u42")
    while True:
        msg = input("You ▸ ")
        print("Mentor ▸", mentor(msg))
