import discord
from discord.ext import commands, tasks
import json
import random
import math
import os

class Levels(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.points = self.load_points()
        self.save_task.start()
        self.recentmessages = {}
        self.growth_rate = 1.2
        self.point_range_upper = 5
        self.point_range_lower = 1
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

    def get_level_from_points(self, points):
        level = 0
        required = 50 # points required for level 1
        counted = 0

        while points >= required:
            counted += 1
            if counted == required:
                level += 1
                required = math.floor(required * self.growth_rate)
                counted = 0  

        remaining_points = required - counted  

        return level, remaining_points
        

        

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
        if os.path.exists("points.json"):
            try:
                with open("points.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Error loading points.json: resetting data.")
                return {}
        return {}

    def save_points(self):
        with open("points.json", "w") as file:
            json.dump(self.points, file, indent=2)
            self.recentmessages = {}

    @tasks.loop(seconds=30)  # save every 30 seconds
    async def save_task(self):
        self.save_points()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levels cog ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        
        random.seed(message.id)
        award = random.randint(self.point_range_lower, self.point_range_upper)
        if message.author.bot or message.guild is None:
            return
        guild_id = str(message.guild.id)
        author_id = str(message.author.id)
        guild_name = message.guild.name

        if self.is_recent_sender(guild_id, author_id):
            stamp = f"{guild_name}: recent sender {message.author.name} not awarded points"
            print(stamp)
            return
        else:
            self.add_recent_sender(guild_id, author_id)
            stamp = f"{guild_name}: awarding {message.author.name} {award} points"
            self.award_points(guild_id, author_id, award)
            print(stamp)
        

    @discord.app_commands.command(name="get_level", description="fetch the level of a user")
    async def get_points(self, interaction: discord.Interaction, user: discord.Member=None):
        targetisinvoker = False

        if user is None or user == interaction.user:
            targetisinvoker = True
            user = interaction.user
        print(f"{interaction.user.name} invoked get_level on {user.name}")
        if interaction.guild is None:
            await interaction.response.send_message("this command must be used in a server!")
            return
        
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        points = self.points.get(guild_id, {}).get(user_id, 0)
        level, tonextlevel = self.get_level_from_points(points)
        stamp = f"level {level} ({points} points) with {tonextlevel - points} points until next level"
        if targetisinvoker:
            await interaction.response.send_message(f"you are {stamp}")
        else:
            await interaction.response.send_message(f"{user.mention} is {stamp}")



    @discord.app_commands.command(name="get_leaderboard", description="fetch the top users by points")
    async def get_leaderboard(self, interaction: discord.Interaction, pages: int=1):
        if interaction.guild is None:
            await interaction.response.send_message("this command must be used in a server!")
            return
        guild_id = str(interaction.guild.id)
        guild_name = interaction.guild.name
        points = self.points.get(guild_id, {})
        sortedpoints = sorted(points.items(), key=lambda x: x[1], reverse=True) # sort users by points
        leaderboard = [] #
        for i, (user_id, user_points) in enumerate(sortedpoints):
            username = interaction.guild.get_member(int(user_id))
            if username is None:
                username = "could not resolve username"
            username = username.name
            level, tonextlevel = self.get_level_from_points(user_points)
            emoji = self.emojis.get(i, "")
            leaderboard.append(f"{emoji} `[Level {level}]` **{username}** `{user_points} points, {tonextlevel - user_points} to next level`")
        header = f"# `Leaderboard for {guild_name}`"
        leaderboard = leaderboard[:(pages * 10)]
        
        leaderboard = '\n'.join(leaderboard)
        leaderboard = header + '\n' + leaderboard
        
        leaderboard = leaderboard + f"\n-# (max items: {pages * 10})"
        await interaction.response.send_message(leaderboard)

        
async def setup(client):
    await client.add_cog(Levels(client))
    print('Cog "levels" loaded')
