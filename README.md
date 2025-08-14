# J.A.C.O.B. - Just Another Cool Online Bot

J.A.C.O.B. is a production-grade Signal chat bot powered by OpenAI's language models through LangChain. This bot provides intelligent, context-aware responses to user messages while maintaining conversation history.

## Features

- **AI-Powered Responses**: Leverages OpenAI's language models for natural language understanding and generation
- **Tool Integration**: Supports tool integration for enhanced functionality (e.g., time queries)
- **Conversation History**: Maintains context across messages for coherent conversations
- **Signal Integration**: Seamlessly integrates with Signal messaging platform
- **Production-Ready**: Includes proper logging, error handling, and configuration management

## Requirements

- Python 3.10+
- Signal account with API access
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/jacob.git
   cd jacob
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. Create a `.env` file with your configuration:
   ```ini
   OPENAI_API_KEY=your_openai_api_key
   SIGNAL_SERVICE=your_signal_service_url
   PHONE_NUMBER=your_signal_phone_number
   ```

## Configuration

The application uses a configuration system with sensible defaults. You can override settings via environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_API_BASE`: OpenAI API base URL (default: "https://api.openai.com/v1")
- `SIGNAL_SERVICE`: Signal service URL (required)
- `PHONE_NUMBER`: Signal phone number (required)
- `SYSTEM_PROMPT`: System prompt for the AI (default: "You are a Signal chat bot named J.A.C.O.B...")
- `DATABASE_URL`: Database connection string (default: "sqlite:///signal.db")

## Usage

1. Start the bot:
   ```bash
   python main.py
   ```

2. The bot will connect to Signal and start processing messages

## Development

### Project Structure

```
jacob/
├── assistant/          # AI assistant implementation
│   ├── __init__.py
│   ├── assistant.py    # Core assistant classes
│   └── tool_time.py    # Time query tool
├── comm_signal/        # Signal integration
│   ├── __init__.py
│   └── bot.py          # Signal bot wrapper
├── config.py           # Configuration management
├── main.py             # Main application entry point
├── pyproject.toml      # Project metadata and dependencies
├── README.md           # Project documentation
└── .env                # Environment variables (not included in git)
```

### Running Tests

Tests can be run using pytest:
```bash
pytest tests/
```

### Adding New Tools

To add a new tool to the assistant:

1. Create a new tool function in `assistant/tool_*.py`
2. Import and register the tool in `main.py`
3. Update the assistant classes if needed

## Logging

The application uses Python's logging module with both file and console handlers. Logs are stored in `jacob.log` and also output to the console.

## Error Handling

The application includes comprehensive error handling with proper exception management and logging. All critical errors are logged with stack traces for debugging.

## Security

- API keys and sensitive configuration are managed via environment variables
- Database credentials are properly handled through configuration
- Input validation is performed on all user inputs

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
