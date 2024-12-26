import discord
import asyncio
import hashlib
import os

from shared import client, tree
from blacklist import readblacklist, blacklistuser, unblacklistuser, isblacklisted, testblacklist

latentmessages = [] # this variable is used to temporarily store messages that are then logged to log.txt every 30 seconds
blacklist = [] # this list will store the hashed usernames of users who have opted out of logging

async def log(): # log messages to log.txt every 30 seconds
    global latentmessages
    await client.wait_until_ready()
    while not client.is_closed():
        if not latentmessages == []:    # don't bother opening the file if there's nothing to write
            with open("log.txt", "a", encoding="utf-8", errors="replace") as file: # open the file in append mode
                file.writelines(latentmessages) # write all the messages in the list to the file
        latentmessages = []
        await asyncio.sleep(30) # wait 30 seconds (asyncio doesn't block the event loop)

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
    await synctrees()
    print("Commands loaded:")
    for command in tree.get_commands():
        print(f" - {command.name}")

    asyncio.create_task(log())
    print("Started logging to log.txt")
    blacklist = readblacklist() # load the blacklist from the file
    testblacklist(blacklist) # run the test function to make sure the blacklist functions work (it'll crash if they don't)
    print(f"Loaded & tested blacklist")



# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
    
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

@tree.command(name="role_list", description="list all members with a given role")
async def role_list(interaction: discord.Interaction, role: discord.Role):
    members = role.members
    output = '\n'.join([member.name for member in members])
    await interaction.response.send_message(f"members of {role.name}:\n {output}")

@tree.command(name="add_role_to_members", description="add a role to all members of a certain role")
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
        latentmessages.extend(errors)
    username = interaction.user.name
    if isblacklisted(username):
        username = "(redacted username)"
    stamp = f"user {username} added role \"{add.name}\" to {added_count}/{len(member)} members of role \"{target.name}\""
    latentmessages.append(stamp)
    print(stamp)
    await message.edit(stamp)

@tree.command(name="privacy", description="prevent debug logs from containing your username")
async def privacy(interaction: discord.Interaction, option: bool):
    blacklist = readblacklist()
    print(f"privacy command invoked by {interaction.user.name}: {option}")
    if option == True:
        if not isblacklisted(interaction.user.name, blacklist):
            blacklist = blacklistuser(interaction.user.name, blacklist)
            await interaction.response.send_message(f"blacklisted user {interaction.user.name}. you can unblacklist yourself by doing /privacy False\n(see https://loritsi.neocities.org/privacy.txt)", ephemeral=True)
        else:
            await interaction.response.send_message(f"user {interaction.user.name} is already blacklisted", ephemeral=True)
        return
    if option == False:
        if isblacklisted(interaction.user.name, blacklist):
            blacklist = unblacklistuser(interaction.user.name, blacklist)
            await interaction.response.send_message(f"unblacklisted user {interaction.user.name}. you can blacklist yourself again by doing /privacy True\n (see https://loritsi.neocities.org/privacy.txt)", ephemeral=True)
        else:
            await interaction.response.send_message(f"user {interaction.user.name} is not blacklisted", ephemeral=True)
        return


    






client.run('MTMyMTY5NzI1MjY2MTc4ODgyNA.G_jV_F.D21WaHXoz3O4kDmpt4Zfab2mFn0z596WaCm_P0')