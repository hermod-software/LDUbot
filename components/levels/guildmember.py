import discord

from guildconfig import GuildConfig

class GuildMember:
    guilds = {
        # guildid: {userid: GuildMember}
    }

    def __init__(self, member: discord.Member):
        self.displayname = member.display_name  # nickname if set, displayname otherwise, username if neither
        self.username = member.name             # username
        self.userid = member.id                 # user id

        self.guildid = member.guild.id          # server id
        self.guildname = member.guild.name      # server name

        self.config = self.getconfig()          # server config
        self.tonextlevel = self.config["base"]  # points needed to level up
        
        self.points = 0                 # points since last level up
        self.points_total = 0           # total points
        self.level = 0                  # current level

        

        self.roles = member.roles

        GuildMember.guilds[self.guildid][self.userid] = self

    def __str__(self):
        stringed = []
        stringed.append(f"user {self.displayname} ({self.username}) in guild {self.guildname} ({self.guildid})\n")
        stringed.append(f"roles: {self.roles}\n")
        stringed.append(f"points: {self.points} (level {self.level})\n")
        return ''.join(stringed)
    
    def getconfig(self):
        config = GuildConfig.guilds[self.guildid].config
        return config
    
    def calculate_level(self, amount):
        
    
    def increment_points(self, amount: int):
        pass



# points to levels formula:
