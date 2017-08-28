import time


class Plugin:
    """Base class for Plugins."""

    def __init__(self, cb):
        self.lastused = int(time.time())
        self.cb = cb

    async def match(self, info):
        """Checks whether the information in the info dict will cause
        the plugin to fire.
        """
        raise NotImplementedError

    async def response(self, info):
        """If the plugin is triggered, this will obtain the response
        to send back.
        """
        raise NotImplementedError


def setup(cb):
    """Returns the plugin object after optional initialisation."""
    return Plugin(cb)
