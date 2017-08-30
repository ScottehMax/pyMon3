from utils import condense


class Room:
    def __init__(self, id):
        self.id = id

    def get_rank(self, user):
        u_id = condense(user)
        for u in self.users:
            if u_id == condense(u):
                return u[0]
