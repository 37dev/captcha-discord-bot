import nextcord

from discord.ext import commands
from nextcord.utils import get

from bot.utils.generics import get_config


class OnChannelCreate(commands.Cog, name="on channel create"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        config = get_config(channel.guild.id)
        unverified_role = get(channel.guild.roles, id=config["captcha_settings"]["unverified_role"])

        if unverified_role is not None:
            if isinstance(channel, nextcord.TextChannel):
                perms = channel.overwrites_for(unverified_role)
                perms.read_messages = False
                await channel.set_permissions(unverified_role, overwrite=perms)

            elif isinstance(channel, nextcord.VoiceChannel):

                perms = channel.overwrites_for(unverified_role)
                perms.read_messages = False
                perms.connect = False
                await channel.set_permissions(unverified_role, overwrite=perms)


def setup(bot):
    bot.add_cog(OnChannelCreate(bot))
