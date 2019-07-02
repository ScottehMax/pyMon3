import asyncio
import json
import random
import re
import time
import traceback

from utils import login, unreg_login, make_msg_info, condense, get_format_info
from room import Room


async def handle_msg(m, cb):
    messages = m.split('\n')

    if messages[0][0] == '>':
        room = messages.pop(0)[1:]
    else:
        room = 'global'

    for rawmessage in messages:
        print(f'{room}{rawmessage}')
        rawmessage = f'{">" + room}\n{rawmessage}'

        msg = rawmessage.split("|")

        if len(msg) < 2:
            continue

        if room.startswith('battle-') and cb.rooms.get(room):
            await cb.rooms[room].battle.handle(msg)

        downmsg = msg[1].lower()

        if downmsg == 'challstr':
            username = cb.username
            if cb.config[cb.id].get('password'):
                assertion = await login(username,
                                        cb.config[cb.id]['password'],
                                        '|'.join(msg[2:4]))
            else:
                assertion = await unreg_login(username,
                                              '|'.join(msg[2:4]))

            if len(assertion) == 0 or assertion is None:
                raise Exception('login failed :(')

            await cb.send('', f'/trn {username},0,{assertion}')

        elif downmsg == 'updateuser':
            if '@' in msg[2][1:]:
                user, status = msg[2].rsplit('@', 1)
            else:
                user = msg[2]
            if condense(user) == condense(cb.username):
                print("Logged in!")
                rooms = cb.config[cb.id]['rooms']
                # join rooms
                for room in rooms.split(','):
                    await cb.send('', f'/join {room}')
                # send status to last room
                await cb.send(room, f'/status {cb.status}')

        elif downmsg == 'formats':
            formats = msg[2:]
            res = {}
            format_name = False
            cur_format = None
            for format in formats:
                if format_name:
                    res[format] = []
                    cur_format = format
                    format_name = False
                    continue
                if format[0] == ',':
                    format_name = True
                    continue
                name, type = format.split(',', 1)
                res[cur_format].append( {'name': name, 'info': get_format_info(type)} )
            cb.battle_formats = res

        elif downmsg == 'init':
            cb.rooms[room] = Room(room, cb)

        elif downmsg == 'deinit':
            del cb.rooms[room]

        elif downmsg == 'title':
            cb.rooms[room].title = msg[2]

        elif downmsg == 'users':
            cb.rooms[room].users = []
            for user in msg[2].split(',')[1:]:
                cb.rooms[room].users.append(user)
            print(cb.rooms[room].__dict__)

        elif downmsg == ':':
            cb.rooms[room].join_time = int(msg[2])

        elif downmsg == 'j':
            if '@' in msg[2][1:]:
                user, status = msg[2].rsplit('@', 1)
            else:
                user = msg[2]
            if condense(user) not in cb.rooms[room].users:
                cb.rooms[room].users.append(user)

        elif downmsg == 'l':
            if '@' in msg[2][1:]:
                user, status = msg[2].rsplit('@', 1)
            else:
                user = msg[2]
            for existing_user in cb.rooms[room].users:
                if condense(existing_user) == condense(user):
                    cb.rooms[room].users.remove(existing_user)

        elif downmsg == 'n':
            newuser, olduser, userfound = msg[2], msg[3], False
            if '@' in newuser[1:]:
                newuser, status = newuser[1:].rsplit('@', 1)
            for user in cb.rooms[room].users:
                if condense(user) == condense(olduser):
                    cb.rooms[room].users.remove(user)
                    userfound = True
            if userfound:
                cb.rooms[room].users.append(newuser)

        elif downmsg == 'updatechallenges':
            challs = json.loads(msg[2])
            for chall in challs['challengesFrom']:
                if challs['challengesFrom'][chall] == 'gen7doublescustomgame':
                    if cb.teams:
                        team = random.choice(cb.teams['gen7doublescustomgame'])
                        await cb.send('', f'/utm {team}')
                        await cb.send('', f'/accept {chall}')

        if downmsg in ['c', 'c:', 'pm', 'j', 'l', 'html']:
            await handle_chat(msg[1:], room, cb)


async def plugin_response(plugin, room, m_info, cb):
    try:
        response = await plugin.response(m_info)
        if response:
            if m_info['where'] == 'pm':
                await cb.send_pm(m_info['who'], response)
            else:
                await cb.send(room, response)
    except Exception as e:
        print(f"Crashed: {e.args}, {plugin}, {type(e)}")
        traceback.print_exception(e)
        await cb.send_pm(cb.master,
                         f"Crashed: {e.args}, {plugin}, {type(e)}")


async def handle_chat(m, room, cb):
    m_info = await make_msg_info(m, room, cb.ws, cb.id, cb.config)
    m_time = m_info.get('when')

    if room != 'global' and m_time and int(m_time) <= cb.rooms[room].join_time:
        return

    for plugin in cb.plugins:
        try:
            match = await plugin.match(m_info)
        except Exception as e:
            print(f"Crashed in match: {e.args}, {plugin}, {type(e)}")
            traceback.print_exception(e)
            await cb.send_pm(cb.master,
                             f"Crashed in match: {e.args}, {plugin}, {type(e)}")
        if match:
            asyncio.run_coroutine_threadsafe(plugin_response(plugin, room,
                                                             m_info, cb),
                                             loop=cb.loop)
