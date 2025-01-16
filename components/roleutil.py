import discord
from discord.ext import commands
from discord import app_commands

class RoleUtil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roster", description="list all members with a given role")
    async def roster(self, interaction: discord.Interaction, role: discord.Role):
        allowedmentions = discord.AllowedMentions.none()    # no pings allowed
        guild = interaction.guild                           # get the guild
        await guild.fetch_members()                         # update member cache

        members = role.members

        if members is None:
            await interaction.response.send_message(f"error fetching members of role {role.mention}", allowed_mentions=allowedmentions)
            return
        elif len(members) == 0:
            await interaction.response.send_message(f"there are no members of role {role.mention}", allowed_mentions=allowedmentions)
            return
        elif len(members) > 150:
            permissions = interaction.channel.permissions_for(interaction.user)
            if not permissions.manage_roles:
                await interaction.response.send_message(f"there are {len(members)} members of {role.mention}, but only users with the manage_roles permission can list roles with more than 150 members")
                return

        await interaction.response.defer() # we might not be able to send the message right away

        output = [[]]
        for member in members:
            mention = f"<@{member.id}>"
            output[-1].append(mention)
            if len(', '.join(output[-1])) > 1900:
                output.append([])

        stamp = f"there are {len(members)} members of {role.mention}:"
        for message in output:
            joined_message = ', '.join(message)
            await interaction.followup.send(
                f"{stamp}\n{joined_message}",
                allowed_mentions=allowedmentions
            )
            stamp = ""

    @app_commands.command(name="bulk_assign", description="add role X to all members of role Y")
    @app_commands.default_permissions(manage_roles=True)
    async def bulk_assign(self, interaction: discord.Interaction, x: discord.Role, y: discord.Role):
        target = y
        add = x
        guild = interaction.guild
        await guild.fetch_members()

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
                await interaction.followup.send(error)
        username = interaction.user.name
        stamp = f"user {username} added role \"{add.name}\" to {added_count}/{len(members)} members of role \"{target.name}\""
        print(stamp)
        await message.edit(content=stamp)

async def setup(bot):
    await bot.add_cog(RoleUtil(bot))