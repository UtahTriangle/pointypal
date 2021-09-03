import discord
from dotmap import DotMap
import regex as re
import yaml
import time

class ClassManager:

    def __init__(self, client, config_path):

        self.client = client
        self.CONFIG = None
        with open(config_path, 'r') as file:
            config_dict = yaml.load(file, Loader=yaml.FullLoader)
            self.CONFIG = DotMap(config_dict)

    
    async def remove_classes(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """
        # Snag the guild and member from the message.
        guild: discord.Guild = message.guild
        member:  discord.Member  = message.author
        
        # Keep track of the # of changes made. If no changes
        # were made, return false to let the program know
        # that the command failed altogether.
        for arg in args:
            result = await self.leave_and_clean_class(arg, member, guild)

        return 


    async def join_departments(
        self,
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
        for arg in args:

            # Pick out the department portion from the string.
            # If the string isn't valid, skip it and move on.
            matches = re.search(self.CONFIG.department_regex, arg)
            if matches is None:
                raise Exception(f"`{arg[:10]}` wasn't a valid department code.")

            department = matches[0].upper()

            # Attempt to get the department category channel - 
            # if none exists, create one
            dep_channel = discord.utils.get(guild.channels, name=department.upper())
            if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
                dep_channel = await guild.create_category(department)

                # Add the necessary member permissions for PointyPal to access
                # this chat, and then hide it from everybody else.
                await dep_channel.set_permissions(self.client.user, view_channel=True)
                await dep_channel.set_permissions(guild.default_role, view_channel=False,
                                                                    read_messages=False)

            channels = [
                (department.lower(), discord.TextChannel),
                (f"{department.upper()} Study Room", discord.VoiceChannel)
            ]

            for c in channels:
                result = await self.create_and_join_class(c[0], member, c[1], dep_channel)

        return 


    async def remove_departments(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

        # Snag the guild and member from the message.
        guild: discord.Guild = message.guild
        member:  discord.Member  = message.author
        
        # Keep track of the # of changes made. If no changes
        # were made, return false to let the program know
        # that the command failed altogether.
        for arg in args:

            # Pick out the department portion from the string.
            # If the string isn't valid, skip it and move on.
            matches = re.search(self.CONFIG.department_regex, arg)
            if matches is None:
                raise Exception(f"`{arg[:10]}` wasn't a valid department code.")

            department = matches[0].upper()

            dep_channel = discord.utils.get(guild.channels, name=department.upper())
            if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
                continue

            await dep_channel.set_permissions(member, view_channel=False,
                                                      read_messages=False)
            for ch in dep_channel.channels:
                await ch.set_permissions(member, view_channel=False,
                                                 read_messages=False)

        return 


    async def place_in_classes(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

        # If there's not at least a user and a single class, return False
        if len(args) < 2:
            raise Exception("Not enough information was provided for the command.")

        # If the message author doesn't have admin-y permissions, return False
        guild: discord.Guild = message.channel.guild

        # If the second arg is a user, grab the ID.
        # If there isn't a match, return False.
        matches = re.search("[0-9]+", args[0])
        if matches is None:
            raise Exception(f"The requested user `{args[0]}` doesn't exist.")
        member_id = matches[0]

        member: discord.Member = guild.get_member(int(member_id))
        if member is None:
            raise Exception(f"The requested user `{args[0]}` doesn't exist.")

        # Once all the verifications have passed, add the target user
        # to all classes provided.
        for arg in args[1:]:
            result = await self.join_class(guild, member, arg)

        return 

    async def place_in_departments(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

        # If there's not at least a user and a single class, return False
        if len(args) < 2:
            raise Exception("Not enough information was provided for the command.")

        # If the message author doesn't have admin-y permissions, return False
        guild: discord.Guild = message.channel.guild

        # If the second arg is a user, grab the ID.
        # If there isn't a match, return False.
        matches = re.search("[0-9]+", args[0])
        if matches is None:
            raise Exception(f"The requested user `{args[0]}` is not a valid UserID")
        member_id = matches[0]

        member: discord.Member = guild.get_member(int(member_id))
        if member is None:
            raise Exception(f"The requested user `{args[0]}` doesn't exist.")

        # Once all the verifications have passed, add the target user
        # to all classes provided.
        await self.join_departments(self.client, message, args[1:])


    async def delete_departments(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

        # Snag the guild and member from the message.
        guild: discord.Guild = message.guild
        member:  discord.Member  = message.author
        
        # Keep track of the # of changes made. If no changes
        # were made, return false to let the program know
        # that the command failed altogether.
        for arg in args:

            # Pick out the department portion from the string.
            # If the string isn't valid, skip it and move on.
            matches = re.search(self.CONFIG.department_regex, arg)
            if matches is None:
                raise Exception(f"`{arg[:10]}` was not a valid department code.")


            department = matches[0].upper()

            dep_channel = discord.utils.get(guild.channels, name=department.upper())
            if (dep_channel is None) or (type(dep_channel) != discord.CategoryChannel):
                continue

            for ch in dep_channel.channels:
                await ch.delete(reason=f"PointyPal cleaning done by"
                                    f"{message.author.display_name}")
            await dep_channel.delete(reason=f"PointyPal cleaning done by"
                                            f"{message.author.display_name}")


    async def delete_classes(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

        # Snag the guild and member from the message.
        guild: discord.Guild = message.guild
        member:  discord.Member  = message.author
        
        # Keep track of the # of changes made. If no changes
        # were made, return false to let the program know
        # that the command failed altogether.
        for arg in args:

            # Verify the class name and snag the department
            name, department = self.verify_class(arg)

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


    async def clean_manager(
        self,
        message: discord.message,
        args
    ):
        """
        Command-facing method
        """

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
        
        return True


    async def create_and_join_class(
        self,
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
        self,
        name: str,
        member: discord.Member,
        guild: discord.Guild,
    ):
        
        # Verify the class name and snag the department
        name, department = self.verify_class(name)

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
        self,
        message: discord.Message,
        args
    ): 

        # Snag the guild and member from the message.
        guild: discord.Guild = message.guild
        member:  discord.Member  = message.author

        # Limit the number of bulk arguments to prevent
        # channel spam.
        args = args[: self.CONFIG.max_command_args]
        
        # Keep track of the # of changes made. If no changes
        # were made, return false to let the program know
        # that the command failed altogether.
        for arg in args:
            result = await self.join_class(guild, member, arg)

            # # delay to avoid message rate limiting
            # time.sleep(self.CONFIG.creation_delay)


    def verify_class(
        self,
        class_string: str
    ):

        matches = re.search(self.CONFIG.class_regex, class_string)

        # If there were no matches, raise exception
        if (matches is None) or (len(matches) != 1):
            raise Exception(f'`{class_string[:10]}` is not a valid course code.')

        # Pick out the department portion from the string
        regex_string = self.CONFIG.department_regex
        dept_search: str = re.search(regex_string, class_string)
        department = dept_search[0].upper()

        return class_string, department

    async def join_class(
        self,
        guild: discord.Guild,
        member: discord.Member,
        class_name: str
    ):

        # Verify the integrity of the class chat
        class_name, department = self.verify_class(class_name)

        # Find (or create) the the department category channel
        dep_channel = discord.utils.get(guild.channels, name=department)
        if  ((dep_channel is None) 
        or (not type(dep_channel) == discord.CategoryChannel)):

            dep_channel = await guild.create_category(department)

            # Add the necessary member permissions for PointyPal to access this chat
            # and then hide it from everybody else.
            await dep_channel.set_permissions(self.client.user, view_channel=True)
            await dep_channel.set_permissions(guild.default_role, view_channel=False,
                                                                read_messages=False)

        channels = [
            (department.lower(), discord.TextChannel),
            (class_name.lower(), discord.TextChannel),
            (f"{department.upper()} Study Room", discord.VoiceChannel)
        ]

        for c in channels:
            await self.create_and_join_class(c[0], member, c[1], dep_channel)

        return True