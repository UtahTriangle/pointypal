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

    # Add the success emoji automatically on guild join
    # TODO: Exception/permissions handling
    await command_manager.modules["general_commands"].add_positive_emoji_override(
        guild
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
        await command_manager.run(message)

is_ready = True
client.run(SECRET["token"])
