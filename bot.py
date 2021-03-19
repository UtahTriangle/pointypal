import discord
from typing import List
from class_manager import run_command
import plugs

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

command_channel_name = "📝pal-class-manager"

@client.event
async def on_ready():
    print('Bot has logged in as {0.user}'.format(client))

@client.event
async def on_guild_join(guild: discord.Guild):

    channel: discord.TextChannel = await guild.create_text_channel(command_channel_name)

    plugs.post_greeting(client, channel)

    await plugs.add_positive_emoji(guild, "assets/success.png")

@client.event
async def on_message(message: discord.Message):

    # Skip the message if the message was sent by the client
    if message.author == client.user:
        return

    # Check if the command was a registered !pal command
    if     ((message.content.startswith('!pal'))
         or (message.content.startswith(f"<@!{client.user.id}>")) # Desktop
         or (message.content.startswith(f"<@{client.user.id}>")) # Mobile, for some damn reason.
       and (message.channel.name == command_channel_name)):

        tokens = message.content.split(" ")

        result = await run_command(client, message, tokens)

        await plugs.verify_command(message, result)

        if not result:
            await plugs.post_help(client, message)

token = ""
with open('assets/token', 'r') as file:
    token = file.read()

client.run(token)