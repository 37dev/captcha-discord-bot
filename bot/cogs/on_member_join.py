import asyncio
from discord.ext import commands
from nextcord.utils import get

from bot.utils.generics import get_config, auto_kick


class OnJoinCog(commands.Cog, name="on join"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.bot:
            return

        config = get_config(member.guild.id)
        captcha_channel = self.bot.get_channel(config["captcha_channel"])

        asyncio.create_task(auto_kick(captcha_channel, member))

        if config["captcha"]:

            # add unverified role
            unverified_role = get(member.guild.roles, id=config["captcha_settings"]["unverified_role"])
            await member.add_roles(unverified_role)

            new_member_mention = await captcha_channel.send(member.mention)
            await new_member_mention.delete()


def setup(bot):
    bot.add_cog(OnJoinCog(bot))
