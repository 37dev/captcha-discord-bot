import discord
import asyncio
import time
from discord.ext import commands
from discord.utils import get
from bot.utils.generics import get_config
from bot.utils.logs import send_log_message


class OnJoinCog(commands.Cog, name="on join"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.bot:
            return

        config = get_config(member.guild.id)
        log_channel = config["log_channel"]
        captcha_channel = self.bot.get_channel(config["captcha_channel"])

        member_time = "{}-{}-{} {}:{}:{}".format(
            member.joined_at.year,
            member.joined_at.month,
            member.joined_at.day,
            member.joined_at.hour,
            member.joined_at.minute,
            member.joined_at.second
        )

        if config["min_account_date"]:
            user_account_date = member.created_at.timestamp()
            if user_account_date < config["min_account_date"]:
                min_account_date = config["min_account_date"] / 3600
                embed = discord.Embed(
                    title=self.bot.translate.message(member.guild.id, "on_member_join", "YOU_HAVE_BEEN_KICKED").format(
                        member.guild.name),
                    description=self.bot.translate.message(
                        member.guild.id, "on_member_join", "MIN_ACCOUNT_AGE_KICK_REASON"
                    ).format(
                        min_account_date), color=0xff0000)
                await member.send(embed=embed)
                await member.kick()

                embed = discord.Embed(
                    title=self.bot.translate.message(member.guild.id, "on_member_join", "HAS_BEEN_KICKED").format(
                        member),
                    description=self.bot.translate.message(
                        member.guild.id, "on_member_join",
                        "MIN_ACCOUNT_AGE_HAS_BEEN_KICKED_REASON"
                    ).format(
                        min_account_date,
                        member.created_at,
                        member,
                        member.id
                    ),
                    color=0xff0000)
                embed.set_footer(text=f"at {member.joined_at}")
                await send_log_message(self, event=member, channel=log_channel, embed=embed)

        if config["captcha"]:

            # Give temporary role
            get_role = get(member.guild.roles, id=config["temporary_role"])
            await member.add_roles(get_role)

            new_member_mention = await captcha_channel.send(member.mention)
            await new_member_mention.delete()


def setup(bot):
    bot.add_cog(OnJoinCog(bot))
