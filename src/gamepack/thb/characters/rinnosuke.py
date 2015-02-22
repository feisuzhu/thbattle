# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards, UserAction
from ..cards import Heal, Skill, t_None, t_OtherOne
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class Psychopath(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class NetoruAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        src.tags['netoru_tag'] = src.tags['turn_count']
        tgt = self.target
        g.process_action(Heal(src, tgt))
        if src.life < src.maxlife:
            g.process_action(Heal(src, src))
        return True

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.tags['netoru_tag'] >= src.tags['turn_count']:
            return False
        return not (tgt.dead or tgt.life >= tgt.maxlife)


class Netoru(Skill):
    associated_action = NetoruAction
    skill_category = ('character', 'active')
    target = t_OtherOne
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return cl and len(cl) == 2 and all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards')
            for c in cl
        )


class PsychopathDrawCards(DrawCards):
    pass


class PsychopathHandler(EventHandler):
    interested = ('card_migration',)
    def handle(self, evt_type, args):
        if evt_type == 'card_migration':
            act, cards, _from, to = args
            if _from is not None and _from.type == 'equips':
                src = _from.owner
                if src.has_skill(Psychopath) and not src.dead:
                    g = Game.getgame()
                    g.process_action(PsychopathDrawCards(src, len(cards)*2))
        return args


@register_character
class Rinnosuke(Character):
    skills = [Netoru, Psychopath]
    eventhandlers_required = [PsychopathHandler]
    maxlife = 3
