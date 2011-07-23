from server.network import Client

class User(Client):
    def __data__(self):
        return dict(
            id=id(self),
            username=self.username,
            nickname=self.nickname,
            halldata=self.halldata if hasattr(self, 'halldata') else None,
            state=self.state,
        )
