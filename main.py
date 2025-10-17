import logging
import pickle
import json
from typing import Any, Dict

import meshtastic
import meshtastic.serial_interface
from langchain_core.messages import BaseMessage, SystemMessage
from pubsub import pub
from signalbot import Command, Context, SignalBot, Message

from assistant import MultiAssistant
from config import get_settings
from tool_search import get_search_results

# Configure logging
_log_formatter = logging.Formatter("%(asctime)s - %(name)24s - %(levelname)s - %(message)s")
_fh = logging.FileHandler("jacob.log")
_fh.setFormatter(_log_formatter)
_sh = logging.StreamHandler()
_sh.setFormatter(_log_formatter)

def getLogger(name: str) -> logging.Logger:
    l = logging.getLogger(name)
    if not l.handlers:
        l.setLevel(logging.INFO)
        l.addHandler(_fh)
        l.addHandler(_sh)
        l.propagate = False
    return l


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
        self.logger = getLogger("SignalCommand")

    def getGroupName(self, raw: Any) -> str:
        env = raw["envelope"]

        if "dataMessage" in env and env["dataMessage"]:
            x = env["dataMessage"]
            if "groupInfo" in x and x["groupInfo"]:
                x = x["groupInfo"]
                if "groupName" in x and x["groupName"]:
                    return x["groupName"]
        return "[UNKNOWN GROUP NAME]"

    def getName(self, raw: Any) -> str:
        env = raw["envelope"]

        if "sourceName" in env and env["sourceName"]:
            return env["sourceName"]

        if "sourceNumber" in env and env["sourceNumber"]:
            return env["sourceNumber"]

        return env["sourceUuid"]

    async def handleDirect(self, c: Context) -> None:
        msg = c.message.text
        id = c.message.source_uuid
        raw = json.loads(c.message.raw_message)

        name = self.getName(raw)
        self.logger.info(f"From \'{name}\': {msg}")

        await c.start_typing()

        # Initialize conversation history if not exists
        if id not in self.history:
            self.history[id] = [SystemMessage(self.prompt)]

        match msg.strip().split():
            case ["!clear", *_]:
                prompt = self.history[id][0].content
                self.history[id] = [SystemMessage(prompt)]
                await c.send("Context cleared!")
                return
            case ["!info", *_] | ["!help", *_]:
                await c.send("<Insert help here>")
                return
            case ["!system"]:
                prompt = self.history[id][0].content
                await c.send(f"The current system prompt is as follows:\n\n{prompt}")
                return
            case ["!system", *prompt]:
                self.history[id] = [SystemMessage(self.prompt + "\n\n" + ' '.join(prompt))]
                await c.send("System prompt set and context cleared!")
                return

        # Get AI response
        resp = self.ai.chat(msg, self.history[id])
        await c.stop_typing()

        # Send response and log
        await c.send(resp)
        if len(resp) > 10:
            resp = resp[:80] + "..."
        self.logger.info(f"To   \'{name}\': {resp}")

    async def handleGroup(self, c: Context) -> None:
        msg = c.message.text
        id = c.message.group
        raw = json.loads(c.message.raw_message)

        name = self.getName(raw)
        groupName = self.getGroupName(raw)

        mentioned = False
        # counter = 0
        for mention in c.message.mentions:
            if mention["uuid"] == "bf7d2593-ebcd-4a5d-97bd-411ef43096fd":
                mentioned = True
                name2 = "J.A.C.O.B."

                m1 = msg[:mention['start']]
                m2 = msg[mention['start']+mention['length']:]
                msg = f"{m1} {name2} {m2}"
                break
            # else:
            #     name2 = f"NAME{counter}"
            #     counter += 1
            # m1 = msg[:mention['start']]
            # m2 = msg[mention['start']+mention['length']:]
            # msg = f"{m1} {name2} {m2}"

        self.logger.info(f"From \'{name}\' in group \'{groupName}\': {msg}")

        if not mentioned:
            # Check reply
            raw = json.loads(c.message.raw_message)
            dataMessage = raw['envelope']['dataMessage']
            if 'quote' in dataMessage:
                if dataMessage['quote']['authorUuid'] != "bf7d2593-ebcd-4a5d-97bd-411ef43096fd":
                    self.logger.info("-- Ignoring message")
                    return
            else:
                self.logger.info("-- Ignoring message")
                return

        # Initialize conversation history if not exists
        if id not in self.history:
            self.history[id] = [SystemMessage(self.prompt)]

        x = msg.strip().split()
        if mentioned:
            x = x[1:]
        match x:
            case ["!clear", *_]:
                prompt = self.history[id][0].content
                self.history[id] = [SystemMessage(prompt)]
                await c.reply("Context cleared!")
                return
            case ["!source"]:
                await c.reply("See my source code at: https://github.com/ME-IRL/JACOB")
                return
            case ["!info", *_] | ["!help", *_]:
                await c.reply("<Insert help here>")
                return
            case ["!system"]:
                prompt = self.history[id][0].content
                await c.reply(f"The current system prompt is as follows:\n\n{prompt}")
                return
            case ["!system", *prompt]:
                self.history[id] = [SystemMessage(self.prompt + "\n\n" + ' '.join(prompt))]
                await c.reply("System prompt set and context cleared!")
                return

        # Get AI response
        resp = self.ai.chat(msg, self.history[id])
        await c.stop_typing()

        # Send response and log
        await c.reply(resp)
        if len(resp) > 10:
            resp = resp[:80] + "..."
        self.logger.info(f"To   \'{name}\' in group \'{groupName}\': {resp}")

    async def handle(self, c: Context) -> None:
        """Handle incoming Signal messages.

        Args:
            c: Signal context containing message information
        """
        try:
            msg = c.message.text
            id = c.message.source_uuid

            if not msg:
                return

            # Handle group messages
            if c.message.is_group():
                await self.handleGroup(c)
            else:
                await self.handleDirect(c)

            # self.logger.info(f"Received message from {id}: {msg}")

            # await c.start_typing()

            # # Initialize conversation history if not exists
            # if id not in self.history:
            #     self.history[id] = [SystemMessage(self.prompt)]

            # # Get AI response
            # resp = self.ai.chat(msg, self.history[id])
            # await c.stop_typing()

            # # Send response and log
            # await c.send(resp)
            # self.logger.info(f"Sent response to {id}")

        except Exception as e:
            self.logger.error(f"Error handling message from {id}: {e}", exc_info=True)
            await c.send("I'm sorry, I encountered an error processing your request.")

    def load(self, filename: str) -> None:
        """Load conversation history from persistent storage."""
        try:
            with open(f"{filename}.pkl", "rb") as f:
                self.history = pickle.load(f)
            self.logger.info("Loaded conversation history")
            # for user in self.history:
            #     self.history[user][0] = SystemMessage(self.prompt)
        except FileNotFoundError:
            self.logger.warning("History file not found, starting with empty history")
        except Exception as e:
            self.logger.error(f"Error loading history: {e}", exc_info=True)

    def save(self, filename: str) -> None:
        """Save conversation history to persistent storage."""
        try:
            with open(f"{filename}.pkl", "wb") as f:
                pickle.dump(self.history, f)
            self.logger.info("Saved conversation history")
        except Exception as e:
            self.logger.error(f"Error saving history: {e}", exc_info=True)


class MeshBot:
    """
    Class to handle village chatbot
    """

    def __init__(self, serial_port: str, ai: MultiAssistant, prompt: str):
        # set up meshtastic threads, note only responding to text messages
        pub.subscribe(self.onReceive, "meshtastic.receive.text")
        pub.subscribe(self.onConnection, "meshtastic.connection.established")

        # The mestastic interface we will use for comms
        self.interface = meshtastic.serial_interface.SerialInterface(serial_port)
        self.ai = ai
        self.prompt = prompt
        self.history: Dict[str, list[BaseMessage]] = {}
        self.logger = logging.getLogger("Mesh")

    def load(self, filename: str) -> None:
        """Load conversation history from persistent storage."""
        try:
            with open(f"{filename}.pkl", "rb") as f:
                self.history = pickle.load(f)
            self.logger.info("Loaded conversation history")
            for user in self.history:
                self.history[user][0] = SystemMessage(self.prompt)
        except FileNotFoundError:
            self.logger.warning("History file not found, starting with empty history")
        except Exception as e:
            self.logger.error(f"Error loading history: {e}", exc_info=True)

    def save(self, filename: str) -> None:
        """Save conversation history to persistent storage."""
        try:
            with open(f"{filename}.pkl", "wb") as f:
                pickle.dump(self.history, f)
            self.logger.info("Saved conversation history")
        except Exception as e:
            self.logger.error(f"Error saving history: {e}", exc_info=True)

    def onReceive(self, packet, interface):
        """
        Handles reciving and responding to messages

        Args:
            packet (_type_): _description_
            interface (_type_): _description_
        """

        self.logger.info(f'Got Message from {packet["fromId"]}: {packet["decoded"]["text"]}')

        if "channel" in packet or packet["toId"] == "^all":
            self.logger.info("Broadcast message -- ignored")
            # TODO: Decide if we want to let the bot interact with channel messages too
        else:  # Message was a direct message
            msg = packet["decoded"]["text"].strip()
            id = packet["fromId"]

            # Initialize conversation history if not exists
            if id not in self.history:
                self.history[id] = [SystemMessage(self.prompt)]

            # Get AI response
            resp = self.ai.chat(msg, self.history[id])

            # Send response and log
            self.interface.sendText(resp, destinationId=packet["from"])
            logger.info(f"Sent response to {id}")

    def onConnection(self, interface, topic=pub.AUTO_TOPIC):
        """
        Called when connection or reconnecting

        Args:
            interface (obj):The meshtastic interface object
            topic (_type_, optional): _description_. Defaults to pub.AUTO_TOPIC.
        """

        self.logger.info("Connected to device")


def main() -> None:
    """Main entry point for the Signal bot application."""
    logger = getLogger("main")
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
        aicommand.load("signal")
        bot.register(aicommand)

        # mesh = MeshBot(
        #     settings.MESH_SERIAL_PORT,
        #     ai,
        #     settings.SYSTEM_PROMPT + settings.MESH_ADDITIONAL_PROMPT,
        # )
        # mesh.load("mesh")

        # Start the bot
        logger.info("Starting Signal bot...")
        bot.start()

    except KeyboardInterrupt:
        print()
        logger.info("Shutting down gracefully (KeyboardInterrupt)")
    except Exception as e:
        print()
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Ensure history is saved on shutdown
        if "mesh" in locals():
            mesh.save("mesh")
            logger.info("Saved meshtastic conversation history on shutdown")
        if "aicommand" in locals():
            aicommand.save("signal")
            logger.info("Saved signal conversation history on shutdown")


if __name__ == "__main__":
    main()
