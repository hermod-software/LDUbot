import discord
from discord.ext import commands
import asyncio
import hashlib
import yaml
import os

from utils.shared import client, tree # using discord.Bot, not discord.Client, holdover from old code
from utils.guildmember import GuildMember
from utils.guildconfig import GuildConfig




client.guildmembers = {}
client.guildconfigs = {}

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
        
    await client.load_extension("cogs.levels")
    await client.load_extension("cogs.mapchart")

    await synctrees()
    print("Commands loaded:")
    for command in tree.get_commands():
        print(f" - {command.name}")


 
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

@tree.command(name="role_list", description="list all members with a given role")
async def role_list(interaction: discord.Interaction, role: discord.Role):
    members = role.members
    output = '\n'.join([member.name for member in members])
    await interaction.response.send_message(f"members of {role.name}:\n {output}")

@tree.command(name="add_role_to_members", description="add a role to all members of a certain role")
@discord.app_commands.default_permissions(manage_roles=True)
async def add_role_to_members(interaction: discord.Interaction, target: discord.Role, add: discord.Role):
    guild = interaction.guild
    guild.fetch_members()

    response = f"adding role \"{add.name}\" to all members of role \"{target.name}\" (this might take a little while)"
    await interaction.response.send_message(response)
    message = await interaction.original_response()

    members = target.members
    added_count = 0
    errors = []
    for member in members:
        try:
            await member.add_roles(add)
            added_count += 1
            print(f"added role {add.name} to {member.name}")
            await message.edit(content=f"{response} \nprogress: {added_count}/{len(members)}")
        except Exception as e:
            error = f"error adding role to {member.name}: {e}"
            print(error)
            errors.append(error)
            interaction.followup.send(error)
    username = interaction.user.name
    stamp = f"user {username} added role \"{add.name}\" to {added_count}/{len(member)} members of role \"{target.name}\""
    print(stamp)
    await message.edit(stamp)

with open("bot_token.txt", "r") as file:
    bot_token = file.read().strip()

client.run(bot_token)