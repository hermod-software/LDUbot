import discord
from discord.ext import commands

# configuration slash commands

@discord.app_commands.default_permissions(manage_roles=True)
class GuildConfig(commands.GroupCog, group_name="config"):
    def __init__(self, client: commands.Bot):
        self.client = client

        for guild in self.client.guilds:
            if guild.id not in ConfigHandler.guilds:
                ConfigHandler(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if guild.id not in ConfigHandler.guilds:
            ConfigHandler(guild)
        print(f"Joined guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if guild.id in ConfigHandler.guilds:
            del ConfigHandler.guilds[guild.id]
        print(f"Left guild: {guild.name} (ID: {guild.id})")

    @discord.app_commands.command(
        name="set_base", 
        description=f"set the amount of points to get from level 0 to level 1 (default: {ConfigHandler.defaultconfig['base']})"
    )
    @commands.has_permissions(manage_guild=True)
    async def set_base(self, interaction: discord.Interaction, base: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("base", base)
        await interaction.response.send_message(f"set base points amount to {base}")

    @discord.app_commands.command(name="get_base", description="get the amount of points to get from level 0 to level 1")
    async def get_base(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        base = guild_config.getconfig("base")
        await interaction.response.send_message(f"base points amount is {base}")

    @discord.app_commands.command(name="set_growth_rate", description=f"set the growth rate for points (default: {ConfigHandler.defaultconfig['growth_rate']})")
    @commands.has_permissions(manage_guild=True)
    async def set_growth_rate(self, interaction: discord.Interaction, rate: float):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("growth_rate", rate)
        await interaction.response.send_message(f"set growth rate to {rate}")

    @discord.app_commands.command(name="get_growth_rate", description="get the growth rate for points")
    @commands.has_permissions(manage_guild=True)
    async def get_growth_rate(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        rate = guild_config.getconfig("growth_rate")
        await interaction.response.send_message(f"growth rate is {rate}")

    @discord.app_commands.command(name="set_point_range", description=f"set the upper and lower bound for points awarded (default: {ConfigHandler.defaultconfig['point_range_lower']} - {ConfigHandler.defaultconfig['point_range_upper']})")
    @commands.has_permissions(manage_guild=True)
    async def set_point_range(self, interaction: discord.Interaction, lower: int, upper: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.setconfig("point_range_lower", lower)
        guild_config.setconfig("point_range_upper", upper)
        await interaction.response.send_message(f"set point range to {lower} - {upper}")

    @discord.app_commands.command(name="get_point_range", description="get the upper and lower bound for points awarded")
    @commands.has_permissions(manage_guild=True)
    async def get_point_range(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        lower = guild_config.getconfig("point_range_lower")
        upper = guild_config.getconfig("point_range_upper")
        await interaction.response.send_message(f"point range is {lower} - {upper}")

    @discord.app_commands.command(name="reset_config", description="reset the configuration for this guild")
    @discord.app_commands.default_permissions(manage_roles=True)
    async def reset_config(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.load()
        await interaction.response.send_message("configuration reset")

    @discord.app_commands.command(name="get_config", description="get the configuration for this guild")
    async def get_config(self, interaction: discord.Interaction):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        
        config = copy.deepcopy(guild_config.config)
        roles = config["roles"]
        upd_roles = {}

        if roles != {}:
            for level, role in roles.items():
                role = interaction.guild.get_role(role)
                upd_roles[level] = role.name
        else:
            upd_roles = "No roles set (use /config set_level_role <level> <role> to set a role)"

        config["roles"] = upd_roles
        
        yaml_config = yaml.dump(config)


        await interaction.response.send_message(f"configuration for {interaction.guild.name}:\n```yaml\n{yaml_config}```")

    @discord.app_commands.command(name="set_level_role", description="set a role to be awarded at a certain level")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def set_level_role(self, interaction: discord.Interaction, level: int, role: discord.Role):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        guild_config.set_level_role(level, role)
        await interaction.response.send_message(f"role {role.name} set to be awarded at level {level}")

    @discord.app_commands.command(name="del_level_role", description="remove a role from being awarded at a certain level")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def del_level_role(self, interaction: discord.Interaction, level: int):
        guild_config = ConfigHandler.guilds.get(interaction.guild.id)
        if not guild_config:
            await interaction.response.send_message("configuration not found for this guild.")
            return
        role_name = guild_config.config["roles"].get(level, "role not found")
        guild_config.del_level_role(level)
        await interaction.response.send_message(f"role {role_name} removed from level {level}")


async def setup(client: commands.Bot):
    await client.add_cog(GuildConfig(client))
