import discord
import asyncio
import hashlib
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

latentmessages = [] # this variable is used to temporarily store messages that are then logged to log.txt every 30 seconds

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
    asyncio.create_task(log())
    print("Started logging to log.txt")

LOG_EXCLUDE_CHANNELS = [
    "bot-games",
    "privatelog"
    "publiclog"
]


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

if os.path.exists("blacklist.txt"):
    with open("blacklist.txt", "r") as file:
        blacklist = file.readlines()
        blacklist = [line.strip() for line in blacklist] # remove newline characters
else:
    blacklist = [] # if the file doesn't exist, create an empty one

def hashusername(username):
    username = username.encode("utf-8")
    return hashlib.sha256(username).hexdigest()

def blacklistuser(username):
    username = hashusername(username)

    if not username in blacklist:
        blacklist.append(username)

    with open("log.txt", "r") as file:  # load the log file into memory
        log = file.readlines()          # read the file into a list of lines

    for i, line in enumerate(log):      # iterate over the lines in the log
        if username in line.split():    # if the username is in the line as a separate word (not as part of a longer word)
            log[i] = log[i].replace(username, "(redacted username)")  #redact the username

    with open("log.txt", "w") as file:  # open the log file in write mode
        file.writelines(log)            # write the new redacted log to the file

    with open("blacklist.txt", "w") as file:    # save the blacklist with the new user added
        file.writelines(blacklist)

def unblacklistuser(username):
    username = hashusername(username)
    for i, user in enumerate(blacklist):
        if user == username:
            blacklist.pop(i)
    with open("blacklist.txt", "w") as file:    # save the blacklist with the new user removed
        file.writelines(blacklist)

    with open("blacklist.txt", "w") as file:    # save the blacklist with the new user removed
        file.writelines(blacklist)

def isblacklisted(username):
    hashtocheck = hashusername(username)
    return hashtocheck in blacklist # check if the hashed username is in the blacklist

@tree.command(name="privacy", description="prevent debug logs from containing your username")
async def privacy(interaction: discord.Interaction, option: bool):
    if option == True:
        if not isblacklisted(interaction.user.name):
            blacklistuser(interaction.user.name)
            await interaction.response.send_message(f"blacklisted user {interaction.user.name}. you can unblacklist yourself by doing /privacy False\n(see https://loritsi.neocities.org/privacy.txt)", ephemeral=True)
        else:
            await interaction.response.send_message(f"user {interaction.user.name} is already blacklisted", ephemeral=True)
    if option == False:
        if isblacklisted(interaction.user.name):
            unblacklistuser(interaction.user.name)
            await interaction.response.send_message(f"unblacklisted user {interaction.user.name}. you can blacklist yourself again by doing /privacy True\n (see https://loritsi.neocities.org/privacy.txt)", ephemeral=True)
        else:
            await interaction.response.send_message(f"user {interaction.user.name} is not blacklisted", ephemeral=True)
    




client.run('MTMyMTY5NzI1MjY2MTc4ODgyNA.GVuDKq.l1dElthaHLrLWGW63MLeXKsXrhlf3mA0ztDCv0')