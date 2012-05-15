# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class SealingArraySkill(TreatAsSkill):
    treat_as = SealingArrayCard
    def check(self):
        cl = self.associated_cards
        if cl and cl[0].suit == Card.DIAMOND:
            return True
        return False

class Flight(GreenUFOSkill):
    increment = 1

class TributeTarget(Skill):
    associated_action = None
    target = t_None

class TributeAction(GenericAction):
    def apply_action(self):
        cl = self.associated_card.associated_cards
        tgt = self.target
        tgt.reveal(cl)
        migrate_cards(cl, tgt.cards)
        src = self.source
        src.tags['tribute_tag'] = src.tags['turn_count']
        return True

    def is_valid(self):
        p = self.source
        if p.tags.get('turn_count', 0) <= p.tags.get('tribute_tag', 0):
            return False
        return True

class Tribute(Skill):
    associated_action = TributeAction
    no_drop = True
    no_reveal = True
    def check(self):
        cl = self.associated_cards
        rst = cl and len(cl) == 1 and (
            cl[0].resides_in and
            cl[0].resides_in.type in (CardList.HANDCARD, CardList.SHOWNCARD, CardList.EQUIPS)
        )
        return rst

    @staticmethod
    def target(g, source, tl):
        tl = [t for t in tl if not t.dead and t.has_skill(TributeTarget)]
        try:
            tl.remove(source)
        except ValueError:
            pass
        return (tl[-1:], bool(len(tl)))

class ReimuHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            g = Game.getgame()
            for p in g.players:
                if not p.has_skill(TributeTarget):
                    p.skills.append(Tribute)
        elif evt_type == 'action_can_fire':
            act, valid = arg
            if not isinstance(act, LaunchCard): return arg
            c = act.card
            if not c.is_card(SealingArraySkill): return arg

            src = act.source
            if src.tags.get('turn_count', 0) <= src.tags.get('reimusa_tag', 0):
                return (act, False)
        elif evt_type == 'action_apply' and isinstance(arg, LaunchCard):
            c = arg.card
            if c.is_card(SealingArraySkill):
                src = arg.source
                src.tags['reimusa_tag'] = src.tags['turn_count']

        return arg

@register_character
class Reimu(Character):
    skills = [SealingArraySkill, Flight, TributeTarget]
    eventhandlers_required = [ReimuHandler]
    maxlife = 3
