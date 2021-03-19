import discord

positive_name = "triangle_heart"

async def add_positive_emoji(guild: discord.Guild, asset_path: str):

    # If the emoji is already present in the server, skip it
    for e in await guild.fetch_emojis():
        if e.name == positive_name:
            positive_emoji = e
            return

    file_bytes = None
    with open(asset_path, "rb") as image:
        file = image.read()
        file_bytes = bytes(file)
    
    await guild.create_custom_emoji(
        name=positive_name,
        image=file_bytes,
        reason="Thanks for using PointyPal! Contact us at "
               "campus.utahtriangle.org if you have any questions!"
    )

    return
    

async def verify_command(message: discord.Message, approved):

    # Define the guild and list of emoji
    guild: discord.Guild = message.guild
    emojis: List[discord.Emoji] = await guild.fetch_emojis()

    # Define the name for the triangle heart emoji
    heart_name = positive_name

    # Scan through the emojis to attempt to find the triangle heart
    positive_emoji = "👍"
    for e in emojis:
        e: discord.Emoji = e
        if e.name == heart_name:
            positive_emoji = e
            break

    negative_emoji = "❌"

    # Add the proper reacc to the message
    result = None
    if approved:
        result = positive_emoji
    else:
        result = negative_emoji

    await message.add_reaction(result)

    return

async def post_help(
    client: discord.Client,
    message: discord.Message,
):
    await message.reply(
        f"Need help using {client.user.mention}? View the help page on GitHub "
         "or contact the team at https://discord.com/invite/sd5G5Zc"
    )

async def post_greeting(
    client: discord.Client,
    channel: discord.TextChannel,
):
    content = ""
    with open('assets/greeting.txt', 'r') as file:
        content = file.read()

    template_dict = {
        "bot_name": client.user.mention,
        "chan_name": channel.mention
    }

    content = content.format(**template_dict)

    await channel.send(f"" + content)