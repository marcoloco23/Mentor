# Mentor Backend

A powerful AI coaching system that leverages long-term memory for personalized mentorship.

## Architecture Overview

The Mentor backend is built around a clean, modular architecture with clear separation of concerns:

```
src/
├── agent.py        # CLI interface entry point
├── boot.py         # Application bootstrapping and dependency wiring
├── config.py       # Centralized configuration parameters
├── export_schema.py # Memory export schemas
├── llm.py          # LLM client for chat completions
├── memory.py       # Memory management and retrieval
├── mentor.py       # Core Mentor agent implementation
└── utils.py        # Utility functions and helpers
```

## Core Components

### 1. Mentor Agent (`mentor.py`)

The central component that orchestrates the interaction between memory retrieval and LLM generation. It:
- Retrieves relevant memories based on the user's message
- Formats conversation context
- Passes everything to the LLM for response generation
- Stores conversations in memory

### 2. Memory Management (`memory.py`)

Handles all aspects of memory:
- Retrieval of semantically relevant memories
- Storage of conversations
- Thread history management
- Recent conversation formatting

### 3. LLM Client (`llm.py`)

Responsible for:
- Formatting the system prompt with the appropriate context
- Generating responses via the OpenAI API
- Handling streaming responses

### 4. Configuration (`config.py`)

Centralizes all configuration parameters:
- LLM settings
- Memory parameters
- Agent defaults
- File paths

## Usage

The Mentor system can be accessed through:

```python
from src.mentor import Mentor
from src.boot import memory_manager, llm_client

# Initialize the Mentor agent
mentor = Mentor(memory_manager, llm_client, user_id="your_user_id")

# Get a response
response = mentor("What should I focus on this week?")

# Or stream a response
for token in mentor.stream_reply("What are my priorities?"):
    print(token, end="", flush=True)
```

## Design Principles

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Configuration Centralization**: All parameters are defined in one place
3. **Clean Interface**: The Mentor class provides a simple, intuitive API
4. **Robust Memory Management**: Efficient retrieval and storage of memories
5. **Lightweight Dependencies**: Minimal external dependencies

## Development

To contribute to the Mentor backend:

1. Ensure you have the required environment variables:
   - `MEM0_API_KEY`
   - `OPENAI_API_KEY`

2. Follow the existing architecture patterns
3. Add appropriate logging for debugging and monitoring
4. Maintain comprehensive docstrings
5. Respect the existing configuration system 