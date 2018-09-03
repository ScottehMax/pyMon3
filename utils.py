import json
import re
import time

import aiohttp


def condense(string):
    return (re.sub(r'[^A-Za-z0-9]', '', string)).lower()


async def login(username, password, challstr):
    url = 'https://play.pokemonshowdown.com/action.php'
    values = {'act': 'login',
              'name': username,
              'pass': password,
              'challstr': challstr
              }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=values) as r:
            resp = await r.text()
            resp = json.loads(resp[1:])
            return resp['assertion']


async def unreg_login(username, challstr):
    url = 'https://play.pokemonshowdown.com/action.php'
    values = {'act': 'getassertion',
              'userid': condense(username),
              'challstr': challstr
              }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=values) as r:
            resp = await r.text()
            return resp


async def make_msg_info(msg, room, ws, id, config):
    info = {'where': msg[0],
            'ws': ws,
            'all': msg,
            'me': config[id]['username']
            }

    info['where'] = info['where'].lower()

    if info['where'] == 'c:':
        info.update({'where': 'c',
                     'room': room,
                     'who': msg[2][1:],
                     'allwho': msg[2],
                     'when': int(msg[1]),
                     'what': '|'.join(msg[3:])})

    elif info['where'] == 'c':
        info.update({'room': room,
                     'who': msg[1][1:],
                     'allwho': msg[1],
                     'when': int(time.time()),
                     'what': '|'.join(msg[2:])})

    elif info['where'] == 'j' or info['where'] == 'l':
        info.update({'room': room,
                     'who': msg[1][1:],
                     'allwho': msg[1],
                     'when': int(time.time()),
                     'what': ''})

    elif info['where'] == 'n':
        info.update({'room': room,
                     'who': msg[1][1:],
                     'allwho': msg[1],
                     'oldname': msg[2],
                     'when': int(time.time()),
                     'what': ''})

    elif info['where'] == 'users':
        info.update({'room': room,
                     'who': '',
                     'what': msg[1]})

    elif info['where'] == 'pm':
        info.update({'who': msg[1][1:],
                     'allwho': msg[1],
                     'target': msg[2][1:],
                     'when': int(time.time()),
                     'what': msg[3]})

    elif info['where'] == 'html':
        info.update({'who': '',
                     'when': int(time.time()),
                     'what': msg[1]})

    return info


async def haste(message):
    async with aiohttp.ClientSession() as session:
        async with session.post('https://hastebin.com/documents',
                                data=message) as r:
            resp = await r.text()
            j = json.loads(resp)
    if 'key' in j:
        result = f"https://hastebin.com/{j['key']}"
    else:
        result = "Didn't work"
    return result


def execute_sql(sql, cb):
    cb.c.execute(sql)
    result = cb.c.fetchall()
    return ppsql(cb.c, result)


def ppsql(cursor, rows):
    widths = []
    columns = []
    tavnit = '|'
    separator = '+'
    res = ''
    for i, cd in enumerate(cursor.description):
        max_l = max([len(x[i]) for x in rows])
        widths.append(max(max_l, len(cd[0])))
        columns.append(cd[0])
    for w in widths:
        tavnit += " %-"+"%ss |" % (w,)
        separator += '-'*w + '--+'
    res += separator + '\n'
    res += tavnit % tuple(columns) + '\n'
    res += separator + '\n'
    for row in rows:
        res += tavnit % row + '\n'
    res += separator
    return res


def get_format_info(format_text):
    results = []
    num = int(format_text, 16)
    if num & 1:
        # this format requires a team.
        results.append('Requires Team')
    if num & 2:
        # this format can be played on the ladder
        results.append('Search')
    if num & 4:
        # this format can be used in private challenges
        results.append('Challenge')
    if num & 8:
        # this format can be used in tournaments
        results.append('Tournaments')
    if num & 16:
        # this format forces level 50
        results.append('Forced Level 50')
    return results
