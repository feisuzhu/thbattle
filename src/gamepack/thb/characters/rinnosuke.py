# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, UserAction
from ..cards import Skill, Heal, t_None, t_OtherOne


class Psychopath(Skill):
    associated_action = None
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
