# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from gamepack.thb.actions import DropCardStage, GenericAction, LifeLost, migrate_cards
from gamepack.thb.actions import random_choose_card, user_choose_cards, user_choose_players
from gamepack.thb.cards import Skill, t_None
from gamepack.thb.characters.baseclasses import Character, register_character


# -- code --
class Shipwreck(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ShipwreckChooseCard(GenericAction):
    # Hack
    card_usage = 'handover'

    def apply_action(self):
        tgt = self.target
        c, = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips')) or (None,)
        c = c or random_choose_card([tgt.cards, tgt.showncards, tgt.equips])
        self.card = c
        return True

    def cond(self, cl):
        tgt = self.target
        if not len(cl) == 1:
            return False

        if not all(c.resides_in in (tgt.cards, tgt.showncards, tgt.equips) for c in cl):
            return False

        if any(c.is_card(Skill) for c in cl):
            return False

        return True


class ShipwreckBrokenScoop(GenericAction):

    def apply_action(self):
        return True


class ShipwreckEffect(GenericAction):

    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        cards = self.cards

        tgt.reveal(cards)
        migrate_cards(cards, tgt.cards)

        self.life_lost = life_lost = len(tgt.cards) + len(tgt.showncards) > tgt.life
        life_lost and g.process_action(LifeLost(src, tgt, 1))

        return True


class ShipwreckDropCardStage(DropCardStage):
    card_usage = 'handover'

    def apply_action(self):
        tgt, victim = self.target, self.victim
        if tgt.dead: return False

        g = Game.getgame()

        sel = ShipwreckChooseCard(tgt, victim)
        g.process_action(sel)
        c = sel.card

        tgt.reveal(c)
        migrate_cards([c], tgt.cards, unwrap=True)

        n = self.dropn
        if n <= 0:
            g.process_action(ShipwreckBrokenScoop(tgt, victim))
            return True

        g = Game.getgame()
        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        if not cards:
            from itertools import chain
            cards = list(chain(tgt.cards, tgt.showncards))[min(-n, 0):]

        g.process_action(ShipwreckEffect(tgt, victim, cards))

        return True

    def init(self, victim):
        self.victim = victim
        self.dropn += 1


class ShipwreckHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('DecayDamageHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(Shipwreck):
                return act

            candidates = [p for p in g.players if not p.dead and (p.cards or p.showncards or p.equips)]
            victim, = user_choose_players(self, tgt, candidates) or (None,)
            if not victim:
                return act

            act.__class__ = ShipwreckDropCardStage
            act.init(victim=victim)

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


# @register_character
class Minamitsu20150818(Character):
    skills = [Shipwreck]
    eventhandlers_required = [ShipwreckHandler]
    maxlife = 4
