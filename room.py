import time

from utils import condense
from experimental import battle


class Room:
    def __init__(self, id, cb):
        self.id = id
        self.cb = cb
        self.users = []
        self.join_time = int(time.time())
        if self.id.startswith('battle-'):
            self.battle = battle.Battle(id, cb)

    def get_rank(self, user):
        u_id = condense(user)
        for u in self.users:
            if u_id == condense(u):
                return u[0]
