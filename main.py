import discord
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

latentmessages = []

async def log():
    global latentmessages
    await client.wait_until_ready()
    while not client.is_closed():
        with open("log.txt", "a", encoding="utf-8", errors="replace") as file:
            file.writelines(latentmessages)
        latentmessages = []
        await asyncio.sleep(30)

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
    for member in members:
        try:
            await member.add_roles(add)
            added_count += 1
            print(f"added role {add.name} to {member.name}")
            await message.edit(content=f"{response} \nprogress: {added_count}/{len(members)}")
        except Exception as e:
            print(f"error adding role to {member.name}: {e}")
            interaction.followup.send(f"could not role to {member.name}: {e}")

    stamp = f"user {interaction.user.name} added role \"{add.name}\" to {added_count}/{len(member)} members of role \"{target.name}\""
    latentmessages.append(stamp)
    print(stamp)
    await message.edit(stamp)

client.run('MTMyMTY5NzI1MjY2MTc4ODgyNA.GVuDKq.l1dElthaHLrLWGW63MLeXKsXrhlf3mA0ztDCv0')