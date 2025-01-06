import discord
from discord.ext import commands, tasks
import json
import yaml
import random
import math
import os
import copy
import unicodedata

import graphic.levels as levels

pointspath = "savedata/points.json" 



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
                print(f"no role set for level {level} in {guildname}")
            
            
                

    @tasks.loop(seconds=30)  # save every 30 seconds
    async def save_task(self):
        self.save_points()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levels cog ready")

    @commands.Cog.listener()
    async def on_message(self, message):
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
            self.add_recent_sender(guild_id, author_id)

            stamp = f"{guild_name}: awarding {message.author.name} {award} points"

            userpoints = self.points.get(guild_id, {}).get(author_id, 0)

            userlevel = self.get_level_from_points(userpoints, guild_id)[0]

            self.award_points(guild_id, author_id, award)

            newuserlevel = self.get_level_from_points(userpoints, guild_id)[0]

            if userlevel != newuserlevel: # if the user levelled up
                self.rolelevelpass(message.guild, message.author, newuserlevel)
                stamp += f"user {message.author.name} levelled up to level {newuserlevel}"
            #print(stamp)
        

    def get_leaderboard_position(self, guild_id, user_id):
        points = self.points.get(guild_id, {})
        sortedpoints = sorted(points.items(), key=lambda x: x[1], reverse=True)
        for i, (id, _) in enumerate(sortedpoints):
            if id == user_id:
                return i
        return None

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
        index = self.get_leaderboard_position(guild_id, user_id)
        
        entry = [displayname, user.name, level, points, percent, tonextlevel, index]

        for i, item in enumerate(entry):
            if item is None:
                entry[i] = "X"

        entry = tuple(entry)
        #print(f"rank entry:\ndisplayname: {displayname}\nusername: {user.name}\nlevel: {level}\npoints: {points}\npercentage: {percent}\ntonextlevel: {tonextlevel}\nindex: {index}")
        userpath = levels.user_level_image(entry)

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
        imagepath = levels.leaderboard_image(truncleaderboard, guild_name, page, maxpages) # create the leaderboard image

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

