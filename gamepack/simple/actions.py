# All Actions, EventHandlers are here
from server.core import Game, Action, EventHandler
from cards import Card, HiddenCard
from network import Endpoint
import random

class GenericAction(Action): pass # others

class UserAction(Action): pass # card/character skill actions
class BaseAction(UserAction): pass # attack, graze, heal

class InternalAction(Action): pass # actions for internal use, should not be intercepted by EHs


class Damage(GenericAction):

    def __init__(self, target, amount=1):
        self.target = target
        self.amount = amount

    def apply_action(self):
        self.target.life -= self.amount
        if Game.CLIENT_SIDE:
            # visual effects
            pass
        return True
        

class Attack(BaseAction):
    
    def __init__(self, target, damage=1):
        self.target = target
        self.damage = damage
    
    def apply_action(self):
        g = Game.getgame()
        if Game.CLIENT_SIDE:
            # visual effects
            pass
        if not g.process_action(UseCard(target=self.target, cond=lambda cl: len(cl) == 1 and cl[0].type == 'graze')):
            return g.process_action(Damage(target=self.target, amount=self.damage))
        else:
            return False

class DropCardIndex(GenericAction):
    
    def __init__(self, target, cards):
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        
        cl = self.target.gamedata.cards
        for i in cards:
            cl[i] = None
        self.target.gamedata.cards = [i for i in cl if i is not None]
        return True
        

class ChooseAndDropCard(GenericAction):
    
    def __init__(self, target, cond):
        self.target = target
        self.cond = cond

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        if Game.SERVER_SIDE:
            cards = p.gexpect('cards')
            if not self.cond([p.gamedata.cards[i] for i in cards]):
                cards = []
            g.players.gwrite(['usecard_index', cards])

        if Game.CLIENT_SIDE:
            me = Game.me
            if self.target is me:
                while True:
                    s = raw_input()
                    if s == '':
                        me.gwrite(['cards',[]])
                        break
                    try:
                        l = eval(s)
                        if self.cond([me.gamedata.cards[i] for i in l]):
                            break
                    except:
                        pass
                    print 'Wrong card! Choose another'
                me.gwrite(['cards', l])

            cards = me.gexpect('usecard_index')
        
        if not len(cards):
            return False

        return g.process_action(DropCardIndex(target=self.target, cards=cards))

class UseCard(ChooseAndDropCard): pass 
class DropUsedCard(DropCardIndex): pass

class DropCardStage(ChooseAndDropCard):
    
    def __init__(self, target):
        ChooseAndDropCard.__init__(self, target, cond = lambda cl: len(cl) == self.target.gamedata.life)

class DrawCardStage(GenericAction):
    
    def __init__(self, target, amount=2):
        self.target = target
        self.amount = amount

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        if Game.SERVER_SIDE:
            c = [Card(random.choice(['attack','graze', 'heal'])) for i in xrange(self.amount)]
            p.gwrite(['drawcards', c])
            p.gamedata.cards += c

        if Game.CLIENT_SIDE:
            if p is Game.me:
                cl = p.gexpect('drawcards')
                cl = [Card.parse(i) for i in cl]
            else:
                p.gamedata.cards += [HiddenCard] * self.amount
        
        return True

class Heal(BaseAction):
    
    def __init__(self, target, amount=1):
        self.target = target
        self.amount = amount

    def apply_action(self):
        self.target.gamedata.life += amount

class ActionStage(GenericAction):
    
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        p = self.target

        while True:
            if Game.SERVER_SIDE:
                ins = p.gexpect('myaction')
                if ins == []:
                    g.players.gwrite(['action', ins])
                    break
                c = p.gamedata.cards[ins[0]]
                act = [ins, c]
                g.players.gwrite(['action', act])

            if Game.CLIENT_SIDE:
                if p is Game.me:
                    print 'Your life is %d' % p.gamedata.life
                    print 'Your cards is %s' % Endpoint.encode(p.gamedata.cards)
                    print 'Players: %s' % Endpoint.encode(g.players)
                    print 'Your instruction: ',
                    ins = raw_input() # "$cardindex $targetindex"
                    if ins == '':
                        ins = []
                    else:
                        ins = [int(i) for i in ins.split(' ')]
                    p.gwrite(['myaction', ins])
                    act = [ins, p.gamedata.cards[ins[0]]]
                    p.gexpect('action')
                else:
                    a = p.gexpect('action')
                    if a == []:
                        break
                    act = [a[0], Card.parse(a[1])]
            
            c = act[2]
            tg = g.players[act[1]]
            if c.type == 'attack':
                g.process_action(Attack(target=tg))
            elif c.type == 'heal':
                g.process_action(Heal(target=tg))
            else:
                continue

            g.process_action(DropUsedCard(target=p, cards=[act[0]]))
        
        return True
