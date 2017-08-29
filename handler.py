import asyncio
import random
import re
import time

import utils


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
                assertion = await utils.login(username,
                                              cb.config[cb.id]['password'],
                                              '|'.join(msg[2:4]))
            else:
                assertion = await utils.unreg_login(username,
                                                    '|'.join(msg[2:4]))

            if len(assertion) == 0 or assertion is None:
                raise Exception('login failed :(')

            await cb.send('', '/trn {0},0,{1}'.format(username, assertion))

        elif downmsg == 'updateuser':
            if utils.condense(msg[2]) == utils.condense(cb.username):
                print("Logged in!")
                rooms = cb.config['DEFAULT']['rooms']
                for room in rooms.split(','):
                    await cb.send('', '/join {}'.format(room))

        elif downmsg == 'formats':
            data = '|'.join(msg[2:])
            cb.battle_formats = list(map(utils.condense,
                                         (re.sub(r'\|\d\|[^|]+', '', ('|' + re.sub(r'(,[0-9a-f])', '', data)))
                                          ).split('|')))[1:]

        elif downmsg in ['c', 'c:', 'pm']:
            await handle_chat(msg[1:], room, cb)


async def plugin_response(plugin, room, m_info, cb):
    response = await plugin.response(m_info)
    if response:
        await cb.send(room, response)


async def handle_chat(m, room, cb):
    m_info = await utils.make_msg_info(m, room, cb.ws, cb.id, cb.config)

    if int(m_info.get('when')) <= cb.logintime:
        return

    for plugin in cb.plugins:
        match = await plugin.match(m_info)
        if match:
            asyncio.run_coroutine_threadsafe(plugin_response(plugin, room,
                                                             m_info, cb),
                                             loop=cb.loop)
