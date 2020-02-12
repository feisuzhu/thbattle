# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game, user_input
from game.base import EventHandler
from thb.actions import AskForCard, Damage, DrawCards, LaunchCard, UserAction
from thb.actions import migrate_cards, user_choose_players
from thb.cards import Attack, AttackCard, Skill, VirtualCard, t_None, PhysicalCard, TreatAs
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class Echo(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class EchoPlaceholderCard(TreatAs, VirtualCard):

    def __init__(self, player, card):
        super(EchoPlaceholderCard, self).__init__(player)
        self.treat_as = card.__class__
        self.suit     = card.suit
        self.number   = card.number

    def check(self):
        return True


class EchoAction(UserAction):
    def __init__(self, source, target, launch_action, card):
        self.source, self.target = source, target
        self.launch_action, self.card = launch_action, card

    def apply_action(self):
        tgt = self.target

        lc = self.launch_action
        if lc and isinstance(lc.card, PhysicalCard):
            mock = EchoPlaceholderCard(tgt, lc.card)
            # HACK: should impl in LaunchCard
            lc.card = mock
            lc.card_action.associated_card = mock

        migrate_cards([self.card], tgt.cards, unwrap=True, is_bh=True)

        return True


class EchoHandler(EventHandler):
    interested = ('action_after',)
    execute_after = (
        'DyingHandler',
        'AyaRoundfanHandler',
        'NenshaPhoneHandler',
    )

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
            if not card:
                return act

            if not card.detached or card.unwrapped:
                return act

            if not VirtualCard.unwrap([card]):
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            attack = card.is_card(AttackCard)
            pl = attack and user_choose_players(self, tgt, [p for p in g.players if not p.dead])
            p = pl[0] if pl else tgt

            for lc in reversed(g.action_stack):
                if isinstance(lc, LaunchCard) and lc.card_action is pact:
                    break
            else:
                lc = None

            g.process_action(EchoAction(tgt, p, lc, card))

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
    pass


class ResonanceAction(AskForCard):
    card_usage = 'launch'

    def __init__(self, source, target, victim):
        AskForCard.__init__(self, source, target, AttackCard)
        self.source = source
        self.target = target
        self.victim = victim

    def process_card(self, c):
        g = Game.getgame()
        g.process_action(ResonanceLaunchCard(self.target, [self.victim], c, bypass_check=True))
        return True

    def ask_for_action_verify(self, p, cl, tl):
        return ResonanceLaunchCard(self.target, [self.victim], cl[0], bypass_check=True).can_fire()


class ResonanceHandler(EventHandler):
    interested = ('action_done',)

    def handle(self, evt_type, act):
        if evt_type == 'action_done' and isinstance(act, Attack):
            src = act.source
            tgt = act.target

            if act.cancelled or src.dead or tgt.dead:
                return act

            if not src.has_skill(Resonance):
                return act

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and p not in (src, tgt)]

            if not pl:
                return act

            pl = user_choose_players(self, src, pl)

            if not pl:
                return act

            g.process_action(ResonanceAction(src, pl[0], tgt))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


@register_character_to('common')
class Kyouko(Character):
    skills = [Echo, Resonance]
    eventhandlers_required = [EchoHandler, ResonanceHandler]
    maxlife = 4
