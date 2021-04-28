import yaml
from dotmap import DotMap
from utils.ClassManager import ClassManager

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
            self.CONFIG.modules.class_manager.config,
            self.CONFIG.modules.class_manager.channel
        )

        self.ALIASES = self.build_alias_map()

    def run(self, message)

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