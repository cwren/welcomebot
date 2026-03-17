import logging
import os
from dotenv import load_dotenv
from signalbot import SignalBot, Config, Command, Context, triggered, enable_console_logging

done = False

class PingCommand(Command):
    @triggered("Ping")
    async def handle(self, context: Context) -> None:
        await context.send("Pong")

def main():
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
        )
    )
    bot.register(PingCommand()) # Run the command for all contacts and groups
    bot.start()

if __name__ == "__main__":
    enable_console_logging(logging.INFO)
    load_dotenv()
    main()
