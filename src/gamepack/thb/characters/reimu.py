# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import migrate_cards, PlayerRevive, UserAction
from ..cards import Card, Skill, TreatAsSkill, RejectCard, GreenUFOSkill, UFOSkill, t_None


class Flight(GreenUFOSkill):
    @staticmethod
    def increment(src):
        for c in src.equips:
            if issubclass(c.equipment_skill, UFOSkill):
                return 0

        return 1


class SpiritualAttack(TreatAsSkill):
    treat_as = RejectCard

    def check(self):
        cl = self.associated_cards
        if cl and len(cl) == 1 and cl[0].color == Card.RED:
            return True

        return False


class TributeTarget(Skill):
    associated_action = None
    target = t_None


class TributeAction(UserAction):
    def apply_action(self):
        cl = self.associated_card.associated_cards
        tgt = self.target
        tgt.reveal(cl)
        migrate_cards([self.associated_card], tgt.cards, unwrap=True)
        src = self.source
        src.tags['tribute_tag'] = src.tags['turn_count']
        return True

    def is_valid(self):
        p = self.source
        if p.tags.get('turn_count', 0) <= p.tags.get('tribute_tag', 0):
            return False
        if self.target.dead:
            return False
        return True


class Tribute(Skill):
    associated_action = TributeAction
    no_drop = True
    no_reveal = True

    def check(self):
        cl = self.associated_cards
        rst = cl and len(cl) == 1 and (
            cl[0].resides_in is not None and
            cl[0].resides_in.type in ('cards', 'showncards')
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


class TributeHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            self.add()

        elif evt_type == 'kof_next_character':
            if any(p.has_skill(TributeTarget) for p in Game.getgame().players):
                self.add()
            else:
                self.remove()

        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            self.add()

        return arg

    def add(self):
        g = Game.getgame()
        for p in g.players:
            if not p.has_skill(TributeTarget) and not p.has_skill(Tribute):
                p.skills.append(Tribute)

    def remove(self):
        g = Game.getgame()
        for p in g.players:
            try:
                p.skills.remove(Tribute)
            except ValueError:
                pass


@register_character
class Reimu(Character):
    #skills = [SealingArraySkill, Flight, TributeTarget]
    skills = [SpiritualAttack, Flight, TributeTarget]
    eventhandlers_required = [TributeHandler]
    maxlife = 3
