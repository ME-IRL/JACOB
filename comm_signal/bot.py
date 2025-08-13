from signalbot import SignalBot, Command


class BotBot:
    def __init__(self, srv: str, num: str):
        if not srv or not num:
            raise ValueError("Missing Signal server or number")

        self.bot = SignalBot({
            "signal_service": srv,
            "phone_number": num,
            "storage": {
                "type": "sqlite",
                "sqlite_db": "signal.db"
            }
        })

    def register(self, cmd: Command):
        self.bot.register(cmd)

    def run(self):
        self.bot.start()