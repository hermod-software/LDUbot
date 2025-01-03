import discord

from guildconfig import GuildConfig

class GuildMember:
    guilds = {}

    def __init__(self, member: discord.Member, guildconfig: GuildConfig):
        self.displayname = member.display_name  # nickname if set, displayname otherwise, username if neither
        self.username = member.name             # username
        self.userid = member.id                 # user id

        self.guildid = member.guild.id          # server id
        self.guildname = member.guild.name      # server name
        
        self.points = 0
        self.points_total = 0
        self.level = 0

        self.tonextlevel = 0

        self.roles = member.roles

        GuildMember.guilds[self.guildid] = self

    def __str__(self):
        stringed = []
        stringed.append(f"user {self.displayname} ({self.username}) in guild {self.guildname} ({self.guildid})\n")
        stringed.append(f"roles: {self.roles}\n")
        stringed.append(f"points: {self.points} (level {self.level})\n")
        return ''.join(stringed)
    
    def increment_points(self, amount: int):
        self.points += amount



# points to levels formula:
