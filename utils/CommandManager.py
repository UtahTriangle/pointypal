import yaml
from dotmap import DotMap
from utils.ClassManager import ClassManager
from utils.GeneralCommands import GeneralCommands


class CommandManager:

    def __init__(self, client, config_path):

        config_path = config_path
        self.CONFIG: DotMap = None
        with open(config_path, 'r') as file:
            config_dict = yaml.load(file, Loader=yaml.FullLoader)
            self.CONFIG = DotMap(config_dict)

        self.client = client

        self.modules = {}

        # Construct class manager and keep it in the module dictionary
        self.modules["class_manager"] = ClassManager(
            self.client,
            f"configs/{self.CONFIG.modules.class_manager.config_path}",
        )

        self.modules["general_commands"] = GeneralCommands(
            self.client,
            f"configs/{self.CONFIG.modules.general_commands.config_path}",
        )

        self.ALIASES = self.build_alias_map()

    async def run(self, message):

        tokens = message.content.split(" ")[1:]

        # If the command wasn't passed any tokens, assume it was a request for
        # help
        if len(tokens) == 0:
            tokens.append("help")

        # If the command doesn't exist in the alias dictionary, provide help
        if not tokens[0] in self.ALIASES.keys():
            tokens[0] = "help"

        moduleName, command = self.ALIASES[tokens[0]]

        module = self.modules[moduleName]

        missing_perms = self.check_permissions(
            message.channel.guild,
            message.channel,
            message.author,
            module.CONFIG.commands[command]
        )

        if len(missing_perms) > 0:
            error_string = (
                f"Please make sure users have the necessary permissions "
                f"to use `{command}`: \n```"
            )

            for actor, scope, perm in missing_perms:
                error_string += f"\n{actor}, {perm}"

            error_string += "\n```"

            await message.reply(error_string)
            return

        # Execute command function

        try:
            await getattr(module, command)(
                message,
                tokens[1:],
            )
        except Exception as e:
            await message.reply(f"It looks like there was an issue with your request. {str(e)}")

        return

    def check_permissions(
        self,
        guild,
        channel,
        member,
        command_config
    ):
        
        actors = {
            "bot":  guild.get_member(self.client.user.id),
            "user": member
        }

        # TODO: Check permissions on a per-channel basis
        scopes = {
            "guild": guild,
#            "channel": channel
        }

        reqs = []
        for actor in actors.keys():
            permissions = command_config[f"{actor}_permissions"]

            for scope in scopes.keys():
                perm_list = permissions[scope]
                for perm in perm_list:
                    reqs.append((actor, scope, perm))

        missing = []
        for actor, scope, perm in reqs:
            actor = actors[actor]
            permissions = getattr(actor, f"{scope}_permissions")
            has_permission = getattr(permissions, perm)
            if not has_permission:
                missing.append((actor, scope, perm))

        return missing


    def is_command(self, message):

        bot_mentioned = (
            (message.content.startswith(self.CONFIG["prefix"]))
         or (message.content.startswith(f"<@!{self.client.user.id}>")) # Desktop
         or (message.content.startswith(f"<@{ self.client.user.id}>")) # Mobile
        )

        return bot_mentioned
        
    def build_alias_map(self):
        
        modules = self.CONFIG.modules.toDict()

        alias_map = {}
        
        for name, contents in modules.items():
            config_path = f"configs/{contents['config_path']}"
            module_config = None
            with open(config_path, 'r') as file:
                module_config = yaml.load(file, Loader=yaml.FullLoader)

            commands = module_config["commands"]

            for command, options in commands.items():

                aliases = options["aliases"]
                
                for alias in aliases:

                    alias_map[alias] = (name, command)

        return alias_map