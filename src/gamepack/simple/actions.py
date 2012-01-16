# All Actions, EventHandlers are here
from game.autoenv import Game, EventHandler, Action, GameError

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
        self.target.gamedata.life -= self.amount
        if Game.CLIENT_SIDE:
            # visual effects
            print 'Damage * %d !' % self.amount
        return True
        

class Attack(BaseAction):
    
    def __init__(self, target, damage=1):
        self.target = target
        self.damage = damage
    
    def apply_action(self):
        g = Game.getgame()
        if Game.CLIENT_SIDE:
            # visual effects
            print 'Attack!'
        if not g.process_action(UseCard(target=self.target, cond=lambda cl: len(cl) == 1 and cl[0].type == 'graze')):
            return g.process_action(Damage(target=self.target, amount=self.damage))
        else:
            if Game.CLIENT_SIDE:
                print 'Missed!'
            return False

class DropCardIndex(GenericAction):
    
    def __init__(self, target, cards):
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        
        cl = self.target.gamedata.cards
        if Game.SERVER_SIDE:
            g.players.gwrite(['dropcardindex', [cl[i] for i in self.cards]])
        for i in self.cards:
            cl[i] = None
        self.target.gamedata.cards = [i for i in cl if i is not None]
        if Game.CLIENT_SIDE:
            realcl = [Card.parse(i) for i in g.me.gexpect('dropcardindex')]
            print 'Card dropped:', str(realcl)

        return True
        

class ChooseAndDropCard(GenericAction):
    
    def __init__(self, target, cond):
        self.target = target
        self.cond = cond

    def apply_action(self):
        g = Game.getgame()
        p = self.target
        if Game.SERVER_SIDE:
            cards = p.gexpect('choosedrop_cards')
            cl = [p.gamedata.cards[i] for i in cards]
            if not self.cond(cl):
                cards = []
            g.players.gwrite(['choosedrop_index', cards])

        if Game.CLIENT_SIDE:
            me = g.me
            if self.target is me:
                while True:
                    print 'Choose card: ',
                    s = raw_input()
                    if s == '':
                        me.gwrite(['choosedrop_cards',[]])
                        break
                    try:
                        l = eval(s)
                        if self.cond([me.gamedata.cards[i] for i in l]):
                            me.gwrite(['choosedrop_cards', l])
                            break
                    except:
                        pass
                    print 'Wrong card! Choose another'

            cards = me.gexpect('choosedrop_index')
        
        if not len(cards):
            return False

        return g.process_action(DropCardIndex(target=self.target, cards=cards))
    
    def default_action(self):
        Game.getgame().players.gwrite(['choosedrop_index',[]])
        return False
        
class UseCard(ChooseAndDropCard): pass 
class DropUsedCard(DropCardIndex): pass

class DropCardStage(GenericAction):
    
    def __init__(self, target):
        self.target = target

    def apply_action(self):
        p = self.target
        life = p.gamedata.life
        n = len(p.gamedata.cards) - life
        if n<=0:
            return True
        g = Game.getgame()
        if not g.process_action(ChooseAndDropCard(p, cond = lambda cl: len(cl) == n)):
            g.process_action(DropCardIndex(p, cards=range(n)))
        
        return True
            
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
            if p is g.me:
                cl = p.gexpect('drawcards')
                cl = [Card.parse(i) for i in cl]
                p.gamedata.cards += cl
            else:
                p.gamedata.cards += [HiddenCard] * self.amount
        
        return True

class Heal(BaseAction):
    
    def __init__(self, target, amount=1):
        self.target = target
        self.amount = amount

    def apply_action(self):
        self.target.gamedata.life += self.amount
        if Game.CLIENT_SIDE:
            print 'Heal!'
        return True

class ActionStage(GenericAction):
    
    def __init__(self, target):
        self.target = target
    
    def default_action(self):
       Game.getgame().players.gwrite(['action', []])
       return True

    def apply_action(self):
        g = Game.getgame()
        p = self.target

        while True:
            if not len(p.gamedata.cards):
                break

            if Game.SERVER_SIDE:
                ins = p.gexpect('myaction')
                if ins == []:
                    g.players.gwrite(['action', ins])
                    break
                c = p.gamedata.cards[ins[0]]
                act = ins + [c]
                g.players.gwrite(['action', act])

            if Game.CLIENT_SIDE:
                me = g.me
                if p is me:
                    print 'Your life is %d' % p.gamedata.life
                    print 'Your cards is %s' % Endpoint.encode(p.gamedata.cards)
                    print 'Players: %s' % Endpoint.encode(g.players)
                    print 'Your instruction: ',
                    ins = raw_input().strip() # "$cardindex $targetindex"
                    if ins == '':
                        ins = []
                    else:
                        ins = [int(i) for i in ins.split(' ')]
                    p.gwrite(['myaction', ins])
                
                a = me.gexpect('action')
                if a == []:
                    break
                act = [a[0], a[1], Card.parse(a[2])]
            
            g.process_action(DropUsedCard(target=p, cards=[act[0]]))
            
            c = act[2]
            tg = g.players[act[1]]
            if c.type == 'attack':
                g.process_action(Attack(target=tg))
            elif c.type == 'heal':
                g.process_action(Heal(target=tg))
            else:
                continue
        
        return True
