import os

CREATOR_ID = os.environ["CREATOR_ID"]


def get_member_ping(guild, string):  # Gets member from guild and @message
    member = None
    if string.startswith("<@") and string.endswith(">"):
        string = string.replace("<@", "")
        string = string.replace(">", "")
        if string.isdigit():
            member = guild.get_member(int(string))
    return member


def ping_string(member_id):  # Creates a ping string with member id
    return "<@" + str(member_id) + ">"


def pref_name(member):  # Returns nickname if one exists and username if not
    if member.nick is not None:
        return member.nick
    else:
        return member.name


def is_creator(member):  # Checks if member is creator or not
    if str(member.id) == str(CREATOR_ID):
        return True
    else:
        return False
