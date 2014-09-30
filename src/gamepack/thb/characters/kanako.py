# -*- coding: utf-8 -*-

from ..actions import DrawCardStage, DrawCards, DropCards, ask_for_action
from ..actions import UserAction, ttags
from ..cards import Skill, t_None
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


class DivinityDrawCardStage(DrawCardStage):
    pass


class DivinityHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if not tgt.has_skill(Divinity):
                return act

            act.__class__ = DivinityDrawCardStage
            act.amount = min(tgt.life, 4)

        return act


class Divinity(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class VirtueAction(UserAction):

    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(DropCards(src, self.cards))
        g.process_action(DrawCards(tgt, 1))
        ttags(g.current_turn)['virtue'] = True
        return True


class VirtueHandler(EventHandler):
    card_usage = 'drop'

    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, cards, _from, to = arg
            if isinstance(act, DrawCardStage):
                return arg

            if not to or not to.owner:
                return arg

            if to.type not in ('cards', 'showncards', 'equips'):
                return arg

            src = to.owner

            if _from and _from.owner is src:
                return arg

            if not src.has_skill(Virtue):
                return arg

            g = Game.getgame()

            if not hasattr(g, 'current_turn'):
                return arg

            if ttags(g.current_turn)['virtue']:
                return arg

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and p is not src]
            _, rst = ask_for_action(self, [src], ('cards', 'showncards'), pl)
            if not rst:
                return arg

            cl, pl = rst

            g.process_action(VirtueAction(src, pl[0], cl))

        return arg

    def cond(self, cl):
        return len(cl) == 1 and cl[0].resides_in.type in ('cards', 'showncards')

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Virtue(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


@register_character
class Kanako(Character):
    skills = [Divinity, Virtue]
    eventhandlers_required = [DivinityHandler, VirtueHandler]
    maxlife = 4
