import discord
import yaml
from utils.CommandManager import CommandManager

# ===== CONFIG SETUP ===========================================================

# Import config and secrets
CONFIG_PATH = "configs/config.yaml"
SECRET_PATH = "configs/secrets.yaml"

# Load secrets into dict
SECRET = None
with open(SECRET_PATH, 'r') as file:
    SECRET = yaml.load(file, Loader=yaml.FullLoader)

# ===== CLIENT SETUP ===========================================================

# Allow the bot to see server members by setting member intent to true.
# SPECIFICALLY required for admin commands.
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# Instantiate a command manager
command_manager = CommandManager(client, CONFIG_PATH)

@client.event
async def on_ready():
    print('Bot has logged in as {0.user}'.format(client))

@client.event
async def on_guild_join(guild: discord.Guild):

    print(f"Bot has been added to server: {guild.name}")

    # Add the success emoji automatically on guild join
    # TODO: Exception/permissions handling
    await command_manager.modules["general_commands"].add_positive_emoji_override(
        guild
    )

    if guild.system_channel:
        sys_channel: discord.TextChannel = guild.system_channel
        await sys_channel.send(
            "Congratulations on installing PointyPal! PointyPal helps you "
            "keep your academic Discord server clean by letting students "
            "add themselves to class and department channels. To use PointyPal, "
            "simply tag it at the beginning of a message!\n"
            "\n"
            "For basic joining and leaving courses, you can use:\n"
            "```\n"
            "@PointyPal join-class CS1410\n"
            "@PointyPal drop-class BIO4200\n"
            "@PointyPal join-department PHYS\n"
            "```"
            "If you have issues using the bot, or need documentation for "
            "administrator commands, be sure to check out the documentation "
            "at <https://github.com/UtahTriangle/pointypal/>!"
        )

    pass

@client.event
async def on_message(message: discord.Message):

    # Skip the message if the message was sent by the client, or if the
    # bot isn't ready to accept commands yet.
    if not is_ready:
        print("Message received before bot was ready.")
        return
        
    if message.author == client.user:
        return

    if command_manager.is_command(message):
        print("Command received from:")
        print("\tGuild:", message.author.nick)
        print("\tUser:",  message.guild.name)
        await command_manager.run(message)
        print()

is_ready = True
client.run(SECRET["token"])
