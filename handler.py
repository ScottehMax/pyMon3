import asyncio
import random
import re
import time
import traceback

from utils import login, unreg_login, make_msg_info, condense
from room import Room


async def handle_msg(m, cb):
    messages = m.split('\n')

    if messages[0][0] == '>':
        room = messages.pop(0)[1:]
    else:
        room = 'lobby'

    for rawmessage in messages:
        print('%s%s' % (room, rawmessage))
        rawmessage = "%s\n%s" % ('>' + room, rawmessage)

        msg = rawmessage.split("|")

        if len(msg) < 2:
            continue

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

            await cb.send('', '/trn {0},0,{1}'.format(username, assertion))

        elif downmsg == 'updateuser':
            if condense(msg[2]) == condense(cb.username):
                print("Logged in!")
                rooms = cb.config['DEFAULT']['rooms']
                for room in rooms.split(','):
                    await cb.send('', '/join {}'.format(room))

        elif downmsg == 'formats':
            data = '|'.join(msg[2:])
            cb.battle_formats = list(map(condense, (re.sub(
                r'\|\d\|[^|]+', '', ('|' + re.sub(r'(,[0-9a-f])', '', data)))).split('|')))[1:]

        elif downmsg == 'init':
            cb.rooms[room] = Room(room)

        elif downmsg == 'title':
            cb.rooms[room].title = msg[2]

        elif downmsg == 'users':
            cb.rooms[room].users = []
            for user in msg[2].split(',')[1:]:
                cb.rooms[room].users.append(user)
            print(cb.rooms[room].__dict__)

        elif downmsg == ':':
            cb.rooms[room].join_time = int(msg[2])

        elif downmsg == 'j' and condense(msg[2]) not in cb.rooms[room].users:
            cb.rooms[room].users.append(msg[2])

        elif downmsg == 'l':
            for user in cb.rooms[room].users:
                if condense(user) == condense(msg[2]):
                    cb.rooms[room].users.remove(user)

        elif downmsg == 'n':
            newuser, olduser, userfound = msg[2], msg[3], False
            for user in cb.rooms[room].users:
                if condense(user) == condense(olduser):
                    cb.rooms[room].users.remove(user)
                    userfound = True
            if userfound:
                cb.rooms[room].users.append(newuser)

        if downmsg in ['c', 'c:', 'pm', 'j', 'l']:
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
        print("Crashed: %s, %s, %s" %
                         (e.args, plugin, type(e)))
        traceback.print_exception(e)
        await cb.send_pm(cb.master,
                         "Crashed: %s, %s, %s" %
                         (e.args, plugin, type(e)))


async def handle_chat(m, room, cb):
    m_info = await make_msg_info(m, room, cb.ws, cb.id, cb.config)

    if room != 'lobby' and int(m_info.get('when')) <= cb.rooms[room].join_time:
        return

    for plugin in cb.plugins:
        match = await plugin.match(m_info)
        if match:
            asyncio.run_coroutine_threadsafe(plugin_response(plugin, room,
                                                             m_info, cb),
                                             loop=cb.loop)
