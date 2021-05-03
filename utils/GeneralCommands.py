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
        return


    async def verify_command(
        self,
        message: discord.Message,
        approved: bool
    ):

        # Define the guild and list of emoji
        guild: discord.Guild = message.guild
        emojis: List[discord.Emoji] = await guild.fetch_emojis()

        # Define the name for the triangle heart emoji
        heart_name = self.CONFIG["positive_emoji"]

        # Scan through the emojis to attempt to find the triangle heart
        positive_emoji = "👍"
        for e in emojis:
            e: discord.Emoji = e
            if e.name == heart_name:
                positive_emoji = e
                break

        negative_emoji = "🤔"

        # Add the proper reaction to the message
        result = None
        if approved:
            result = positive_emoji
        else:
            result = negative_emoji

        await message.add_reaction(result)

        return

    async def add_positive_emoji(
        self,
        message,
        tokens
    ):

        guild = message.channel.guild

        # If the emoji is already present in the server, skip it
        for e in await guild.fetch_emojis():
            if e.name == self.CONFIG["positive_emoji"]:
                positive_emoji = e
                return

        file_bytes = None
        with open(f"../{self.CONFIG['heart_path']}", "rb") as image:
            file = image.read()
            file_bytes = bytes(file)
        
        await guild.create_custom_emoji(
            name=self.CONFIG["positive_emoji"],
            image=file_bytes,
            reason="Thanks for using PointyPal! Contact us at "
                "on GitHub if you have any questions!"
        )

        return

    async def add_positive_emoji_override(
        self,
        guild
    ):

        # If the emoji is already present in the server, skip it
        for e in await guild.fetch_emojis():
            if e.name == self.CONFIG["positive_emoji"]:
                positive_emoji = e
                return

        file_bytes = None
        with open(f"../{self.CONFIG['heart_path']}", "rb") as image:
            file = image.read()
            file_bytes = bytes(file)
        
        await guild.create_custom_emoji(
            name=self.CONFIG["positive_emoji"],
            image=file_bytes,
            reason="Thanks for using PointyPal! Contact us at "
                "on GitHub if you have any questions!"
        )

        return