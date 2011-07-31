from network import Endpoint

class User(Endpoint):
    def __data__(self):
        return dict(
            id=id(self),
            username=self.username,
            nickname=self.nickname,
            halldata=self.halldata if hasattr(self, 'halldata') else None,
            state=self.state,
        )
