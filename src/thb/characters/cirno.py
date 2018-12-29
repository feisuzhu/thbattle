# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import Damage, DropCards, GenericAction, LaunchCard, LifeLost, UserAction
from thb.actions import random_choose_card, ttags, user_choose_cards
from thb.cards.base import Skill, VirtualCard
from thb.cards.classes import AttackCard, DuelCard, t_None, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class CirnoDropCards(GenericAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        src, tgt = self.source, self.target
        cards = self.cards

        g = self.game
        g.players.reveal(cards)
        g.process_action(DropCards(src, tgt, cards))
        return True


class BakadesuAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        src, tgt = self.source, self.target
        ttags(src)['bakadesu'] = True

        cl = user_choose_cards(self, tgt, ('cards', 'showncards'))
        g = self.game
        if cl:
            g.process_action(LaunchCard(tgt, [src], cl[0]))
        else:
            c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
            c = c or random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
            c and g.process_action(CirnoDropCards(src, tgt, [c]))

        return True

    def is_valid(self):
        src, tgt = self.source, self.target
        if not LaunchCard(tgt, [src], AttackCard()).can_fire():
            return False

        return not ttags(src)['bakadesu']

    def cond(self, cl):
        if len(cl) != 1:
            return False
        c = cl[0]

        return c.is_card(AttackCard) and (
            c.resides_in is not None and c.resides_in.type in ('cards', 'showncards')
        )

    def ask_for_action_verify(self, p, cl, tl):
        src, tgt = self.source, self.target
        return LaunchCard(tgt, [src], cl[0]).can_fire()


class Bakadesu(Skill):
    associated_action = BakadesuAction
    skill_category = ['character', 'active']
    target = t_OtherOne

    def check(self):
        return not self.associated_cards


class PerfectFreeze(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class PerfectFreezeAction(UserAction):
    card_usage = 'drop'

    def __init__(self, source, target, damage):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        self.damage.cancelled = True

        src, tgt = self.source, self.target
        g = self.game
        cl = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        c = cl[0] if cl else random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])

        if c:
            damage = c.resides_in is not tgt.equips
            g.process_action(CirnoDropCards(src, tgt, [c]))

            if damage:
                g.process_action(LifeLost(src, tgt, 1))

        return True

    def cond(self, cl):
        if len(cl) != 1:
            return False

        if cl[0].is_card(VirtualCard):
            return False

        return True

    def ask_for_action_verify(self, p, cl, tl):
        return CirnoDropCards(self.source, self.target, cl).can_fire()


class PerfectFreezeHandler(THBEventHandler):
    interested = ['action_before']

    execute_after = [
        'RepentanceStickHandler',
        'AyaRoundfanHandler',
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled:
                return act

            src, tgt = act.source, act.target
            if not (src and src.has_skill(PerfectFreeze)):
                return act

            g = self.game
            for lc in reversed(g.action_stack):
                if isinstance(lc, LaunchCard):
                    break
            else:
                return act

            if src is not lc.source:
                return act

            c = lc.card
            if not c.is_card(AttackCard) and not c.is_card(DuelCard):
                return act

            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(PerfectFreezeAction(src, tgt, act))

        return act


@register_character_to('common')
class Cirno(Character):
    skills = [Bakadesu, PerfectFreeze]
    eventhandlers = [PerfectFreezeHandler]
    maxlife = 4
