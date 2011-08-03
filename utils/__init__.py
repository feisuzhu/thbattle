class PlayerList(list):
    def write(self, data):
        for p in self:
            p.write(data)
