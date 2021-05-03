import discord
import regex as re
from dotmap import DotMap
import yaml

class GeneralCommands:

    def __init__(self, client, config_path):
        self.client = client
        self.CONFIG = None
        with open(config_path, 'r') as file:
            config_dict = yaml.load(file, Loader=yaml.FullLoader)
            self.CONFIG = DotMap(config_dict)

    async def help(self, message, tokens):
        await message.reply(
            "If you need help, be sure to check out the documentation "
            "at <https://github.com/UtahTriangle/pointypal/>!\n"
            "\n"
            "For basic joining and leaving courses, you can use:\n"
            "```\n"
            "@PointyPal join-class CS1410\n"
            "@PointyPal drop-class BIO4200\n"
            "@PointyPal join-department PHYS\n"
            "```"
        )