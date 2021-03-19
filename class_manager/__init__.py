import discord
import regex as re
import plugs

bulk_class_limiter = 5

def verify_admin(
    guild: discord.Guild,
    member: discord.Member
):
    is_admin = ((member.guild_permissions.manage_channels is True)
            and (member.guild_permissions.manage_messages is True))

    return is_admin

async def create_and_join_class(
    name: str,
    member: discord.Member,
    channel_type: type,
    parent: discord.CategoryChannel
):

    # Find (or create) class chats.
    channel: GuildChannel = discord.utils.get(parent.channels, name=name)
    if (channel is None):

        # Create class, and post a message welcoming the member.
        if channel_type == discord.TextChannel:

            # Create channel and add member
            channel = await parent.create_text_channel(name)
            await channel.set_permissions(member, view_channel=True, read_messages=True)

            # Post initial invite message
            invite = await channel.create_invite(max_age = 0)
            await channel.send(
                f"Hey, {member.mention}! Congratulations on being the first person in {channel.mention}!\n"
                f"You can invite your friends and classmates by sending them this link: {invite}"
            )

        else:

            # Create channel and add member
            channel = await parent.create_voice_channel(name)
            await channel.set_permissions(member, view_channel=True, read_messages=True)

    else:
        # If a class currently exists, just add them to that one and post accordingly.

        # Check if member actually needs to be added to the class
        member_perms = channel.overwrites_for(member)
        needs_add = ((member_perms.view_channel is None)  or (member_perms.read_messages is None)
                  or (member_perms.view_channel is False) or (member_perms.read_messages is False))

        if needs_add:

            # Allow this member to view this channel
            await channel.set_permissions(member, view_channel=True, read_messages=True)

            # Post welcome message
            if channel_type == discord.TextChannel:
                await channel.send(f"Welcome to {channel.mention}, {member.mention}!")

    return True


async def leave_and_clean_class(
    name: str,
    member: discord.Member,
    guild: discord.Guild,
):
    
    # Verify the class name and snag the department
    name, department = verify_class(name)

    # Attempt to get the department category channel -
    # if none exists, return False.
    dep_channel = discord.utils.get(guild.channels, name=department.upper())
    if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
        return False

    # Attempt to get the channel - if none exists, return False.
    target_channel = discord.utils.get(dep_channel.channels, name=name.lower())
    if target_channel is None:
        return False

    await target_channel.set_permissions(member, view_channel=False,
                                                 read_messages=False)

    return True


async def join_classes(
    client: discord.Client,
    message: discord.Message,
    args
): 

    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author

    # Limit the number of bulk arguments to prevent
    # channel spam.
    args = args[:bulk_class_limiter]
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:
        result = await join_class(client, guild, member, arg)
        num_changes = num_changes + 1 if result else num_changes

    return num_changes > 0


def verify_class(class_string: str):

    # Regular expressions are the bane of my existence
    # This regular expression requires that a "valid class" consists of 2 to 6 letters,
    # followed by 3 to 5 more numbers.
    #
    # For example, "CHEM101", "CS2420", or "ATMOS4000" are all valid classes, but "CS", 
    # "5000", "CS2420ATMOS4000" or simply "" would all be invalid.
    matches = re.search("^[a-zA-Z]{2,6}[0-9]{3,5}$", class_string)

    # If there were no matches, return two NoneTypes to let the member know that
    # the class wasn't valid.    
    if (matches is None) or (len(matches) != 1):
        return None, None

    # Pick out the department portion from the string
    department: str = re.search("^[a-zA-Z]{2,6}", class_string)[0].upper()

    return class_string, department

async def join_class(
    client: discord.Client,
    guild: discord.Guild,
    member: discord.Member,
    class_name: str
):

    # Verify the integrity of the class chat
    class_name, department = verify_class(class_name)
    if class_name is None:
        return False

    # Find (or create) the the department category channel
    dep_channel = discord.utils.get(guild.channels, name=department)
    if  ((dep_channel is None) 
      or (not type(dep_channel) == discord.CategoryChannel)):

        dep_channel = await guild.create_category(department)

        # Add the necessary member permissions for PointyPal to access this chat
        # and then hide it from everybody else.
        await dep_channel.set_permissions(client.user, view_channel=True)
        await dep_channel.set_permissions(guild.default_role, view_channel=False,
                                                              read_messages=False)

    channels = [
        (department.lower(), discord.TextChannel),
        (class_name.lower(), discord.TextChannel),
        (f"{department.upper()} Study Room", discord.VoiceChannel)
    ]

    for c in channels:
        await create_and_join_class(c[0], member, c[1], dep_channel)

    return True


async def remove_classes(
    client: discord.client,
    message: discord.message,
    args
):
    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:
        result = await leave_and_clean_class(arg, member, guild)
        num_changes = num_changes + 1 if result else num_changes

    return num_changes > 0


async def join_departments(
    client: discord.client,
    message: discord.message,
    args
):

    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author

    # Limit the number of bulk arguments to prevent
    # channel spam.
    args = args[0:1]
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:

        # Pick out the department portion from the string.
        # If the string isn't valid, skip it and move on.
        matches = re.search("^[a-zA-Z]{2,6}$", arg)
        if matches is None:
            continue

        department = matches[0].upper()

        # Attempt to get the department category channel - 
        # if none exists, create one
        dep_channel = discord.utils.get(guild.channels, name=department.upper())
        if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
            dep_channel = await guild.create_category(department)

            # Add the necessary member permissions for PointyPal to access
            # this chat, and then hide it from everybody else.
            await dep_channel.set_permissions(client.user, view_channel=True)
            await dep_channel.set_permissions(guild.default_role, view_channel=False,
                                                                  read_messages=False)

        channels = [
            (department.lower(), discord.TextChannel),
            (f"{department.upper()} Study Room", discord.VoiceChannel)
        ]

        for c in channels:
            result = await create_and_join_class(c[0], member, c[1], dep_channel)
            num_changes = num_changes + 1 if result else num_changes

    return num_changes > 0


async def remove_departments(
    client: discord.client,
    message: discord.message,
    args
):

    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:

        # Pick out the department portion from the string.
        # If the string isn't valid, skip it and move on.
        matches = re.search("^[a-zA-Z]{2,6}$", arg)
        if matches is None:
            continue

        department = matches[0].upper()

        dep_channel = discord.utils.get(guild.channels, name=department.upper())
        if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
            continue

        await dep_channel.set_permissions(member, view_channel=False,
                                                  read_messages=False)
        for ch in dep_channel.channels:
            await ch.set_permissions(member, view_channel=False,
                                             read_messages=False)
            num_changes += 1

    return num_changes > 0


async def place_in_classes(
    client: discord.client,
    message: discord.message,
    args
):

    # If there's not at least a user and a single class, return False
    if len(args) < 2:
        return False

    # If the message author doesn't have admin-y permissions, return False
    guild: discord.Guild = message.channel.guild
    if not verify_admin(guild, message.author):
        return False

    # If the second arg is a user, grab the ID.
    # If there isn't a match, return False.
    matches = re.search("[0-9]+", args[0])
    if matches is None:
        return False
    member_id = matches[0]

    member: discord.Member = guild.get_member(int(member_id))
    if member is None:
        return False

    # Once all the verifications have passed, add the target user
    # to all classes provided.
    num_changes = 0
    for arg in args[1:]:
        result = await join_class(client, guild, member, arg)
        num_changes = num_changes + 1 if result else num_changes

    return num_changes > 0

async def place_in_departments(
    client: discord.client,
    message: discord.message,
    args
):

    # If there's not at least a user and a single class, return False
    if len(args) < 2:
        return False

    # If the message author doesn't have admin-y permissions, return False
    guild: discord.Guild = message.channel.guild
    if not verify_admin(guild, message.author):
        return False

    # If the second arg is a user, grab the ID.
    # If there isn't a match, return False.
    matches = re.search("[0-9]+", args[0])
    if matches is None:
        return False
    member_id = matches[0]

    member: discord.Member = guild.get_member(int(member_id))
    if member is None:
        return False

    # Once all the verifications have passed, add the target user
    # to all classes provided.
    result = await join_departments(client, message, args[1:])

    return result

async def delete_departments(
    client: discord.client,
    message: discord.message,
    args
):

    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author

    # Verify that the caller is authorized to delete channels
    if not verify_admin(guild, message.author):
        return False
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:

        # Pick out the department portion from the string.
        # If the string isn't valid, skip it and move on.
        matches = re.search("^[a-zA-Z]{2,6}$", arg)
        if matches is None:
            continue

        department = matches[0].upper()

        dep_channel = discord.utils.get(guild.channels, name=department.upper())
        if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
            continue

        for ch in dep_channel.channels:
            await ch.delete(reason=f"PointyPal cleaning done by"
                                   f"{message.author.display_name}")
            num_changes += 1
        await dep_channel.delete(reason=f"PointyPal cleaning done by"
                                        f"{message.author.display_name}")
        num_changes += 1

    return num_changes > 0


async def delete_classes(
    client: discord.client,
    message: discord.message,
    args
):

    # Snag the guild and member from the message.
    guild: discord.Guild = message.guild
    member:  discord.Member  = message.author

    # Verify that the caller is authorized to delete channels
    if not verify_admin(guild, message.author):
        return False
    
    # Keep track of the # of changes made. If no changes
    # were made, return false to let the program know
    # that the command failed altogether.
    num_changes = 0
    for arg in args:

        # Verify the class name and snag the department
        name, department = verify_class(arg)

        if name is None:
            continue

        # Attempt to get the department category channel - if none exists, return False.
        dep_channel = discord.utils.get(guild.channels, name=department.upper())
        if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
            continue

        # Attempt to get the channel - if none exists, return False.
        target_channel: discord.GuildChannel = discord.utils.get(
            dep_channel.channels, name=name.lower()
        )

        if target_channel is None:
            continue

        await target_channel.delete(reason=f"PointyPal cleaning done by"
                                           f"{message.author.display_name}")
        num_changes += 1

    return num_changes > 0


async def post_greeting(
    client: discord.client,
    message: discord.message,
    args
):

    # Verify that the caller is authorized to delete channels
    if not verify_admin(message.channel.guild, message.author):
        return False

    await plugs.post_greeting(client, message.channel)
    return True


async def clean_manager(
    client: discord.client,
    message: discord.message,
    args
):

    # Verify that the caller is authorized to delete channels
    if not verify_admin(message.channel.guild, message.author):
        return False

    channel: discord.TextChannel = message.channel

    new_channel = await channel.clone(
        name=channel.name,
        reason="New channel clean by "
              f"{message.author.display_name}"
        )

    await channel.delete(
        reason="New channel clean by "
              f"{message.author.display_name}"
    )

    await plugs.post_greeting(client, new_channel)
    
    return True


command_lookup = {
    "join-class": join_classes,
    "join-classes": join_classes,

    "join-department": join_departments,
    "join-departments": join_departments,

    "add-class": join_classes,
    "add-classes": join_classes,

    "add-department": join_departments,
    "add-departments": join_departments,

    "drop-class": remove_classes,
    "drop-classes": remove_classes,

    "drop-department": remove_departments,
    "drop-departments": remove_departments,

    "place-in-class": place_in_classes,
    "place-in-classes": place_in_classes,

    "place-in-department": place_in_departments,
    "place-in-department": place_in_departments,

    "delete-class": delete_classes,
    "delete-classes": delete_classes,

    "delete-department": delete_departments,
    "delete-departments": delete_departments,

    "post-greeting": post_greeting,

    "clean-manager": clean_manager,
}

async def run_command(
    client: discord.client,
    message: discord.message,
    tokens
):
        
    print(f"Command logged from {message.channel.guild.name}: {message.content}")

    if len(tokens) <= 1:
        return False

    com_string = tokens[1]

    if not com_string in command_lookup.keys():
        return False

    com_func = command_lookup[com_string]

    result = await com_func(client, message, tokens[2:])

    return result