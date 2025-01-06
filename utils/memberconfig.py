import discord

from utils.guildconfig import GuildConfig
from utils.shared import client

class GuildMember:
    # guilds = {
    #     # guildid: {userid: GuildMember}
    # }

    def __init__(self, memberid: int):

        member = client.get_user(memberid)

        self.displayname = member.display_name  # nickname if set, displayname otherwise, username if neither
        self.username = member.name             # username
        self.userid = member.id                 # user id

        self.guildid = member.guild.id          # server id
        self.guildname = member.guild.name      # server name

        self.config = self.getconfig()          # server config
        self.tonextlevel = self.config["base"]  # points needed to level up
        
        self.points = 0                         # total points

        

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
    
    



# points to levels formula:
