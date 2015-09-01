# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCards, GenericAction, LaunchCard, UserAction
from ..actions import migrate_cards, user_choose_players, user_choose_cards
from ..cards import Card, AttackCard, Skill, t_None, PhysicalCard, Attack
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class Echo(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class EchoAction(UserAction):
    def __init__(self, source, target, card):
        self.source, self.target, self.card = source, target, card

    def apply_action(self):
        migrate_cards([self.card], self.target.cards, unwrap=True, is_bh=True)

        return True


class EchoHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.dead:
                return act

            if not tgt.has_skill(Echo):
                return act

            g = Game.getgame()
            pact = g.action_stack[-1]
            card = getattr(pact, 'associated_card', None)
            print card
            if not card or not card.is_card(PhysicalCard):
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            attack = card.is_card(AttackCard)
            pl = attack and user_choose_players(self, tgt, [p for p in g.players if not p.dead])
            p = pl[0] if pl else tgt

            g.process_action(EchoAction(tgt, p, card))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Resonance(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ResonanceDrawAction(DrawCards):
    pass


class ResonanceLaunchCard(LaunchCard):
    def apply_action(self):
        g = Game.getgame()
        if self.card.suit == self.suit:
            g.process_action(ResonanceDrawAction(self.source, 1))

        return super(ResonanceLaunchCard, self).apply_action()


class ResonanceAction(GenericAction):
    def __init__(self, source, target, suit):
        self.source, self.target, self.suit = source, target, suit

    def apply_action(self):
        src, tgt = self.source, self.target
        cards = user_choose_cards(self, src, ('cards', 'showncards'))
        if cards:
            c = cards[0]
            rlc = ResonanceLaunchCard(src, [tgt], c, bypass_check=True)
            rlc.suit = self.suit
            Game.getgame().process_action(rlc)

        return True

    def cond(self, cl):
        if len(cl) != 1:
            return False

        c = cl[0]
        if not c.associated_action:
            return False

        return issubclass(c.associated_action, Attack)

    def ask_for_action_verify(self, p, cl, tl):
        return ResonanceLaunchCard(self.source, [self.target], cl[0], bypass_check=True).can_fire()


class ResonanceHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Attack):
            src = act.source
            tgt = act.target

            if src.dead or tgt.dead:
                return act

            if not src.has_skill(Resonance):
                return act

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and p is not src]
            pl = user_choose_players(self, src, pl)

            if not pl:
                return act

            card = getattr(act, 'associated_card', None)
            suit = card.suit if card else Card.NOTSET

            g.process_action(ResonanceAction(pl[0], tgt, suit))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


@register_character
class Kyouko(Character):
    skills = [Echo, Resonance]
    eventhandlers_required = [EchoHandler, ResonanceHandler]
    maxlife = 3
