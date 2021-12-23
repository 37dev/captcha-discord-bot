import discord
import logging


class MyClient(discord.Client):
    async def on_ready(self):
        pass

    async def on_message(self, message):
        pass


# setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


client = MyClient()
client.run('OTIzMDI2MzI4OTY0NDYwNjI1.YcKBQQ.BfkktJ2aLBAb1DEEHJwmxHxDZJk')
