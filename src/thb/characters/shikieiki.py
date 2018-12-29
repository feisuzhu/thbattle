# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import Damage, FatetellMalleateHandler, MigrateCardsTransaction, UseCard
from thb.actions import UserAction, detach_cards, migrate_cards, user_choose_cards
from thb.cards.base import Skill
from thb.cards.classes import t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class Trial(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class Majesty(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class TrialAction(UseCard):
    def __init__(self, source, target, ft, card):
        self.source, self.target, self.ft, self.card = \
            source, target, ft, card

    def apply_action(self):
        g = self.game
        c = self.card
        ft = self.ft
        g.players.exclude(self.source).reveal(c)
        with MigrateCardsTransaction(self) as trans:
            migrate_cards([ft.card], g.deck.droppedcards, unwrap=True, trans=trans, is_bh=True)
            detach_cards([c], trans=trans)
            self.ft.set_card(c, self)

        return True


class TrialHandler(THBEventHandler):
    interested = ['fatetell']
    arbiter = FatetellMalleateHandler
    card_usage = 'use'

    def handle(self, p, act):
        if p.dead: return act
        if not p.has_skill(Trial): return act

        self.act = act

        if not user_input([p], ChooseOptionInputlet(self, (False, True))):
            return act

        cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))

        if cards:
            c = cards[0]
            self.game.process_action(TrialAction(p, act.target, act, c))

        return act

    def cond(self, cards):
        return len(cards) == 1 and not cards[0].is_card(Skill)

    def ask_for_action_verify(self, p, cl, tl):
        act = self.act
        return TrialAction(p, act.target, act, cl[0]).can_fire()


class MajestyAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
        if not c: return False
        src.reveal(c)
        migrate_cards([c], src.cards)
        return True


class MajestyHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, Damage): return act
        src, tgt = act.source, act.target
        if not src: return act

        cats = [
            src.cards, src.showncards, src.equips
        ]

        if not any(cats): return act
        if tgt.dead: return act
        if not tgt.has_skill(Majesty): return act

        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        self.game.process_action(MajestyAction(tgt, src))

        return act


@register_character_to('common')
class Shikieiki(Character):
    skills = [Trial, Majesty]
    eventhandlers = [TrialHandler, MajestyHandler]
    maxlife = 3
