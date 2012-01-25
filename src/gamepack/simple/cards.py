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

    def _get_action(self):
        import actions
        return dict(
            attack = actions.Attack,
            graze = None,
            heal = actions.Heal,
            __hidden__ = None,
        ).get(self.type) # nasty circular reference !

    assocated_action = property(_get_action)

HiddenCard = Card('hidden')
HiddenCard.hidden = True
