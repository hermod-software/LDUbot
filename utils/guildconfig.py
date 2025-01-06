import discord
import os
import yaml
import copy

from utils.shared import client

class GuildConfig:
    """
    class to handle configuration files of a guild\n
    get the config object for a guild with GuildConfig.guilds[guildid]

    methods:
    save(): save the config to file
    load(): load the config from file
    reload(): save and reload the config
    modify(key, value): modify a key in the config
    setreward(level, role): set a role to be given at a certain level
    delreward(level): remove a role from the rewards list
    """
    # guilds = {}
    DEFAULTCONFIG = {
        "base": 50,                 # base points needed to reach level 1
        "growth_rate": 1.2,         # growth rate of points needed to reach next level (1.2 means 20% more points needed)
        "point_range_upper": 5,     # maximum points that can be earned in a single message (randomised)
        "point_range_lower": 1,     # minimum points that can be earned in a single message (randomised)
        "roles": {                  # role awards to be given at certain levels
            # level: roleid
        }                 
    }
    VALIDKEYS = DEFAULTCONFIG.keys()    # list of valid keys for the config

    def __init__(self, guildid: int):
        guild = discord.utils.get(client.guilds, id=guildid)    # get the guild object from the client
        if guild is None:                                       # if the guild doesn't exist, don't register ourselves
            print(f"i have no access to guild {guildid}, skipping config object creation")
            return                                              # (the function will end here if the guild doesn't exist)

        self.guildid = guild.id
        self.guildname = guild.name

        self.config = self.load()                                   # load the config from file
        if self.config is None:                                     # if the config doesn't exist, create a new default config
            self.config = copy.deepcopy(GuildConfig.DEFAULTCONFIG)  # copy the default config into the new config
            self.save()                                             # save the new config to file 
            self.config = self.load()                               # load the new config again for good measure

        GuildConfig.guilds[self.guildid] = self
    
    def save(self):
        """
        save the config to file\n
        filepath is ./savedata/configs/{guildid}.yaml
        """
        try:
            if not os.path.exists("./savedata/configs"):
                os.makedirs("./savedata/configs")
            with open(f"./savedata/configs/{self.guildid}.yaml", "w") as file:
                yaml.dump(self.config, file)
        except IOError:
            print(f"IOError: couldn't save config for guild {self.guildname} ({self.guildid})")
        except Exception as e:
            print(f"Error: couldn't save config for guild {self.guildname} ({self.guildid}): {e}")

    def load(self):
        """
        load the config from file\n
        filepath is ./savedata/configs/{guildid}.yaml\n
        returns the config as a dict, or None if the file doesn't exist
        """
        if not os.path.exists(f"./savedata/configs/{self.guildid}.yaml"):   # if the file doesn't exist return None
            return None
        with open(f"./savedata/configs/{self.guildid}.yaml", "r") as file:   # otherwise open the file
            config = yaml.safe_load(file)                                    # load & return the config
            return config
        
    def reload(self):
        """
        save and reload self.config
        """
        self.save()
        self.config = self.load()
        
    def modify(self, key: str, value):
        """modify a key in the config
        key: the key to modify
        value: the new value for the key"""

        if key not in GuildConfig.VALIDKEYS:    # if the key isn't valid, return False
            return False
        self.config[key] = value    # otherwise set the key to the new value
        self.reload()               # reload the config   
        return True                 # return True to indicate success
    
    def setreward(self, level: int, role: discord.Role):
        """
        set a role to be given at a certain level
        level: the level to give the role at
        roleid: the id of the role to give\n
        returns (True, "") if successful, (False, errormessage) if not
        """

        if role is None:
            return False, "role not found"
        if level < 1:
            return False, "level must be 1 or higher"
        
        if level in self.config["roles"]:                   # if the level is already in the config
            for key, value in self.config["roles"].items(): # find the level it's already set to
                if value == role.id:
                    return False, f"role {role.name} is already set to be given at level {key}"

                                                # if no errors occur:
        self.config["roles"][level] = role.id   # set the role to be given at the level
        self.reload()                           # reload the config
        return True, ""                         # return success with no error message
    
    def delreward(self, level:int):
        """
        remove a role from the rewards list
        level: the level to remove the reward for\n
        returns (True, "") if successful, (False, errormessage) if not
        """

        if level not in self.config["roles"]:
            return False, f"no reward at that level"
        
        del self.config["roles"][level]    # remove the role from the config