import discord
from bot.utils.generics import get_config
from discord.ext import commands
from discord.utils import get


class OnChannelCreate(commands.Cog, name="on channel create"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        data = get_config(channel.guild.id)
        temporary_role = get(channel.guild.roles, id=data["temporary_role"])

        if temporary_role is not None:
            if isinstance(channel, discord.TextChannel):
                perms = channel.overwrites_for(temporary_role)
                perms.read_messages = False
                await channel.set_permissions(temporary_role, overwrite=perms)

            elif isinstance(channel, discord.VoiceChannel):

                perms = channel.overwrites_for(temporary_role)
                perms.read_messages = False
                perms.connect = False
                await channel.set_permissions(temporary_role, overwrite=perms)


def setup(bot):
    bot.add_cog(OnChannelCreate(bot))
