# Cards and Deck definition

class Card(object):
    def __init__(self, t):
        self.type = t
        self.hidden = False

    def __data__(self):
        return dict(
            type=self.type,
            hidden=False,
        )

    @staticmethod
    def parse(data):
        if data['hidden']:
            return HiddenCard
        else:
            return Card(t=data['type'])

HiddenCard = Card('__hidden__')
HiddenCard.hidden = True
