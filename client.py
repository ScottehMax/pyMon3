#!/usr/bin/env python3

import asyncio
import configparser

import aiohttp

import handler
import chatbot


config = configparser.ConfigParser()
if not config.read('config.ini'):
    print("Empty configuration file.")
    exit(1)

chatbots = []


async def create_cb(chatbot_id, cbs, config):
    # cbs is the list of chatbots
    cb = chatbot.Chatbot(id=chatbot_id,
                         cbs=cbs,
                         config=config)
    await cb._init_plugins()
    await cb._connect()
    return cb


for chatbot_id in config.sections():
    if config[chatbot_id].getboolean('enabled'):
        cb = create_cb(chatbot_id, chatbots, config)
        chatbots.append(cb)

loop = asyncio.get_event_loop()

loop.run_until_complete(asyncio.wait(chatbots))
loop.close()
