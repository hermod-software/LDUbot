import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(intents=intents, command_prefix="shdfjk")
tree = client.tree

def getclient():
    return client

def gettree():
    return tree