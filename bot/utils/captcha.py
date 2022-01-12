import os
import shutil
import string

import Augmentor
import nextcord
import numpy as np
from PIL import ImageFont, ImageDraw, Image

from bot.utils.generics import system_rng


class Captcha:
    def __init__(self, member):
        self.member = member
        self.text = None
        self.file = None

    def _generate_image(self):
        random = system_rng()
        image = np.zeros(shape=(100, 320, 3), dtype=np.uint8)

        image = Image.fromarray(image + 255)  # +255 : black to white

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font="bot/utils/arial.ttf", size=60)

        self.text = ' '.join(
            random.choice(string.ascii_uppercase) for _ in range(5))

        w_, h_ = (350, 100)
        w, h = draw.textsize(self.text, font=font)
        draw.text(((w_ - w) / 2, (h_ - h) / 2), self.text, font=font, fill=(90, 90, 90))

        image_folder_path = f"captcha_folder/{self.member.guild.id}/captcha_{self.member.id}"
        image_path = f"{image_folder_path}/captcha{self.member.id}.png"

        try:
            os.mkdir(image_folder_path)
        except (FileNotFoundError, FileExistsError):
            if os.path.isdir(f"captcha_folder/{self.member.guild.id}") is False:
                os.mkdir(f"captcha_folder/{self.member.guild.id}")
            if os.path.isdir(image_folder_path) is True:
                shutil.rmtree(image_folder_path)
            os.mkdir(image_folder_path)
        image.save(image_path)

        return image_folder_path

    @staticmethod
    def _deform_image(image_folder_path, noise):
        random = system_rng()

        # distort image
        p = Augmentor.Pipeline(image_folder_path)
        p.random_distortion(probability=1, grid_width=4, grid_height=4, magnitude=14)
        p.process()

        distorted_image_path = f"{image_folder_path}/output"
        files = os.listdir(distorted_image_path)

        captcha_name = [i for i in files if i.endswith('.png')]

        captcha_name = captcha_name[0]
        image = Image.open(f"{image_folder_path}/output/{captcha_name}")

        # Add lines
        width = random.randrange(6, 8)
        co1 = random.randrange(0, 75)
        co3 = random.randrange(275, 350)
        co2 = random.randrange(40, 65)
        co4 = random.randrange(40, 65)
        draw = ImageDraw.Draw(image)
        draw.line([(co1, co2), (co3, co4)], width=width, fill=(90, 90, 90))

        # Add noise
        noise_percentage = noise / 100

        pixels = image.load()  # create the pixel map
        for i in range(image.size[0]):  # for every pixel:
            for j in range(image.size[1]):
                rdn = random.random()  # Give a random %
                if rdn < noise_percentage:
                    pixels[i, j] = (90, 90, 90)

        # Save
        image.save(f"{image_folder_path}/output/{captcha_name}_2.png")

        # Send captcha
        captcha_file = nextcord.File(f"{image_folder_path}/output/{captcha_name}_2.png")

        # Remove captcha folder
        try:
            shutil.rmtree(image_folder_path)
        except Exception as error:
            print(f"Delete captcha file failed {error}")

        return captcha_file

    def generate(self, noise=25):
        image_folder_path = self._generate_image()
        captcha_file = self._deform_image(image_folder_path, noise=noise)
        self.file = captcha_file
