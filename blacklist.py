import discord
import hashlib
import os

from shared import client, tree

def readblacklist():
    if os.path.exists("blacklist.txt"):
        with open("blacklist.txt", "r") as file:
            blacklist = file.readlines()
            blacklist = [line.strip() for line in blacklist] # remove newline characters
            return blacklist
    else:
        blacklist = [] # if the file doesn't exist, create an empty one
        return blacklist
    
def writelog(log):
    with open("log.txt", "w") as file:
        file.writelines(log)

def writeblacklist(blacklist):
    with open("blacklist.txt", "w") as file:
        file.writelines(blacklist)

def hashusername(username):
    username = username.encode("utf-8")
    return hashlib.sha256(username).hexdigest()

def blacklistuser(username, blacklist):
    username = hashusername(username)

    if not username in blacklist:
        blacklist.append(username)

    with open("log.txt", "r") as file:  # load the log file into memory
        log = file.readlines()          # read the file into a list of lines

    for i, line in enumerate(log):      # iterate over the lines in the log
        if username in line.split():    # if the username is in the line as a separate word (not as part of a longer word)
            log[i] = log[i].replace(username, "(redacted username)")  #redact the username

    writelog(log)
    writeblacklist(blacklist) # save the blacklist with the new user added

def unblacklistuser(username, blacklist):
    username = hashusername(username)
    for i, user in enumerate(blacklist):
        if user == username:
            blacklist.pop(i)
    writeblacklist(blacklist) # save the blacklist with the user removed

def isblacklisted(username, blacklist):
    hashtocheck = hashusername(username)
    return hashtocheck in blacklist # check if the hashed username is in the blacklist

def testblacklist(blacklist):
    user = "ABCDEF" # cannot be a real username as usernames are always lowercase
    checks = 0
    blacklistuser(user, blacklist)
    assert isblacklisted(user, blacklist)
    unblacklistuser(user, blacklist)
    assert not isblacklisted(user, blacklist)

