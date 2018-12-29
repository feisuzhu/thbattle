# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import ActionStage, DropCards, ShowCards, UserAction, migrate_cards
from thb.actions import user_choose_cards
from thb.cards.base import Card, Skill
from thb.cards.classes import t_None, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, HopeMaskInputlet, HopeMaskKOFInputlet
from thb.mode import THBEventHandler


# -- code --
class BaseHopeMaskAction(UserAction):

    def apply_action(self):
        tgt = self.target
        g = self.game
        n = 1 + tgt.maxlife - tgt.life
        cards = g.deck.getcards(n)

        tgt.reveal(cards)
        putback, acquire = user_input([tgt], self.inputlet_cls(self, cards), timeout=20)
        for c in acquire:
            c.detach()

        assert not putback or set(putback) == set(g.deck.getcards(len(putback)))

        deck = g.deck.cards
        for i, c in enumerate(putback):
            deck[i] = c

        assert not putback or putback == g.deck.getcards(len(putback))

        if acquire:
            g.process_action(ShowCards(tgt, acquire))
            migrate_cards(acquire, tgt.cards)

        self.acquire = acquire

        return True


class HopeMaskAction(BaseHopeMaskAction):
    inputlet_cls = HopeMaskInputlet


class HopeMaskKOFAction(BaseHopeMaskAction):
    inputlet_cls = HopeMaskKOFInputlet


class BaseHopeMaskHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            tgt = act.target
            if not tgt.has_skill(self.skill): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act
            self.game.process_action(self.action(tgt, tgt))

        return act


class HopeMask(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class HopeMaskKOF(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class HopeMaskHandler(BaseHopeMaskHandler):
    skill  = HopeMask
    action = HopeMaskAction


class HopeMaskKOFHandler(BaseHopeMaskHandler):
    skill  = HopeMaskKOF
    action = HopeMaskKOFAction


class BaseDarkNohAction(UserAction):
    card_usage = 'drop'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game

        src.tags['darknoh_tag'] = src.tags['turn_count']
        sk = self.associated_card
        card = sk.associated_cards[0]
        self.card = card
        migrate_cards([sk], tgt.showncards, unwrap=True)
        self.n = n = len(tgt.cards) + len(tgt.showncards) - tgt.life
        if n <= 0: return True

        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        if not cards:
            cl = list(tgt.cards) + list(tgt.showncards)
            try:
                cl.remove(card)
            except Exception:
                pass

            cards = cl[:n]

        g.players.reveal(cards)
        g.process_action(DropCards(src, tgt, cards))

        return True

    def cond(self, cards):
        if len(cards) != self.n or self.card in cards:
            return False

        if any([c.is_card(Skill) for c in cards]):
            return False

        return True


class DarkNohAction(BaseDarkNohAction):

    def is_valid(self):
        src = self.source
        tgt = self.target

        if src.tags['darknoh_tag'] >= src.tags['turn_count']:
            return False

        if src.life > tgt.life:
            return False

        return True


class DarkNohKOFAction(BaseDarkNohAction):

    def is_valid(self):
        src = self.source
        tgt = self.target

        if src.tags['darknoh_tag'] > 0:
            return False

        if src.life > tgt.life:
            return False

        return True


class BaseDarkNoh(Skill):
    no_drop = True
    skill_category = ['character', 'active']
    target = t_OtherOne
    usage = 'handover'

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if c.resides_in.type not in ('cards', 'showncards', 'equips'): return False
        if c.suit not in (Card.SPADE, Card.CLUB): return False
        return True


class DarkNoh(BaseDarkNoh):
    associated_action = DarkNohAction


class DarkNohKOF(BaseDarkNoh):
    associated_action = DarkNohKOFAction


@register_character_to('common', '-kof')
class Kokoro(Character):
    skills = [HopeMask, DarkNoh]
    eventhandlers = [HopeMaskHandler]
    maxlife = 3


@register_character_to('kof')
class KokoroKOF(Character):
    skills = [HopeMaskKOF, DarkNohKOF]
    eventhandlers = [HopeMaskKOFHandler]
    maxlife = 3
