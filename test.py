import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    synced = await bot.tree.sync()  # Global sync
    print(f"Synced {len(synced)} commands globally.")

@bot.tree.command(name="test", description="A simple test command.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("test", ephemeral=True)

bot.run("MTMyMTY5NzI1MjY2MTc4ODgyNA.G_jV_F.D21WaHXoz3O4kDmpt4Zfab2mFn0z596WaCm_P0")
