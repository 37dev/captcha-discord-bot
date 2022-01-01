import shutil

from discord.ext import commands


class OnRemoveCog(commands.Cog, name="on remove"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if member.bot:
            return

        # Remove user captcha folder
        member_id = member.id
        folder_path = f"captchaFolder/captcha_{member_id}"
        try:
            shutil.rmtree(folder_path)  # Remove file
        except (FileNotFoundError, FileExistsError):
            return


def setup(bot):
    bot.add_cog(OnRemoveCog(bot))
