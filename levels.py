import discord
from discord.ext import commands, tasks
import json
import os

class Levels(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.points = self.load_points()

    def load_points(self):
        if os.path.exists("points.json"):
            try:
                with open("points.json", "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print("Error loading points.json, resetting data.")
                return {}
        return {}

    def save_points(self):
        with open("points.json", "w") as file:
            json.dump(self.points, file)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Levels cog ready")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        guild_id = str(message.guild.id)
        author_id = str(message.author.id)

        if guild_id not in self.points:
            self.points[guild_id] = {}
        if author_id not in self.points[guild_id]:
            self.points[guild_id][author_id] = 0
        self.points[guild_id][author_id] += 1

        # Save periodically for better performance
        self.save_points()

    @discord.app_commands.command(name="get_points", description="fetch the points of a user")
    async def get_points(self, interaction: discord.Interaction, user: discord.Member=None):
        targetisinvoker = False
        if user is None:
            targetisinvoker = True
            user = interaction.user
        guild_id = str(interaction.guild.id)
        user_id = str(user.id)
        points = self.points.get(guild_id, {}).get(user_id, 0)
        if targetisinvoker:
            await interaction.response.send_message(f"you have {points} points")
        else:
            await interaction.response.send_message(f"{user.mention} has {points} points")
        
async def setup(client):
    await client.add_cog(Levels(client))
    print('Cog "levels" loaded')
