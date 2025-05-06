"""
Command-line interface entry point for the Mentor agent.

This script initializes the Mentor agent and provides a simple REPL for user interaction via the command line.
Run this file directly to start a CLI session with the Mentor agent.
"""

from src.mentor import Mentor
from src.boot import memory_manager, llm_client
from src.config import DEFAULT_USER_ID

if __name__ == "__main__":
    """
    Entry point for the Mentor CLI REPL.
    Continuously prompts the user for input and prints the Mentor's response.
    """
    mentor = Mentor(memory_manager, llm_client, user_id=DEFAULT_USER_ID)
    print(f"Mentor initialized. Type 'exit' or 'quit' to end the session.")

    while True:
        msg = input("You ▸ ")
        if msg.lower() in ("exit", "quit"):
            print("Ending session. Goodbye!")
            break

        print("Mentor ▸", mentor(msg))
