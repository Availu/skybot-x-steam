import re, sys
from util import hook, http

api_key = ""
profile_url = "http://www.steamcommunity.com/id/"

@hook.api_key('steam')
@hook.command(autohelp=False)
def steam(inp, url_pasted=None, chan='', nick='', reply=None, api_key=None, db=None):
    ".steam -- gets Steam profile info for <user>"

    db.execute(
        "create table if not exists "
        "steam(chan, nick, user, primary key(chan, nick))"
    )

    if inp[0:1] == '@':
        nick = inp[1:].strip()
        user = None
        dontsave = True
    else:
        user = inp

        dontsave = user.endswith(" dontsave")
        if dontsave:
            user = user[:-9].strip().lower()

    if not user:
        user = db.execute(
            "select user from steam where chan=? and nick=lower(?)",
            (chan, nick)).fetchone()
        if not user:
            return steam.__doc__
        user = user[0]

    getid_url = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"

    steamid = http.get_json(getid_url, key = api_key, vanityurl = user)
    if steamid["response"]["success"] == 42: #fail response
        return "error: "+ str(steamid["response"]["success"]) + " ("+ steamid["response"]["message"] +")"

    request_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"

    steamapi = http.get_json(request_url, key = api_key, steamids = steamid["response"]["steamid"])
    steam = steamapi["response"]["players"][0]

    status = {0: "\x0304Offline\x03",
                   1: "\x0303Online\x03",
                   2: "\x0308Busy\x03",
                   3: "\x0308Away\x03",
                   4: "\x0308Snooze\x03",
                   5: "\x0303looking to trade\x03",
                   6: "\x0303looking to play\x03"}

    ret = "\x02"+ steam["personaname"] + "\x0f [" + status[steam["profilestate"]] +"]"
    if "gameid" not in steam:
        ret += " | Not playing anything."
    else:
        ret += " | Playing \x02"+ steam["gameextrainfo"] +"\x02"
    if url_pasted is None:
        ret += " | "+ profile_url + user

    return ret

    if inp and not dontsave:
        db.execute(
            "insert or replace into steam(chan, nick, user) "
            "values (?, ?, ?)", (chan, nick.lower(), inp))
        db.commit()

@hook.regex(r"steamcommunity.com/id/([_0-9a-zA-Z]+)")
def show_channel(match, url_pasted=None):
    return steam(match.group(1), "yes", '', '', None, None, None)

