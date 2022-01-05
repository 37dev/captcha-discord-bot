import nextcord
import os
from discord.ext import commands
from bot.utils.generics import get_guild_prefix, get_token_from_config
from bot.utils.translation import Translator
from bot.views.captcha import VerifyMeView

intents = nextcord.Intents.default()
intents.members = True


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persistent_views_added = False

    async def on_ready(self):
        if not self.persistent_views_added:
            self.add_view(VerifyMeView())
            self.persistent_views_added = True

        print(f'We have logged in as {bot.user}')
        print(nextcord.__version__)
        await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f"Captchas!"))


bot = Bot(get_guild_prefix, intents=intents)

bot.translate = Translator()

# Load cogs
if __name__ == '__main__':
    for filename in os.listdir("bot/cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"bot.cogs.{filename[:-3]}")


bot.run(get_token_from_config())

"""
# setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
"""