import discord
import numpy as np
import random
import string
import Augmentor
import os
import shutil
import asyncio
import time
from discord.ext import commands
from discord.utils import get
from PIL import ImageFont, ImageDraw, Image
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
                    title=self.bot.translate.message(member.guild.id, "on_member_join", "HAS_BEEN_KICKED").format(member),
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

            # Create captcha
            image = np.zeros(shape=(100, 350, 3), dtype=np.uint8)

            # Create image
            image = Image.fromarray(image + 255)  # +255 : black to white

            # Add text
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(font="bot/utils/arial.ttf", size=60)

            text = ' '.join(
                random.choice(string.ascii_uppercase) for _ in range(6))  # + string.ascii_lowercase + string.digits

            # Center the text
            w_, h_ = (350, 100)
            w, h = draw.textsize(text, font=font)
            draw.text(((w_ - w) / 2, (h_ - h) / 2), text, font=font, fill=(90, 90, 90))

            # Save
            member_id = member.id
            folder_path = f"captcha_folder/{member.guild.id}/captcha_{member_id}"
            try:
                os.mkdir(folder_path)
            except (FileNotFoundError, FileExistsError):
                if os.path.isdir(f"captcha_folder/{member.guild.id}") is False:
                    os.mkdir(f"captcha_folder/{member.guild.id}")
                if os.path.isdir(folder_path) is True:
                    shutil.rmtree(folder_path)
                os.mkdir(folder_path)
            image.save(f"{folder_path}/captcha{member_id}.png")

            # Deform
            p = Augmentor.Pipeline(folder_path)
            p.random_distortion(probability=1, grid_width=4, grid_height=4, magnitude=14)
            p.process()

            # Search file in folder
            path = f"{folder_path}/output"
            files = os.listdir(path)
            captcha_name = [i for i in files if i.endswith('.png')]
            captcha_name = captcha_name[0]

            image = Image.open(f"{folder_path}/output/{captcha_name}")

            # Add line
            width = random.randrange(6, 8)
            co1 = random.randrange(0, 75)
            co3 = random.randrange(275, 350)
            co2 = random.randrange(40, 65)
            co4 = random.randrange(40, 65)
            draw = ImageDraw.Draw(image)
            draw.line([(co1, co2), (co3, co4)], width=width, fill=(90, 90, 90))

            # Add noise
            noise_percentage = 0.25  # 25%

            pixels = image.load()  # create the pixel map
            for i in range(image.size[0]):  # for every pixel:
                for j in range(image.size[1]):
                    rdn = random.random()  # Give a random %
                    if rdn < noise_percentage:
                        pixels[i, j] = (90, 90, 90)

            # Save
            image.save(f"{folder_path}/output/{captcha_name}_2.png")

            # Send captcha
            captcha_file = discord.File(f"{folder_path}/output/{captcha_name}_2.png")
            captcha_embed = await captcha_channel.send(
                self.bot.translate.message(member.guild.id, "on_member_join", "CAPTCHA_MESSAGE").format(member.mention),
                file=captcha_file)
            # Remove captcha folder
            try:
                shutil.rmtree(folder_path)
            except Exception as error:
                print(f"Delete captcha file failed {error}")

            # Check if it is the right user
            def check(message):
                if message.author == member and message.content != "":
                    return message.content

            try:
                msg = await self.bot.wait_for('message', timeout=120.0, check=check)
                # Check the captcha
                password = text.split(" ")
                password = "".join(password)
                if msg.content == password:

                    embed = discord.Embed(description=self.bot.translate.message(
                        member.guild.id, "on_member_join",
                        "MEMBER_PASSED_THE_CAPTCHA"
                    ).format(
                        member.mention
                    ), color=0x2fa737)  # Green
                    await captcha_channel.send(embed=embed, delete_after=5)
                    try:
                        get_role = get(member.guild.roles, id=config["temporary_role"])
                        await member.remove_roles(get_role)
                    except Exception as error:
                        print(f"No temp role found (on_member_join) : {error}")
                    time.sleep(3)
                    try:
                        await captcha_embed.delete()
                    except discord.errors.NotFound:
                        pass
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                    # Logs
                    embed = discord.Embed(
                        title=self.bot.translate.message(
                            member.guild.id,
                            "on_member_join",
                            "MEMBER_PASSED_THE_CAPTCHA"
                        ).format(member),
                        description=self.bot.translate.message(member.guild.id, "on_member_join", "USER_INFORMATION").format(
                            member, member.id), color=0x2fa737)
                    embed.set_footer(
                        text=self.bot.translate.message(
                            member.guild.id, "on_member_join", "DATE"
                        ).format(
                            member_time
                        )
                    )
                    await send_log_message(self, event=member, channel=log_channel, embed=embed)

                else:
                    link = await captcha_channel.create_invite(max_age=172800)  # Create an invite
                    embed = discord.Embed(description=self.bot.translate.message(
                        member.guild.id, "on_member_join",
                        "MEMBER_FAILED_THE_CAPTCHA"
                    ).format(
                        member.mention
                    ), color=0xca1616)  # Red
                    await captcha_channel.send(embed=embed, delete_after=5)
                    embed = discord.Embed(
                        title=self.bot.translate.message(
                            member.guild.id, "on_member_join", "YOU_HAVE_BEEN_KICKED"
                        ).format(
                            member.guild.name
                        ), description=self.bot.translate.message(
                            member.guild.id, "on_member_join",
                            "MEMBER_FAILED_THE_CAPTCHA_REASON"
                        ).format(link), color=0xff0000
                    )

                    try:
                        await member.send(embed=embed)
                    except discord.errors.Forbidden:
                        # can't send dm to user
                        pass
                    await member.kick()

                    time.sleep(3)
                    try:
                        await captcha_embed.delete()
                    except discord.errors.NotFound:
                        pass
                    try:
                        await msg.delete()
                    except discord.errors.NotFound:
                        pass
                    # Logs
                    embed = discord.Embed(
                        title=self.bot.translate.message(member.guild.id, "on_member_join", "MEMBER_HAS_BEEN_KICKED").format(
                            member), description=self.bot.translate.message(
                            member.guild.id, "on_member_join",
                            "MEMBER_FAILED_THE_CAPTCHA_REASON_LOG"
                        ).format(
                            member, member.id), color=0xff0000)
                    embed.set_footer(text=self.bot.translate.message(member.guild.id, "on_member_join", "DATE").format(
                        member_time
                    ))
                    await send_log_message(self, event=member, channel=log_channel, embed=embed)

            except asyncio.TimeoutError:
                link = await captcha_channel.create_invite(max_age=172800)  # Create an invite
                embed = discord.Embed(
                    title=self.bot.translate.message(member.guild.id, "on_member_join", "TIME_IS_OUT"),
                    description=self.bot.translate.message(
                        member.guild.id, "on_member_join",
                        "USER_HAS_EXCEEDED_THE_RESPONSE_TIME"
                    ).format(
                        member.mention
                    ), color=0xff0000)
                await captcha_channel.send(embed=embed, delete_after=5)
                try:
                    embed = discord.Embed(
                        title=self.bot.translate.message(member.guild.id, "on_member_join", "YOU_HAVE_BEEN_KICKED").format(
                            member.guild.name), description=self.bot.translate.message(
                            member.guild.id, "on_member_join", "USER_HAS_EXCEEDED_THE_RESPONSE_TIME_REASON").format(
                            link), color=0xff0000)
                    await member.send(embed=embed)
                    await member.kick()  # Kick the user
                except Exception as error:
                    print(f"Log failed (on_member_join) : {error}")
                time.sleep(3)
                await captcha_embed.delete()
                # Logs
                embed = discord.Embed(
                    title=self.bot.translate.message(
                        member.guild.id,
                        "on_member_join",
                        "MEMBER_HAS_BEEN_KICKED"
                    ).format(member),
                    description=self.bot.translate.message(
                        member.guild.id, "on_member_join",
                        "USER_HAS_EXCEEDED_THE_RESPONSE_TIME_LOG"
                    ).format(
                        member,
                        member.id
                    ),
                    color=0xff0000)
                embed.set_footer(text=self.bot.translate.message(
                    member.guild.id,
                    "on_member_join",
                    "DATE"
                ).format(member_time))
                await send_log_message(self, event=member, channel=log_channel, embed=embed)


def setup(bot):
    bot.add_cog(OnJoinCog(bot))
