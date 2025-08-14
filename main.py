import logging
import pickle
from typing import Dict

from langchain_core.messages import BaseMessage, SystemMessage
from signalbot import Command, Context, SignalBot

from assistant import MultiAssistant
from config import get_settings
from tool_search import get_search_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)24s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("jacob.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load configuration
settings = get_settings()


class AICommand(Command):
    """Command handler for AI-powered Signal bot responses."""

    def __init__(self, ai: MultiAssistant, prompt: str):
        """Initialize the AI command handler.

        Args:
            ai: MultiAssistant instance for handling AI interactions
            prompt: System prompt for the AI
        """
        super().__init__()
        self.ai = ai
        self.prompt = prompt
        self.history: Dict[str, list[BaseMessage]] = {}

    async def handle(self, c: Context) -> None:
        """Handle incoming Signal messages.

        Args:
            c: Signal context containing message information
        """
        try:
            msg = c.message.text
            id = c.message.source_uuid

            # Skip group messages
            if c.message.group:
                logger.debug(f"Skipping group message from {id}")
                return

            logger.info(f"Received message from {id}: {msg}")

            await c.start_typing()

            # Initialize conversation history if not exists
            if id not in self.history:
                self.history[id] = [SystemMessage(self.prompt)]

            # Get AI response
            resp = self.ai.chat(msg, self.history[id])
            await c.stop_typing()

            # Send response and log
            await c.send(resp)
            logger.info(f"Sent response to {id}")

        except Exception as e:
            logger.error(f"Error handling message from {id}: {e}", exc_info=True)
            await c.send("I'm sorry, I encountered an error processing your request.")

    def load(self) -> None:
        """Load conversation history from persistent storage."""
        try:
            with open("history.pkl", "rb") as f:
                self.history = pickle.load(f)
            logger.info("Loaded conversation history")
        except FileNotFoundError:
            logger.warning("History file not found, starting with empty history")
        except Exception as e:
            logger.error(f"Error loading history: {e}", exc_info=True)

    def save(self) -> None:
        """Save conversation history to persistent storage."""
        try:
            with open("history.pkl", "wb") as f:
                pickle.dump(self.history, f)
            logger.info("Saved conversation history")
        except Exception as e:
            logger.error(f"Error saving history: {e}", exc_info=True)


def main() -> None:
    """Main entry point for the Signal bot application."""
    try:
        # Initialize AI assistant
        logger.info("Initializing AI assistant...")
        ai = MultiAssistant(settings.OPENAI_API_BASE, settings.OPENAI_API_KEY)
        # ai.add_tool(get_time)
        ai.add_tool(get_search_results)

        # Initialize Signal bot
        logger.info("Initializing Signal bot...")
        bot = SignalBot(
            {
                "signal_service": settings.SIGNAL_SERVICE,
                "phone_number": settings.PHONE_NUMBER,
                "storage": {"type": "sqlite", "sqlite_db": "signal.db"},
            }
        )

        # Initialize and register AI command handler
        logger.info("Initializing AI command handler...")
        aicommand = AICommand(ai, settings.SYSTEM_PROMPT)
        aicommand.load()
        bot.register(aicommand)

        # Start the bot
        logger.info("Starting Signal bot...")
        bot.start()

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Ensure history is saved on shutdown
        if "aicommand" in locals():
            aicommand.save()
            logger.info("Saved conversation history on shutdown")


if __name__ == "__main__":
    main()
