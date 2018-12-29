# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import AskForCard, Damage, DrawCards, LaunchCard, UserAction, migrate_cards
from thb.actions import user_choose_players
from thb.cards.base import Skill, VirtualCard
from thb.cards.classes import Attack, AttackCard, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class Echo(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class EchoAction(UserAction):
    def __init__(self, source, target, card):
        self.source, self.target, self.card = source, target, card

    def apply_action(self):
        migrate_cards([self.card], self.target.cards, unwrap=True, is_bh=True)

        return True


class EchoHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            if tgt.dead:
                return act

            if not tgt.has_skill(Echo):
                return act

            g = self.game
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

            g.process_action(EchoAction(tgt, p, card))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Resonance(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
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
        g = self.game
        g.process_action(ResonanceLaunchCard(self.target, [self.victim], c, bypass_check=True))
        return True

    def ask_for_action_verify(self, p, cl, tl):
        return ResonanceLaunchCard(self.target, [self.victim], cl[0], bypass_check=True).can_fire()


class ResonanceHandler(THBEventHandler):
    interested = ['action_done']

    def handle(self, evt_type, act):
        if evt_type == 'action_done' and isinstance(act, Attack):
            src = act.source
            tgt = act.target

            if src.dead or tgt.dead:
                return act

            if not src.has_skill(Resonance):
                return act

            g = self.game
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
    eventhandlers = [EchoHandler, ResonanceHandler]
    maxlife = 4
