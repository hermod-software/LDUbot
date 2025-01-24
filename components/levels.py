import discord
from discord.ext import commands, tasks
import json
import yaml
import random
import math
import os
import copy
import unicodedata

import shared.utils.graphic as graphic
from shared.defs.shared import client

class ConfigHandler:
    guilds = {}
    defaultconfig = {
        "base": 50,
        "growth_rate": 1.2,
        "point_range_upper": 5,
        "point_range_lower": 1,
        "roles": {}
    }

    def __init__(self, guild: discord.Guild):
        self.guildid = guild.id
        self.guildname = guild.name
        self.config = {}

        self.config = self.load()
        print(f"config for {self.guildid} ({self.guildname}) loaded:\n{self.config}")
        
        if self.guildid not in ConfigHandler.guilds:
            ConfigHandler.guilds[self.guildid] = self


    def save(self):
        dir_path = f"savedata/{self.guildid}"
        file_path = f"{dir_path}/config.yml"

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        try:
            with open(file_path, "w") as file:
                yaml.dump(self.config, file)
        except Exception as e:
            print(f"Failed to save config for guild {self.guildid}: {e}")

    def load(self):
        if not os.path.exists(f"savedata/{self.guildid}/config.yml"):
            self.config = copy.deepcopy(ConfigHandler.defaultconfig)
            self.save()
        else:
            with open(f"savedata/{self.guildid}/config.yml", "r") as file:
                self.config = yaml.safe_load(file)
        return self.config

    def setconfig(self, key, value):
        self.config[key] = value
        self.save()
        return self.config[key]

    def getconfig(self, key: str):
        """ get a config value by key """
        return self.config.get(key, None)

    def delconfig(self, key):
        if key in self.config:
            del self.config[key]
            self.save()
            self.load()

    def set_level_role(self, level: int, role: discord.Role):
        roleid = role.id
        self.config["roles"][level] = roleid
        self.save()
        return self.config["roles"][level]
    
    def del_level_role(self, level: int):
        if level in self.config["roles"]:
            del self.config["roles"][level]
            self.save()
            self.load()


pointspath = "savedata/points.json"

@discord.app_commands.default_permissions(manage_roles=True)
class GuildConfig(commands.GroupCog, group_name="config"):
    def __init__(self, client: commands.Bot):
        self.client = client

        for guild in self.client.guilds:
            if guild.id not in ConfigHandler.guilds:
                ConfigHandler(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in ConfigHandler.guilds:
            ConfigHandler(guild)
        print(f"Joined guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in ConfigHandler.guilds:
            del ConfigHandler.guilds[guild.id]
        print(f"Left guild: {guild.name} (ID: {guild.id})")

    @discord.app_commands.command(
        name="set_base", 
        description=f"set the amount of points to get from level 0 to level 1 (default: {ConfigHandler.defaultconfig['base']})"
    )
    @commands.has_permissions(manage_guild=True)
    async def set_base(self, interaction: discord.Interaction, base: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("base", base)
        await interaction.response.send_message(f"set base points amount to {base}")

    @discord.app_commands.command(name="get_base", description="get the amount of points to get from level 0 to level 1")
    async def get_base(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        base = guild_config.getconfig("base")
        await interaction.response.send_message(f"base points amount is {base}")

    @discord.app_commands.command(name="set_growth_rate", description=f"set the growth rate for points (default: {ConfigHandler.defaultconfig['growth_rate']})")
    @commands.has_permissions(manage_guild=True)
    async def set_growth_rate(self, interaction: discord.Interaction, rate: float):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("growth_rate", rate)
        await interaction.response.send_message(f"set growth rate to {rate}")

    @discord.app_commands.command(name="get_growth_rate", description="get the growth rate for points")
    @commands.has_permissions(manage_guild=True)
    async def get_growth_rate(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        rate = guild_config.getconfig("growth_rate")
        await interaction.response.send_message(f"growth rate is {rate}")

    @discord.app_commands.command(name="set_point_range", description=f"set the upper and lower bound for points awarded (default: {ConfigHandler.defaultconfig['point_range_lower']} - {ConfigHandler.defaultconfig['point_range_upper']})")
    @commands.has_permissions(manage_guild=True)
    async def set_point_range(self, interaction: discord.Interaction, lower: int, upper: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("point_range_lower", lower)
        guild_config.setconfig("point_range_upper", upper)
        await interaction.response.send_message(f"set point range to {lower} - {upper}")

    @discord.app_commands.command(name="get_point_range", description="get the upper and lower bound for points awarded")
    @commands.has_permissions(manage_guild=True)
    async def get_point_range(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        lower = guild_config.getconfig("point_range_lower")
        upper = guild_config.getconfig("point_range_upper")
        await interaction.response.send_message(f"point range is {lower} - {upper}")

    @discord.app_commands.command(name="reset_config", description="reset the configuration for this guild")
    @discord.app_commands.default_permissions(manage_roles=True)
    async def reset_config(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.load()
        await interaction.response.send_message("configuration reset")

    @discord.app_commands.command(name="get_config", description="get the configuration for this guild")
    async def get_config(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        
        config = copy.deepcopy(guild_config.config)
        roles = config["roles"]
        upd_roles = {}

        if roles != {}:
            for level, role in roles.items():
                role = interaction.guild.get_role(role)
                upd_roles[level] = role.name
        else:
            upd_roles = "No roles set (use /config set_level_role <level> <role> to set a role)"

        config["roles"] = upd_roles
        
        yaml_config = yaml.dump(config)


        await interaction.response.send_message(f"configuration for {interaction.guild.name}:\n```yaml\n{yaml_config}```")

    @discord.app_commands.command(name="set_level_role", description="set a role to be awarded at a certain level")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def set_level_role(self, interaction: discord.Interaction, level: int, role: discord.Role):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.set_level_role(level, role)
        await interaction.response.send_message(f"role {role.name} set to be awarded at level {level}")

    @discord.app_commands.command(name="del_level_role", description="remove a role from being awarded at a certain level")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def del_level_role(self, interaction: discord.Interaction, level: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        role_name = guild_config.config["roles"].get(level, "role not found")
        guild_config.del_level_role(level)
        await interaction.response.send_message(f"role {role_name} removed from level {level}")


async def setup(client: commands.Bot):
    await client.add_cog(GuildConfig(client))


class Levels(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.points = self.load_points()
        self.save_task.start()
        self.recentmessages = {}
        self.default_growth_rate = 1.2
        self.default_point_range_upper = 5
        self.default_point_range_lower = 1
        self.emojis = {
            0: ":first_place:",
            1: ":second_place:",
            2: ":third_place:",
            3: ":four:",
            4: ":five:",
            5: ":six:",
            6: ":seven:",
            7: ":eight:",
            8: ":nine:",
            9: ":keycap_ten:"
        }
        self.otheremoji = ":speech_balloon:"

    def get_level_from_points(self, points, guild_id):
        try:
            guild_id = int(guild_id)
        except ValueError:
            print(f"Error converting guild_id {guild_id} to int")
            return 0, 0

        if guild_id not in ConfigHandler.guilds:
            print(f"Guild ID {guild_id} not found in ConfigHandler.guilds")
            return 0, 0

        guild = ConfigHandler.guilds[guild_id]
        base = guild.getconfig("base")
        growth_rate = guild.getconfig("growth_rate")
        level = 0
        total_required = base                       # points required for the current level
        cumulative_points = 0                       # total points required to reach the current level

        while points >= total_required:
            cumulative_points += total_required     # add points needed for the current level
            points -= total_required                # deduct points for the current level
            level += 1                              # increment level
            total_required = math.floor(base * (growth_rate ** level))  # points needed for the next level

        # calculate points remaining to reach the next level
        remaining_points = total_required - points

        # debug output to trace calculations
        #print(f"Level: {level}, Points Remaining: {points} Next Level Threshold: {total_required}, Remaining Points to Next Level: {remaining_points}")

        return level, remaining_points

    def get_points_from_level(self, level, guild_id):
        try:
            guild_id = int(guild_id)
        except ValueError:
            print(f"Error converting guild_id {guild_id} to int")
            return 0

        if guild_id not in ConfigHandler.guilds:
            print(f"Guild ID {guild_id} not found in ConfigHandler.guilds")
            return 0

        guild = ConfigHandler.guilds[guild_id]
        base = guild.getconfig("base")
        growth_rate = guild.getconfig("growth_rate")
        points = 0
        for i in range(level):
            points += math.floor(base * (growth_rate ** i))
        return points

        

    def get_points(self, guild, user):
        return self.points.get(guild, {}).get(user, 0)

    def add_recent_sender(self, guild, user):
        if guild not in self.recentmessages.keys():
            self.recentmessages[guild] = []
        if user not in self.recentmessages[guild]:
            self.recentmessages[guild].append(user)

    def is_recent_sender(self, guild, user):
        if guild not in self.recentmessages.keys():
            return False
        if user in self.recentmessages[guild]:
            return True
        return False
    
    def award_points(self, guild, user, points):
        if guild not in self.points.keys():
            self.points[guild] = {}
        if user not in self.points[guild]:
            self.points[guild][user] = 0
        self.points[guild][user] += points

    def load_points(self):
        if os.path.exists(pointspath):
            try:
                with open(pointspath, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Error loading points.json: resetting data.")
                return {}
        return {}

    def save_points(self):
        with open(pointspath, "w") as file:
            json.dump(self.points, file, indent=2)
            self.recentmessages = {}

    def reset_guild_points(self, guild):
        self.points[guild] = {}
        self.save_points()

    async def rolelevelpass(self, guild: discord.Guild, member: discord.Member, level):
        print(f"rolelevelpass called for {member.name} in {guild.name}")
        async def giverole(member, role, guild):
            if role in member.roles: # don't give the role if the user already has it
                return
            try:
                await member.add_roles(role)
                print(f"added role {role.name} to {member.name}")
                try:
                    await member.send(f"you have been awarded the role {role.name} in {guild.name} for reaching level {level}")
                except Exception as e:
                    print(f"could not send DM to {member.name}: {e}")
            except discord.Forbidden:
                print(f"tried to give {role.name} to {member.name} but have no permission to add roles in {guild.name}")

        print(f"rolelevelpass called for {member.name} in {guild.name}")
        guildid = guild.id
        guildname = guild.name
        guildconfig = ConfigHandler.guilds[guildid]
        roles = guildconfig.getconfig("roles")
        for level in range(0, level + 1):
            role = roles.get(level, None)
            if role is not None:
                role = guild.get_role(role)
                if role is not None:
                    await giverole(member, role, guild)
                    
                else:
                    print(f"role for level {level} not found in {guildname}")
            else:
                pass
            
            
                

    @tasks.loop(seconds=30)  # save every 30 seconds
    async def save_task(self):
        self.save_points()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levels cog ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"message received in {message.guild.name} from {message.author.name}")
        if message.author.bot:
            return
        guildconfig = ConfigHandler.guilds[message.guild.id]
        guildid = str(message.guild.id)
        if guildconfig is None:
            print(f"ConfigHandler.guilds[{guildid}] is None!")
            point_range_lower = self.default_point_range_lower
            point_range_upper = self.default_point_range_upper
        else:
            point_range_lower = guildconfig.getconfig("point_range_lower")
            point_range_upper = guildconfig.getconfig("point_range_upper")


        random.seed(message.id)
        award = random.randint(point_range_lower, point_range_upper)
        if message.author.bot or message.guild is None:
            return
        guild_id = str(message.guild.id)
        author_id = str(message.author.id)
        guild_name = message.guild.name

        if self.is_recent_sender(guild_id, author_id):
            stamp = f"{guild_name}: recent sender {message.author.name} not awarded points"
            #print(stamp)
            return
        else:
            self.add_recent_sender(guild_id, author_id)                             # add the user to the recent sender list

            userpoints = self.points.get(guild_id, {}).get(author_id, 0)

            userlevel = self.get_level_from_points(userpoints, guild_id)[0]

            self.award_points(guild_id, author_id, award)

            newuserlevel = self.get_level_from_points(userpoints, guild_id)[0]

        await self.rolelevelpass(message.guild, message.author, newuserlevel) # check if the user has reached a new level and award the role if they have
            #print(stamp)
        
    async def user_in_guild(self, guild, user_id):
        if type(user_id) is not int:
            try:
                user_id = int(user_id)
            except ValueError:
                print(f"Error converting user_id {user_id} to int")
                return False
        try:
            user = await guild.fetch_member(user_id)
            if user is None:
                raise discord.NotFound
            return True # only reached if the user is found and not None
        except discord.NotFound:
            print(f"user {user_id} not found")
            return False

    async def get_leaderboard_position(self, guild, user_id):
        guild_id = str(guild.id)
        user_id = str(user_id)
        guild_points = self.points.get(guild_id, None)
        if guild_points is None:
            return None # no points for the guild
        if not await self.user_in_guild(guild, user_id):
            return None # user not in the guild
        if not user_id in guild_points:
            return None # user has no points in the guild
        
        sorted_points = sorted(guild_points, key=lambda k: guild_points[k], reverse=True) # sort the users by points within the guild
        user_index = sorted_points.index(user_id) # get the index of the user in the sorted list
        return user_index # return the index
        

    @discord.app_commands.command(name="rank", description="fetch the level of a user")
    async def rank(self, interaction: discord.Interaction, user: discord.Member=None):
        targetisinvoker = False

        if user is None or user == interaction.user:
            targetisinvoker = True
            user = interaction.user
        print(f"{interaction.user.name} invoked get_level on {user.name}")
        if interaction.guild is None:
            await interaction.response.send_message("this command must be used in a server!")
            return
        
        guild_id = str(interaction.guild.id)
        displayname = user.display_name
        displayname = unicodedata.normalize("NFKD", displayname)                # normalise the display name
        user_id = str(user.id)
        points = self.points.get(guild_id, {}).get(user_id, 0)
        level, tonextlevel = self.get_level_from_points(points, guild_id)
        pointsthislevel = points - self.get_points_from_level(level, guild_id)
        percent = (pointsthislevel / (pointsthislevel + tonextlevel)) * 100
        index = await self.get_leaderboard_position(interaction.guild, user_id)
        
        entry = [displayname, user.name, level, points, percent, tonextlevel, index]

        for i, item in enumerate(entry):
            if item is None:
                entry[i] = "X"

        entry = tuple(entry)
        #print(f"rank entry:\ndisplayname: {displayname}\nusername: {user.name}\nlevel: {level}\npoints: {points}\npercentage: {percent}\ntonextlevel: {tonextlevel}\nindex: {index}")
        userpath = graphic.user_level_image(entry)

        try:
            with open(userpath, "rb") as file:
                await interaction.response.send_message(file=discord.File(file))
        except FileNotFoundError:
            await interaction.response.send_message("we lost track of the user level image, please try again")

    @discord.app_commands.command(name="add_points", description="add points to a user")
    @discord.app_commands.default_permissions(manage_roles=True)
    async def add_points(self, interaction: discord.Interaction, user: discord.Member, points: int):
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        self.award_points(guild_id, user_id, points)
        user_points = self.points.get(guild_id, {}).get(user_id, 0)
        user_level = self.get_level_from_points(user_points, guild_id)[0]
        await self.rolelevelpass(interaction.guild, user, user_level)
        await interaction.response.send_message(f"added {points} points to {user.name}")



    @discord.app_commands.command(name="leaderboard", description="fetch the top users by points")
    async def leaderboard(self, interaction: discord.Interaction, page: int=1):
        if interaction.guild is None:
            await interaction.response.send_message("this command must be used in a server!")
            return

        guild_id = str(interaction.guild.id)        # get the guild ID
        guild_name = interaction.guild.name         # get the guild name
        points = self.points.get(guild_id, {})      # get the points for the guild
        sortedpoints = sorted(points.items(), key=lambda x: x[1], reverse=True)  # sort users by points
        leaderboard = [] # list to store the leaderboard

        for i, (user_id, user_points) in enumerate(sortedpoints): # iterate over the sorted points list
            username = interaction.guild.get_member(int(user_id)) # get the user object from the user ID
            if username is None:                            # if there is no user for some reason
                username = "(no user)"                      # set the username to an error message
                displayname = username    
                continue # don't add the user to the leaderboard
            if not isinstance(username, str):       # if the user is not a string (i.e. it's a user object and not an error message or something)
                displayname = username.display_name # get the user's display name
                username = username.name            # get the user's username

            level, tonextlevel = self.get_level_from_points(user_points, guild_id)  # get the user's level and points to next level
            points_this_level = user_points - self.get_points_from_level(level, guild_id) # get the points the user has this level
            percentage = (points_this_level / (points_this_level + tonextlevel)) * 100 # calculate the percentage to next level
            displayname = unicodedata.normalize("NFKD", displayname)                # normalise the display name

            entry = (str(displayname), str(username), int(level), int(user_points), int(percentage), int(tonextlevel))   # create a tuple with the user's name, level, and percentage to next level
            #print(f"leaderboard entry:\ndisplayname: {displayname}\nusername: {username}\nlevel: {level}\npoints: {user_points}\npercentage: {percentage}\ntonextlevel: {tonextlevel}")
            leaderboard.append(entry)               # add the tuple to the leaderboard
            
        startindex = (page - 1) * 10
        endindex = page * 10
        truncleaderboard = leaderboard[startindex:endindex] # truncate the leaderboard to the number of pages requested
        maxpages = math.ceil(len(leaderboard) / 10)
        imagepath = graphic.leaderboard_image(truncleaderboard, guild_name, page, maxpages) # create the leaderboard image

        try:
            with open(imagepath, "rb") as file:
                await interaction.response.send_message(file=discord.File(file))
        except FileNotFoundError:
            await interaction.response.send_message("we lost track of the leaderboard image, please try again")
        

    @discord.app_commands.command(name="reset_points", description="reset the points for the whole server")
    @discord.app_commands.default_permissions(manage_roles=True)
    async def reset_points(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("this command must be used in a server!")
            return
        guild_id = str(interaction.guild.id)
        self.reset_guild_points(guild_id)
        await interaction.response.send_message(f"points for guild {interaction.guild.name} reset")

        
async def setup(client):
    levels_cog = Levels(client)
    guild_config_cog = GuildConfig(client)

    await client.add_cog(levels_cog)
    await client.add_cog(guild_config_cog)

    print('Cogs "levels" and "guild_config" loaded')

