# Ted - Your Lifelong AI Companion

Ted is a lifelong AI companion and confidant, designed to be your personal assistant that remembers, learns, and grows with you over time. Think Ted from the movie: loyal, witty, a bit cheeky, but always there when you need him.

## Features

### 🧠 Long-term Memory
- **Persistent Memory**: Ted remembers your conversations, preferences, and important details using Mem0
- **Semantic Search**: Retrieves relevant memories based on context, not just keywords
- **Time-aware Recall**: Memories are organized by date and weighted by recency

### ⏰ Time-Aware Intelligence
- **Current Time Context**: Ted knows what time it is and can respond appropriately
- **Smart Message Filtering**: Automatically handles conversation breaks (like overnight gaps)
- **Conversation Resumption**: Detects when you're resuming after a break and responds naturally
- **Situational Awareness**: Understands morning vs. evening, weekdays vs. weekends

### 💬 Natural Conversation
- **Streaming Responses**: Real-time chat with immediate feedback
- **Personality**: Playful, loyal, and irreverent while being genuinely caring
- **Context-Aware**: Uses memories and time context to provide relevant responses

### 🔧 Technical Features
- **REST API**: FastAPI-based service for easy integration
- **Multiple Interfaces**: CLI, web API, and streaming support
- **Robust Error Handling**: Graceful fallbacks and comprehensive logging
- **Modular Architecture**: Clean separation of concerns for maintainability

## Time-Aware Features

### Smart Message Filtering
Ted intelligently filters conversation history based on time gaps:

- **Recent Conversations**: Includes up to 20 recent messages when conversation is active
- **Time Breaks**: Detects gaps of 4+ hours and starts fresh context
- **Stale Conversations**: Limits to 3 messages when resuming after long breaks (8+ hours)
- **Overnight Handling**: Automatically handles sleep/work breaks without including stale context

### Time Context Integration
Ted receives rich time context including:

- Current date and time
- Time of day (morning, afternoon, evening, night)
- Day of week and season
- Special time indicators (early morning, late night, weekend)

### Configuration Options
```python
# Time-based filtering settings
MESSAGE_FRESHNESS_HOURS = 8       # Messages older than this create a "break"
MAX_STALE_MESSAGES = 3            # Max messages when conversation is stale
TIME_BREAK_THRESHOLD_HOURS = 4    # Hours gap that indicates a break
```

## Architecture

### Core Components

1. **Ted Agent** (`ted.py`): Main agent orchestrating memory and LLM interactions
2. **Memory Manager** (`memory.py`): Handles long-term memory storage and retrieval with time-aware filtering
3. **LLM Client** (`llm.py`): OpenAI integration with time-aware prompt formatting
4. **Utilities** (`utils.py`): Time context generation and message filtering logic

### Time-Aware Flow

1. **Message Reception**: User sends a message
2. **Time Context**: Generate current time context and situational awareness
3. **Memory Retrieval**: Fetch relevant memories using semantic search
4. **Message Filtering**: Apply smart time-based filtering to conversation history
5. **Conversation Detection**: Check if this is a resumption after a break
6. **Prompt Formation**: Combine time context, memories, and filtered messages
7. **Response Generation**: Generate contextually-aware response
8. **Memory Storage**: Store the conversation with timestamp

## API Examples

### Basic Chat
```python
from src.ted import Ted
from src.boot import memory_manager, llm_client

ted = Ted(memory_manager, llm_client, user_id="alice")
response = ted("Good morning! How's the weather?")
```

### Streaming Chat
```python
for token in ted.stream_reply("Tell me about my day"):
    print(token, end="", flush=True)
```

### Time Context
```python
from src.utils import get_time_context
context = get_time_context()
# "It's morning on Monday, December 16, 2024 at 08:30 (winter)"
```

### Message Filtering
```python
from src.utils import filter_messages_by_time_gaps
filtered_messages = filter_messages_by_time_gaps(conversation_history)
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
MEM0_API_KEY=your_mem0_key
```

### Time Zone Configuration
```python
# config.py
USER_TZ = ZoneInfo("Europe/Berlin")  # Set your timezone
```

## Examples of Time-Aware Behavior

### Morning Greeting
```
User: "Hey"
Ted: "Good morning! How are you feeling this Monday morning? Ready to tackle the week?"
```

### Evening Check-in
```
User: "How's it going?"
Ted: "Hey! How was your day? It's getting late - are you winding down for the evening?"
```

### Conversation Resumption
```
User: "Hi" (after 10 hours)
Ted: "Good morning! Welcome back - I see it's been a while since we last chatted. How did you sleep?"
```

### Weekend Context
```
User: "What should I do?"
Ted: "It's Saturday morning! Perfect time to relax or tackle those weekend projects. What are you in the mood for?"
```

## Development

### Running Tests
```bash
python test_time_features.py  # Test time-aware features
python -m pytest tests/       # Run full test suite
```

### Adding New Time Features
1. Add configuration to `config.py`
2. Implement logic in `utils.py`
3. Update prompt template in `prompts.py`
4. Test with `test_time_features.py`

## Memory Management

Ted uses a hybrid approach:
- **Semantic Memory**: Long-term memories stored in Mem0 with semantic search
- **Episodic Memory**: Recent conversation history with time-aware filtering
- **Time-based Filtering**: Smart context selection based on conversation gaps

The system automatically handles:
- Conversation continuity during active chats
- Natural breaks in conversation (meals, work, sleep)
- Long-term memory formation and retrieval
- Context switching between different conversation sessions

This creates a natural, human-like conversation experience that respects time boundaries while maintaining conversational depth and continuity. 