import nextcord
import asyncio
from discord.ext import commands
from discord.utils import get
from discord.errors import HTTPException
from bot.utils.generics import get_config, update_config
from bot.views.captcha import VerifyMeView
from bot.views.generics import ConfirmationView


class CaptchaCog(commands.Cog, name="Setup Captcha command"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='captcha',
        usage="<on/off>",
        description="Enable or disable the captcha system."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    @commands.guild_only()
    async def captcha(self, ctx, captcha_switch):

        captcha_switch = captcha_switch.lower()

        if captcha_switch == "on":
            embed = nextcord.Embed(
                title=self.bot.translate.message(
                    ctx.guild.id,
                    "captcha",
                    "DO_YOU_WANT_TO_SET_UP_THE_CAPTCHA_PROTECTION"
                ),
                description=self.bot.translate.message(
                    ctx.guild.id,
                    "captcha",
                    "DO_YOU_WANT_TO_SET_UP_THE_CAPTCHA_PROTECTION_DESCRIPTION"
                ),
                color=0xff0000
            )
            confirmation_view = ConfirmationView()
            await ctx.channel.send(embed=embed, view=confirmation_view)
            await confirmation_view.wait()

            try:

                if not confirmation_view.confirmed:
                    await ctx.channel.send(self.bot.translate.message(ctx.guild.id, "captcha", "SET_UP_ABANDONED"))
                else:
                    try:
                        config = get_config(ctx.guild.id)
                        is_captcha_on = config["captcha"]

                        if is_captcha_on:
                            await ctx.channel.send(
                                self.bot.translate.message(ctx.guild.id, "captcha", "CAPTCHA_ON_ALREADY")
                            )
                            return

                        loading = await ctx.channel.send(
                            self.bot.translate.message(ctx.guild.id, "captcha", "CREATION_OF_CAPTCHA_PROTECTION")
                        )

                        temporary_role = await ctx.guild.create_role(name="unverified")

                        for channel in ctx.guild.channels:
                            if isinstance(channel, nextcord.TextChannel):

                                perms = channel.overwrites_for(temporary_role)
                                perms.read_messages = False
                                await channel.set_permissions(temporary_role, overwrite=perms)

                            elif isinstance(channel, nextcord.VoiceChannel):

                                perms = channel.overwrites_for(temporary_role)
                                perms.read_messages = False
                                perms.connect = False
                                await channel.set_permissions(temporary_role, overwrite=perms)

                        # Create captcha channel
                        captcha_channel = await ctx.guild.create_text_channel('start-here')

                        perms = captcha_channel.overwrites_for(temporary_role)
                        perms.read_messages = True
                        perms.send_messages = True
                        await captcha_channel.set_permissions(temporary_role, overwrite=perms)

                        perms = captcha_channel.overwrites_for(ctx.guild.default_role)
                        perms.read_messages = False
                        await captcha_channel.set_permissions(ctx.guild.default_role, overwrite=perms)

                        await captcha_channel.edit(slowmode_delay=5)

                        # Create captcha images channel
                        captcha_images_channel = await ctx.guild.create_text_channel('captcha-images-channel')
                        perms = captcha_images_channel.overwrites_for(ctx.guild.default_role)
                        perms.read_messages = False
                        await captcha_images_channel.set_permissions(ctx.guild.default_role, overwrite=perms)

                        # Create log channel
                        if config["log_channel"] is False:
                            log_channel = await ctx.guild.create_text_channel(f"{self.bot.user.name}-logs")
                            perms = log_channel.overwrites_for(ctx.guild.default_role)
                            perms.read_messages = False
                            await log_channel.set_permissions(ctx.guild.default_role, overwrite=perms)

                            config["log_channel"] = log_channel.id

                        config["captcha"] = True
                        config["temporary_role"] = temporary_role.id
                        config["captcha_channel"] = captcha_channel.id
                        config["captcha_images_channel"] = captcha_images_channel.id

                        update_config(ctx.guild.id, config)

                        embed = nextcord.Embed(
                            title="**Server Verification**",
                            description="To prevent bot abuse, new members are required to verify in this server. "
                                        "Please complete the verification promptly, or you risk being kicked from the "
                                        "server.\nPress the button below to begin the verification process",
                            color=0x2fa737
                        )
                        embed.set_author(
                            name="",
                            icon_url=""
                        )
                        embed.set_thumbnail(
                            url=""
                        )
                        await captcha_channel.send(embed=embed, view=VerifyMeView())

                        await loading.delete()
                        embed = nextcord.Embed(
                            title=self.bot.translate.message(ctx.guild.id, "captcha",
                                                             "CAPTCHA_WAS_SET_UP_WITH_SUCCESS"),
                            description=self.bot.translate.message(ctx.guild.id, "captcha",
                                                                   "CAPTCHA_WAS_SET_UP_WITH_SUCCESS_DESCRIPTION"),
                            color=0x2fa737)  # Green
                        await ctx.channel.send(embed=embed)
                    except Exception as error:
                        embed = nextcord.Embed(title=self.bot.translate.message(ctx.guild.id, "global", "ERROR"),
                                               description=self.bot.translate.message(ctx.guild.id, "global",
                                                                                      "ERROR_OCCURRED").format(error),
                                               color=0xe00000)  # Red
                        return await ctx.channel.send(embed=embed)

            except asyncio.TimeoutError:
                embed = nextcord.Embed(title=self.bot.translate.message(ctx.guild.id, "captcha", "TIME_IS_OUT"),
                                       description=self.bot.translate.message(
                                           ctx.guild.id, "setup",
                                           "USER_HAS_EXCEEDED_THE_RESPONSE_TIME").format(
                                           ctx.author.mention
                                       ), color=0xff0000)
                await ctx.channel.send(embed=embed)

        else:
            loading = await ctx.channel.send(
                self.bot.translate.message(ctx.guild.id, "captcha", "DELETION_OF_THE_CAPTCHA_PROTECTION"))
            config = get_config(ctx.guild.id)
            config["captcha"] = False

            # Delete all
            not_deleted = []
            try:
                temporary_role = get(ctx.guild.roles, id=config["temporary_role"])
                await temporary_role.delete()
            except (HTTPException, AttributeError, KeyError):
                not_deleted.append("temporary_role")
            try:
                captcha_channel = self.bot.get_channel(config["captcha_channel"])
                await captcha_channel.delete()
            except (HTTPException, AttributeError, KeyError):
                not_deleted.append("captcha_channel")

            try:
                captcha_images_channel = self.bot.get_channel(config["captcha_images_channel"])
                await captcha_images_channel.delete()
            except (HTTPException, AttributeError, KeyError):
                not_deleted.append("captcha_images_channel")

            # Add modifications
            config["captcha_channel"] = False

            # Edit configuration.json
            update_config(ctx.guild.id, config)

            await loading.delete()
            embed = nextcord.Embed(
                title=self.bot.translate.message(ctx.guild.id, "captcha", "CAPTCHA_WAS_DELETED_WITH_SUCCESS"),
                description=self.bot.translate.message(ctx.guild.id, "captcha",
                                                       "CAPTCHA_WAS_DELETED_WITH_SUCCESS_DESCRIPTION"),
                color=0x2fa737)  # Green
            await ctx.channel.send(embed=embed)
            if len(not_deleted) > 0:
                errors = ", ".join(not_deleted)
                embed = nextcord.Embed(
                    title=self.bot.translate.message(ctx.guild.id, "captcha", "CAPTCHA_DELETION_ERROR"),
                    description=self.bot.translate.message(ctx.guild.id, "captcha",
                                                           "CAPTCHA_DELETION_ERROR_DESCRIPTION").format(
                        errors), color=0xe00000)  # Red
                await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(CaptchaCog(bot))
