"""
Command-line interface entry point for the Ted agent.

This script initializes the Ted agent and provides a simple REPL for user interaction via the command line.
Run this file directly to start a CLI session with Ted.
"""

from src.ted import Ted
from src.boot import memory_manager, llm_client
from src.config import DEFAULT_USER_ID

if __name__ == "__main__":
    """
    Entry point for the Ted CLI REPL.
    Continuously prompts the user for input and prints Ted's response.
    """
    ted = Ted(memory_manager, llm_client, user_id=DEFAULT_USER_ID)
    print(f"Ted initialized. Type 'exit' or 'quit' to end the session.")

    while True:
        msg = input("You ▸ ")
        if msg.lower() in ("exit", "quit"):
            print("Ending session. Goodbye!")
            break

        print("Ted ▸", ted(msg))
