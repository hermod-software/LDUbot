import discord
from discord.ext import commands
import asyncio
import hashlib
import yaml
import os

from shared.defs.shared import client, tree
from components.blacklist import readblacklist, blacklistuser, unblacklistuser, isblacklisted, testblacklist



blacklist = []      # this list will store the hashed usernames of users who have opted out of logging

async def synctrees():
    print(f"Syncing commands list...", end="")
    await tree.sync()
    print("\rSynced commands list           ")
    

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    print(f"Connected guilds:")
    for guild in client.guilds:
        print(f" - {guild.name}")
        
    await client.load_extension("components.levels")
    await client.load_extension("components.mapchart")
    await client.load_extension("components.roleutil")

    loaded_cogs = client.cogs.keys()
    print("Loaded cogs: ")
    for cog in loaded_cogs:
        print(f" - {cog}")

    await synctrees()
    print("Commands loaded:")
    for command in tree.get_commands():
        print(f" - {command.name}")

    blacklist = readblacklist() # load the blacklist from the file
    testblacklist(blacklist) # run the test function to make sure the blacklist functions work (it'll crash if they don't)
    print(f"Loaded & tested blacklist")

 
@client.event
async def on_guild_join(guild):
    print(f"Joined guild:")
    print(f" - {guild.name}")
    await synctrees() 

@client.event
async def on_guild_remove(guild):
    print(f"Left guild:")
    print(f" - {guild.name}")
    await synctrees()

@client.event
async def on_interaction(interaction):
    print(f"interaction received: {interaction.data}")



import os



with open("bot_token.txt", "r") as file:
    bot_token = file.read().strip()

client.run(bot_token)