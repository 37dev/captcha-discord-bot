import string

import discord
import nextcord

from typing import List

from nextcord.utils import get

from bot.utils.captcha import Captcha
from bot.utils.generics import system_rng, get_config


class BaseCaptchaView:
    @staticmethod
    def get_captcha_embed(captcha_view):
        captcha_embed = nextcord.Embed(
            title="**Complete the Captcha!**",
            description=f"Press each letter one-by-one using the buttons below.\n"
                        f"Attempt {captcha_view.retries}/{captcha_view.max_retries}",
            color=0x2fa737
        )

        return captcha_embed

    @staticmethod
    async def get_captcha_image_url(captcha, interaction):
        config = get_config(interaction.guild.id)

        captcha_images_channel = interaction.guild.get_channel(config["captcha_images_channel"])

        captcha_image_embed = await captcha_images_channel.send(file=captcha.file)
        image_url = captcha_image_embed.attachments[0].proxy_url
        await captcha_image_embed.delete()

        return image_url


class CaptchaButton(nextcord.ui.Button['CaptchaView']):
    def __init__(self, row, column, label):
        super().__init__(style=nextcord.ButtonStyle.secondary, label=label, row=row)
        self.column = column

    async def callback(self, interaction):
        self.view.disable_clicked_column(column=self.column)
        self.view.clicked_letters.append(self.label)
        self.style = nextcord.ButtonStyle.danger

        await interaction.response.edit_message(view=self.view)

        # check if last column was pressed
        if self.view.is_captcha_completed:
            if self.view.is_captcha_valid:
                self.view.captcha_valid = True
                self.view.stop()
                return

            if self.view.can_retry:
                await self.view.retry_captcha(interaction=interaction)
                return


class NewCaptchaButton(nextcord.ui.Button['CaptchaView']):
    def __init__(self):
        super().__init__(style=nextcord.ButtonStyle.danger, emoji="🔄", label="New Captcha")

    async def callback(self, interaction):
        await self.view.retry_captcha(interaction=interaction)
        return


class CaptchaView(nextcord.ui.View, BaseCaptchaView):
    # pycharm linter needs it
    children: List[CaptchaButton]

    def __init__(self, rows, captcha, max_retries=3):
        super().__init__()
        self.captcha = captcha
        self.rows = rows
        self.columns = self._get_columns()
        self.clicked_letters = []
        self.captcha_completed = False
        self.disabled_columns = 0
        self.max_retries = max_retries
        self.retries = 0
        self.captcha_valid = False
        self.get_buttons()

    def get_buttons(self):
        if self.children:
            self.clear_items()

        for column in range(self.columns):
            captcha_column_letters = self._get_column_letters(column)
            for row in range(self.rows):
                # for each column, we add a letter per row
                row_letter = captcha_column_letters.pop()
                self.add_item(CaptchaButton(row, column, label=row_letter))

        self.add_item(NewCaptchaButton())

    async def retry_captcha(self, interaction):
        captcha = Captcha(member=interaction.user)
        captcha.generate()

        # refresh captcha
        self.captcha = captcha

        captcha_image_url = await self.get_captcha_image_url(captcha, interaction.user)
        captcha_embed = self.get_captcha_embed(captcha_view=self)
        captcha_embed.set_image(url=captcha_image_url)

        self.get_buttons()

        await interaction.response.edit_message(view=self, embed=captcha_embed)

    def _get_columns(self):
        text = self.captcha.text
        columns = len(text.replace(" ", ""))
        return columns

    def _get_column_letters(self, column):
        random = system_rng()
        captcha_letters = self.captcha.text.split()
        random_letters = []

        column_captcha_letter = captcha_letters[column]

        while column_captcha_letter in random_letters or not random_letters:
            random_letters = random.sample(string.ascii_uppercase, self.rows)

        captcha_letter_pos = random.randrange(0, self.rows)

        random_letters[captcha_letter_pos] = column_captcha_letter
        return random_letters

    def disable_clicked_column(self, column):
        for children in self.children:
            if children.column == column:
                children.disabled = True

        self.disabled_columns += 1

    @property
    def is_captcha_completed(self):
        if self.disabled_columns == self.columns:
            return True

    @property
    def is_captcha_valid(self):
        captcha_letters = self.captcha.text.split()
        return captcha_letters == self.clicked_letters

    @property
    def can_retry(self):
        return self.retries < self.max_retries


class VerifyMeView(nextcord.ui.View, BaseCaptchaView):
    def __init__(self):
        super().__init__()
        self.running_captcha = False

    @nextcord.ui.button(label='Verify Me!', style=nextcord.ButtonStyle.green)
    async def send_captcha(self, button, interaction):
        config = get_config(interaction.guild.id)

        self.running_captcha = True
        captcha = Captcha(member=interaction.user)
        captcha.generate()

        captcha_view = CaptchaView(rows=4, captcha=captcha)

        captcha_image_url = await self.get_captcha_image_url(captcha, interaction)
        captcha_embed = self.get_captcha_embed(captcha_view=captcha_view)
        captcha_embed.set_image(url=captcha_image_url)

        await interaction.response.send_message(view=captcha_view, embed=captcha_embed, ephemeral=True)

        await captcha_view.wait()

        if captcha_view.captcha_valid:
            user_temporary_role = get(interaction.user.guild.roles, id=config["temporary_role"])
            await interaction.user.remove_roles(user_temporary_role)

        self.stop()
