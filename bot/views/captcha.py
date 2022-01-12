import asyncio
import string

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
                        f"Attempt {captcha_view.attempt}/{captcha_view.max_attempts}",
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
        self.view.set_column_progress(column=self.column, clicked_column_button_label=self.label)
        self.view.clicked_letters.append(self.label)

        # check if last column was pressed
        if self.view.is_captcha_completed:
            if self.view.is_captcha_valid:
                self.view.captcha_valid = True
                await self.view.captcha_complete(interaction)
                self.view.stop()
                return

            if self.view.can_retry:
                self.view.attempt += 1
                await self.view.new_captcha(interaction=interaction)
                return
            else:
                await self.view.captcha_kick(interaction)
                self.view.stop()
                return

        await interaction.response.edit_message(view=self.view)


class NewCaptchaButton(nextcord.ui.Button['CaptchaView']):
    def __init__(self):
        super().__init__(
            style=nextcord.ButtonStyle.danger,
            emoji="🔄",
            label="New Captcha",
            custom_id='persistent_view:new_captcha'
        )

    async def callback(self, interaction):
        await self.view.new_captcha(interaction=interaction)
        return


class CaptchaView(nextcord.ui.View, BaseCaptchaView):
    # pycharm linter needs it
    children: List[CaptchaButton]

    def __init__(self, rows=None, captcha=None, max_attempts=3):
        super().__init__(timeout=None)
        self.captcha = captcha
        self.rows = rows
        self.columns = self._get_columns()
        self.clicked_letters = []
        self.captcha_completed = False
        self.disabled_columns = 0
        self.max_attempts = max_attempts
        self.attempt = 1
        self.captcha_valid = False
        self._init_captcha_buttons()

    def _init_captcha_buttons(self):
        if not self.columns:
            return

        for column in range(self.columns):
            captcha_column_letters = self._get_column_letters(column)
            for row in range(self.rows):
                # for each column, we add a letter per row
                row_letter = captcha_column_letters.pop()
                self.add_item(CaptchaButton(row, column, label=row_letter))

        self.add_item(NewCaptchaButton())

    def _clear_state(self):
        self.disabled_columns = 0
        if self.children:
            self.clear_items()
        if self.clicked_letters:
            self.clicked_letters.clear()

    def _get_new_captcha_buttons(self):
        self._clear_state()
        self._init_captcha_buttons()

    async def new_captcha(self, interaction):
        captcha = Captcha(member=interaction.user)
        captcha.generate()

        # refresh captcha
        self.captcha = captcha
        self._get_new_captcha_buttons()

        captcha_image_url = await self.get_captcha_image_url(captcha, interaction.user)
        captcha_embed = self.get_captcha_embed(captcha_view=self)
        captcha_embed.set_image(url=captcha_image_url)

        await interaction.response.edit_message(view=self, embed=captcha_embed)

    def _get_columns(self):
        if not self.captcha:
            return None

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

    def set_column_progress(self, column, clicked_column_button_label):
        captcha_letters = self.captcha.text.split()

        # if user clicks wrong btn, complete captcha and disable all columns
        if captcha_letters[column] != clicked_column_button_label:
            # ignore retry button
            for children in self.children[:-1]:
                children.disabled = True
                if children.label == captcha_letters[column]:
                    children.style = nextcord.ButtonStyle.success
                else:
                    children.style = nextcord.ButtonStyle.danger

            self.disabled_columns = self.columns

        else:
            for children in self.children[:-1]:
                if children.column == column:
                    children.disabled = True
                    if children.label == captcha_letters[column]:
                        children.style = nextcord.ButtonStyle.success
                    else:
                        children.style = nextcord.ButtonStyle.danger

            self.disabled_columns += 1

    @staticmethod
    async def captcha_kick(interaction, timer=5):
        embed = nextcord.Embed(
            title="Captcha Failed",
            description=f"You have failed the captcha and will be kicked in {timer} seconds.",
            color=0xe00000
        )  # Red
        await interaction.response.edit_message(
            embed=embed,
            view=None
        )
        await asyncio.sleep(timer)
        await interaction.guild.kick(interaction.user)

    @staticmethod
    async def captcha_complete(interaction):
        embed = nextcord.Embed(
            title="Captcha Completed",
            description=f"You have completed the captcha",
            color=0x2fa737
        )  # Red
        await interaction.response.edit_message(
            embed=embed,
            view=None
        )

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
        return self.attempt < self.max_attempts


class VerifyMeView(nextcord.ui.View, BaseCaptchaView):
    current_users = set()

    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(label='Verify Me!', style=nextcord.ButtonStyle.green, custom_id='persistent_view:send_captcha')
    async def send_captcha(self, button, interaction):
        if interaction.user.id in self.current_users:
            return

        config = get_config(interaction.guild.id)

        captcha = Captcha(member=interaction.user)
        captcha.generate()

        captcha_view = CaptchaView(rows=4, captcha=captcha)

        captcha_image_url = await self.get_captcha_image_url(captcha, interaction)
        captcha_embed = self.get_captcha_embed(captcha_view=captcha_view)
        captcha_embed.set_image(url=captcha_image_url)

        await interaction.response.send_message(view=captcha_view, embed=captcha_embed, ephemeral=True)
        self.current_users.add(interaction.user.id)
        await captcha_view.wait()

        if captcha_view.captcha_valid:
            # remove unverified role add verified role (or custom)
            verified_role = get(interaction.user.guild.roles, id=config["captcha_settings"]["verified_role"])
            await interaction.user.add_roles(verified_role)

            unverified_role = get(interaction.user.guild.roles, id=config["captcha_settings"]["unverified_role"])
            await interaction.user.remove_roles(unverified_role)

            self.current_users.remove(interaction.user.id)
