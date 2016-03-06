# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import ActionShootdown, EventHandler, Game, user_input
from thb.actions import Damage, DrawCards, ForEach, LaunchCard, Reforge, UserAction
from thb.actions import migrate_cards, random_choose_card, ttags, user_choose_players
from thb.cards import Card, Skill, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character
from thb.inputlets import ChooseIndividualCardInputlet, ChooseOptionInputlet


# -- code --
class MindReadEffect(UserAction):
    def apply_action(self):
        tgt = self.target
        assert tgt.cards
        c = random_choose_card([tgt.cards])
        g = Game.getgame()
        g.players.reveal(c)
        tgt.tags['mind_hack_effect-%s' % g.turn_count] = True
        migrate_cards([c], tgt.showncards)
        return True


class MindReadAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        ttags(src)['mind_read'] = True
        return g.process_action(MindReadEffect(src, tgt))

    def is_valid(self):
        src, tgt = self.source, self.target
        return not ttags(src)['mind_read'] and bool(tgt.cards)


class MindReadLimit(ActionShootdown):
    pass


class MindReadHandler(EventHandler):
    interested = ('action_shootdown', )

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown' and isinstance(act, LaunchCard):
            src = act.source
            g = Game.getgame()
            if not src.tags['mind_hack_effect-%s' % g.turn_count]: return act
            if any(c for c in VirtualCard.unwrap([act.card]) if c.color == Card.BLACK and c in src.showncards):
                raise MindReadLimit

        return act


class MindRead(Skill):
    associated_action = MindReadAction
    skill_category = ('character', 'active')

    @staticmethod
    def target(g, source, tl):
        tl = [t for t in tl if not t.dead and t.cards]
        try:
            tl.remove(source)
        except ValueError:
            pass

        return (tl[-1:], bool(len(tl)))

    def check(self):
        cl = self.associated_cards
        return not cl


class Rosa(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class RosaHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            src, tgt = act.source, act.target

            if ForEach.is_group_effect(pact): return act
            if src is tgt: return act

            self.process(src, tgt)
            self.process(tgt, src)

        return act

    def process(self, src, tgt):
        if src is None or tgt is None:
            return

        if not src.has_skill(Rosa):
            return

        if not tgt.cards:
            return

        if user_input([src], ChooseOptionInputlet(self, (False, True))):
            g = Game.getgame()
            g.process_action(MindReadEffect(src, tgt))


class HeartfeltFancy(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class HeartfeltFancyAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        src, tgt, cl = self.source, self.target, self.cards
        g = Game.getgame()

        c = user_input([src], ChooseIndividualCardInputlet(self, cl)) or random_choose_card([cl])
        g.process_action(Reforge(src, tgt, c))

        '''
        candidates = [i for i in g.players if not i.dead]
        p, = user_choose_players(self, src, candidates) or (src,)

        g.process_action(DrawCards(p, 1))
        '''

        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class HeartfeltFancyHandler(EventHandler):
    interested = ('card_migration', )

    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, cards, _from, to, is_bh = arg
            if not (to is not None and to.owner and to is to.owner.showncards):
                return arg

            if not len(to) >= 2:
                return arg

            g = Game.getgame()
            for p in g.players:
                if p.dead: continue
                if not p.has_skill(HeartfeltFancy): continue
                if not user_input([p], ChooseOptionInputlet(self, (False, True))): continue
                g.process_action(HeartfeltFancyAction(p, to.owner, to))

        return arg


# @register_character
class Satori20150804(Character):
    skills = [MindRead, Rosa, HeartfeltFancy]
    eventhandlers_required = [
        MindReadHandler,
        RosaHandler,
        HeartfeltFancyHandler,
    ]
    maxlife = 3
