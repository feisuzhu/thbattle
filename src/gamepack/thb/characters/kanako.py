# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DistributeCards, DrawCardStage, DrawCards, DropCards, UserAction
from ..actions import ask_for_action, ttags, user_choose_cards
from ..cards import Skill, t_None
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler, Game


# -- code --
class DivinityDrawCards(DrawCards):
    pass


class DivinityDropCards(DropCards):
    pass


class DivinityAction(UserAction):
    card_usage = 'drop'

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        self.amount = min(tgt.life, 4)
        g.process_action(DivinityDrawCards(tgt, self.amount))
        cl = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        cl = cl or (list(tgt.showncards) + list(tgt.cards) + list(tgt.equips))[:self.amount]
        g.players.reveal(cl)
        g.process_action(DivinityDropCards(tgt, cl))
        return True

    def cond(self, cl):
        if not len(cl) == self.amount:
            return False

        tgt = self.target

        if not all(c.resides_in in (tgt.cards, tgt.showncards, tgt.equips) for c in cl):
            return False

        from ..cards import VirtualCard
        if any(c.is_card(VirtualCard) for c in cl):
            return False

        return True


class DivinityHandler(EventHandler):
    interested = ('action_apply',)
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, DrawCardStage):
            tgt = act.target
            if not tgt.has_skill(Divinity):
                return act

            # if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            #     return act

            g = Game.getgame()
            g.process_action(DivinityAction(tgt, tgt))

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
    interested = ('card_migration',)
    card_usage = 'drop'

    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, cards, _from, to = arg
            if isinstance(act, (DistributeCards, DrawCardStage, DivinityDrawCards)):
                return arg

            if to is None or not to.owner:
                return arg

            if to.type not in ('cards', 'showncards', 'equips'):
                return arg

            src = to.owner

            if _from is not None and _from.owner is src:
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


@register_character_to('common', '-kof')
class Kanako(Character):
    skills = [Divinity, Virtue]
    eventhandlers_required = [DivinityHandler, VirtueHandler]
    maxlife = 4
