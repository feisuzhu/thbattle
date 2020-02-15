# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, Type

# -- third party --
# -- own --
from thb.actions import Damage, DrawCardStage, DrawCards, DropCards, FinalizeStage, ForEach
from thb.actions import LaunchCard, ShowCards, UserAction, migrate_cards, random_choose_card, ttags
from thb.actions import user_choose_cards, user_choose_players
from thb.cards.base import Card, Skill, VirtualCard
from thb.cards.classes import AttackCard, DuelCard, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class KanakoFaithCheers(UserAction):
    def apply_action(self):
        return self.game.process_action(DrawCards(self.target, 1))


class KanakoFaithAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class KanakoFaithDuel(TreatAs, VirtualCard):
    treat_as = DuelCard


class KanakoFaithCounteract(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        g.process_action(KanakoFaithCounteractPart1(src, tgt))
        g.process_action(KanakoFaithCounteractPart2(src, tgt))
        return True


class KanakoFaithCounteractPart1(UserAction):

    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]

        card = g.user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        card = card or random_choose_card(g, cats)

        assert card
        self.card = card

        g.players.reveal(card)
        g.process_action(DropCards(src, tgt, [card]))
        return True


class KanakoFaithCounteractPart2(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game

        choice = g.user_input([tgt], ChooseOptionInputlet(self, ('duel', 'attack')))

        cls: Type[Any]
        if choice == 'duel':
            cls = KanakoFaithDuel
        elif choice == 'attack':
            cls = KanakoFaithAttack
        else:
            cls = KanakoFaithAttack

        g.process_action(LaunchCard(tgt, [src], cls(tgt), bypass_check=True))

        return True


class KanakoFaithEffect(UserAction):
    card_usage = 'drop'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game

        has_card = src.cards or src.showncards or src.equips

        if has_card and g.user_input([tgt], ChooseOptionInputlet(self, ('drop', 'draw'))) == 'drop':
            g.process_action(KanakoFaithCounteract(tgt, src))
        else:
            g.process_action(KanakoFaithCheers(tgt, src))

        return True


class KanakoFaithAction(ForEach):
    action_cls = KanakoFaithEffect

    def prepare(self):
        self.source.tags['kanako_faith'] = True

    def is_valid(self):
        return not self.source.tags['kanako_faith']


class KanakoFaith(Skill):
    associated_action = KanakoFaithAction
    skill_category = ['character', 'active', 'once']

    def check(self):
        return not self.associated_cards

    @staticmethod
    def target(g, p, tl):
        l = g.players.rotate_to(p)
        del l[0]

        dists = LaunchCard.calc_raw_distance(p, AttackCard())
        return ([t for t in l if not t.dead and dists[t] <= 1], True)


class VirtueAction(UserAction):
    card_usage = 'handover'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        g.process_action(DrawCards(tgt, 2))

        cl = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        c = cl[0] if cl else random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])

        if not c: return False

        g.players.reveal(c)
        g.process_action(ShowCards(tgt, [c]))
        migrate_cards([c], src.cards)

        if c.suit == Card.HEART:
            g.process_action(DrawCards(src, 1))

        self.card = c

        return True

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)


class VirtueHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled:
                return act

            tgt = act.target
            if not tgt.has_skill(Virtue):
                return act

            g = self.game
            pl = [p for p in g.players if not p.dead and p is not tgt]
            pl = pl and user_choose_players(self, tgt, pl)
            if not pl:
                return act

            act.cancelled = True
            g.process_action(VirtueAction(tgt, pl[0]))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class KanakoFaithKOF(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class KanakoFaithKOFAction(DrawCards):
    pass


class KanakoFaithKOFHandler(THBEventHandler):
    interested = ['action_before', 'action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FinalizeStage):
            tgt = act.target
            if not tgt.has_skill(KanakoFaithKOF):
                return act

            g = self.game
            op = g.get_opponent(tgt)

            if tgt.life > op.life or ttags(tgt)['kanako_faith_kof']:
                n = tgt.life - (len(tgt.cards) + len(tgt.showncards))
                if n > 0:
                    g.process_action(KanakoFaithKOFAction(tgt, n))

        elif evt_type == 'action_apply' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            g = self.game

            if src and src.has_skill(KanakoFaithKOF) and tgt is g.get_opponent(src):
                ttags(src)['kanako_faith_kof'] = True

        return act


class Virtue(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


@register_character_to('common', '-kof')
class Kanako(Character):
    skills = [Virtue, KanakoFaith]
    eventhandlers = [VirtueHandler]
    maxlife = 4


# @register_character_to('kof')
class KanakoKOF(Character):
    skills = [KanakoFaithKOF]
    eventhandlers = [KanakoFaithKOFHandler]
    maxlife = 4
