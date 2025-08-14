import os
import pickle

from langchain_core.messages import SystemMessage
from signalbot import Command, Context, SignalBot

from assistant import get_time, MultiAssistant

API_KEY = os.environ.get("OPENAI_API_KEY", "")
API_URL = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
SIGNAL_SRV = os.environ.get("SIGNAL_SERVICE", "")
SIGNAL_NUM = os.environ.get("PHONE_NUMBER", "")

SYSTEM_PROMPT = "You are a Signal chat bot named J.A.C.O.B. , short for \"Just Another Cool Online Bot\". Use only as many words needed, but fewer than 800 words."

class AICommand(Command):

    def __init__(self, ai: MultiAssistant, prompt: str):
        super().__init__()
        self.ai = ai
        self.prompt = prompt
        self.history = {}

    async def handle(self, c: Context):
        msg = c.message.text
        id = c.message.source_uuid

        # pprint(vars(c.message))

        # Group message
        if c.message.group:
            return
        # if c.message.group and c.message.text:

        await c.start_typing()

        if id not in self.history:
            self.history[id] = [SystemMessage(SYSTEM_PROMPT)]
        resp = self.ai.chat(msg, self.history[id])
        await c.stop_typing()
        await c.send(resp)

    def load(self):
        try:
            with open("history.pkl", "rb") as f:
                self.history = pickle.load(f)
        except FileNotFoundError:
            print("File does not exist")

    def save(self):
        with open("history.pkl", "wb") as f:
            pickle.dump(self.history, f)


def main():
    ai = MultiAssistant(API_URL, API_KEY)
    ai.add_tool(get_time)

    bot = SignalBot({
        "signal_service": SIGNAL_SRV,
        "phone_number": SIGNAL_NUM,
        "storage": {
            "type": "sqlite",
            "sqlite_db": "signal.db"
        }
    })

    aicommand = AICommand(ai, SYSTEM_PROMPT)
    aicommand.load()

    bot.register(aicommand)
    bot.start()
    bot.scheduler.start()
    aicommand.save()

if __name__ == "__main__":
    main()
