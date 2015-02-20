# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import PlayerRevive, UserAction, migrate_cards
from ..cards import Card, GreenUFOSkill, RejectCard, Skill, TreatAs, UFOSkill, t_None
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class Flight(GreenUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')

    @staticmethod
    def increment(src):
        for c in src.equips:
            if issubclass(c.equipment_skill, UFOSkill):
                return 0

        return 1


class SpiritualAttack(TreatAs, Skill):
    skill_category = ('character', 'active')
    treat_as = RejectCard

    def check(self):
        cl = self.associated_cards
        if not(cl and len(cl) == 1 and cl[0].color == Card.RED):
            return False

        c = cl[0]
        if c.resides_in is None or c.resides_in.type not in (
            'cards', 'showncards'
        ): return False

        return True


class TributeTarget(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
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

        tgt = self.target

        if tgt.dead: return False
        if len(tgt.cards) + len(tgt.showncards) >= tgt.maxlife: return False
        return True


class Tribute(Skill):
    associated_action = TributeAction
    skill_category = ('active',)
    no_drop = True
    no_reveal = True
    usage = 'handover'

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
    interested = (
        ('action_after', PlayerRevive),
        'game_begin', 'switch_character',
    )

    def handle(self, evt_type, arg):
        if evt_type == 'game_begin':
            self.add()

        elif evt_type == 'switch_character':
            cond = any([
                isinstance(p, Character) and p.has_skill(TributeTarget)
                for p in Game.getgame().players
            ])

            self.add() if cond else self.remove()

        elif evt_type == 'action_after' and isinstance(arg, PlayerRevive):
            self.add()

        return arg

    def add(self):
        g = Game.getgame()
        for p in g.players:
            if not isinstance(p, Character): continue
            if p.has_skill(TributeTarget): continue
            if not p.has_skill(Tribute):
                p.skills.append(Tribute)

    def remove(self):
        g = Game.getgame()
        for p in g.players:
            if not isinstance(p, Character): continue
            try:
                p.skills.remove(Tribute)
            except ValueError:
                pass


@register_character
class Reimu(Character):
    # skills = [SealingArraySkill, Flight, TributeTarget]
    skills = [SpiritualAttack, Flight]
    eventhandlers_required = []
    maxlife = 3
