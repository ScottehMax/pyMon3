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
                     'what': ''})

    elif info['where'] == 'n':
        info.update({'room': room,
                     'who': msg[1][1:],
                     'allwho': msg[1],
                     'oldname': msg[2],
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
    return info
