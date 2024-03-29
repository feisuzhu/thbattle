# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import cast

# -- third party --
# -- own --
from thb.actions import Damage, DrawCards, DropCardStage, DropCards, FinalizeStage, GenericAction
from thb.actions import MigrateCardsTransaction, PlayerTurn, UserAction, random_choose_card
from thb.actions import user_choose_players
from thb.cards.base import Skill, VirtualCard
from thb.cards.classes import t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class AutumnWindEffect(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target

        g = self.game

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]
        card = g.user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        card = card or random_choose_card(g, cats)
        if not card:
            return False

        self.card = card
        g.players.exclude(tgt).reveal(card)
        g.process_action(DropCards(src, tgt, cards=[card]))
        return True

    def is_valid(self):
        tgt = self.target
        catnames = ('cards', 'showncards', 'equips')
        return not tgt.dead and any(getattr(tgt, i) for i in catnames)


class AutumnWindAction(UserAction):
    def __init__(self, source, target_list):
        self.source = source
        self.target = source
        self.target_list = target_list

    def apply_action(self):
        g = self.game
        src = self.source

        for p in self.target_list:
            g.process_action(AutumnWindEffect(src, p))

        return True


class AutumnWindHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DropCardStage):
            self.n = n = act.dropn
            if n <= 0:
                return act

            tgt = act.target
            if not tgt.has_skill(AutumnWind):
                return act

            g = self.game
            if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            candidates = [
                p for p in g.players if
                p is not tgt and
                (p.cards or p.showncards or p.equips) and
                not p.dead
            ]

            pl = candidates and user_choose_players(self, tgt, candidates)
            if not pl:
                return act

            g.process_action(AutumnWindAction(tgt, pl))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[:self.n], True)


class AutumnWind(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


class DecayDrawCards(DrawCards):
    pass


class DecayDrawCardHandler(THBEventHandler):
    interested = ['post_card_migration']
    execute_before = ['LuckHandler']

    def handle(self, evt_type, arg):
        if evt_type != 'post_card_migration':
            return arg

        g = self.game

        try:
            me = PlayerTurn.get_current(g).target
        except IndexError:
            return arg

        if me is None: return arg
        if me.dead: return arg
        if not me.has_skill(Decay): return arg

        trans = cast(MigrateCardsTransaction, arg)

        candidates = {}

        for m in trans.movements:
            src = m.fr.owner
            if not src: continue
            if m.card.is_card(VirtualCard): continue
            if m.fr.type not in ('cards', 'showncards'): continue
            if src.cards or src.showncards: continue
            if src.dead: continue
            if src is me: continue
            candidates[src] = 1

        if not candidates:
            return arg

        g.process_action(DecayDrawCards(me, len(candidates)))

        return arg


class DecayAction(UserAction):
    def apply_action(self):
        tgt = self.target
        tgt.tags['shizuha_decay'] = True
        return True


class DecayEffect(UserAction):
    def __init__(self, source, target, dcs):
        self.source = source
        self.target = target
        self.dcs = dcs

    def apply_action(self):
        self.dcs.dropn = max(1, self.dcs.dropn + 1)
        return True


class DecayDamageHandler(THBEventHandler):
    interested = ['action_after', 'action_before']
    execute_after = [
        'DyingHandler',
        'AyaRoundfanHandler',
        'NenshaPhoneHandler',
        'SuwakoHatHandler',
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (tgt and tgt.has_skill(Decay)):
                return act

            g = self.game

            try:
                cur = PlayerTurn.get_current(g).target
            except IndexError:
                # Yugi AssaultKOF & Yuuka Sadist
                return act

            if cur is tgt: return act
            g.process_action(DecayAction(src, cur))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            t = tgt.tags
            if not t['shizuha_decay']: return act

            t['shizuha_decay'] = False
            g = self.game
            g.process_action(DecayEffect(tgt, tgt, act))

        return act


class DecayFadeHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, FinalizeStage):
            tgt = act.target
            if tgt.tags['shizuha_decay']:
                tgt.tags['shizuha_decay'] = False

        return act


class Decay(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


@register_character_to('common')
class Shizuha(Character):
    skills = [Decay, AutumnWind]
    eventhandlers = [DecayDamageHandler, DecayDrawCardHandler, DecayFadeHandler, AutumnWindHandler]
    maxlife = 3
