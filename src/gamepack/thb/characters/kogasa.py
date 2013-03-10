# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Jolly(Skill):
    associated_action = None
    target = t_None

class Surprise(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        suit = user_choose_option(self, tgt)
        card = random_choose_card([src.cards, src.showncards])
        src.tags['surprise_tag'] = src.tags['turn_count']
        assert card
        g = Game.getgame()
        g.players.exclude(src).reveal(card)
        if card.suit != suit:
            dmg = Damage(src, tgt)
            dmg.associated_action = self
            g.process_action(dmg)
            rst = True
        else:
            rst = False

        if not tgt.dead:
            migrate_cards([card], tgt.cards)

        g.process_action(DrawCards(src, 1))

        return rst

    def is_valid(self):
        src = self.source
        if self.associated_card.associated_cards: return False
        if src.tags.get('turn_count', 0) <= src.tags.get('surprise_tag', 0):
            return False
        if not (src.cards or src.showncards):
            return False
        return True

class SurpriseSkill(Skill):
    associated_action = Surprise
    target = t_OtherOne
    def check(self):
        return not self.associated_cards

class JollyDrawCard(DrawCards):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.amount = 1

class JollyHandler(EventHandler):
    choose_player_target = t_One
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DrawCardStage):
            tgt = act.target

            if not tgt.has_skill(Jolly): return act

            g = Game.getgame()
            pl = user_choose_players(self, tgt, [p for p in g.players if not p.dead])
            if not pl: pl = [tgt]

            p = pl[0]

            g.process_action(JollyDrawCard(tgt, p))

        return act

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)

@register_character
class Kogasa(Character):
    skills = [SurpriseSkill, Jolly]
    eventhandlers_required = [JollyHandler]
    maxlife = 3
