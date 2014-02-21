# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import GenericAction, Damage, user_choose_cards
from ..actions import DropCards, PlayerTurn
from ..cards import Skill, t_None, InstantSpellCardAction, Reject, SpellCardAction
from ..inputlets import ProphetInputlet, ChooseOptionInputlet


class Prophet(Skill):
    associated_action = None
    target = t_None


class ExtremeIntelligence(Skill):
    associated_action = None
    target = t_None


class ProphetAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        n = min(len([p for p in g.players if not p.dead]), 5)
        cards = g.deck.getcards(n)

        assert cards == g.deck.getcards(n)

        tgt.reveal(cards)

        upcards, downcards = user_input([tgt], ProphetInputlet(self, cards), timeout=45) or [range(n), []]

        deck = g.deck.cards
        for i, c in enumerate(downcards):
            deck[i] = c
        deck.rotate(-len(downcards))

        for i, c in enumerate(upcards):
            deck[i] = c

        assert g.deck.getcards(len(upcards)) == upcards

        return True


class ProphetHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Prophet): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act
            Game.getgame().process_action(ProphetAction(tgt, tgt))

        return act


class ExtremeIntelligenceAction(GenericAction):
    def __init__(self, source, target, act):
        self.source, self.target, self.action = \
            source, act.target, act

    def apply_action(self):
        p = self.source
        cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
        if not cards: return False
        p.tags['ran_ei'] = p.tags['turn_count'] + 1
        g = Game.getgame()
        g.process_action(DropCards(p, cards))

        act = self.action
        nact = act.__class__(source=p, target=act.target)
        try:
            nact.target_list = act.target_list
        except AttributeError:
            pass

        try:
            # this is for actions triggered by ForEach action.
            # Well, actually it's for Harvest since only this
            # uses the attrib
            nact.parent_action = act.parent_action
        except AttributeError:
            pass

        try:
            nact.associated_card = act.associated_card
        except AttributeError:
            pass

        g.process_action(nact)
        return True

    usage = 'drop'
    def cond(self, cl):
        return len(cl) == 1


class ExtremeIntelligenceHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, InstantSpellCardAction):
            if isinstance(act, Reject): return act
            g = Game.getgame()
            target = g.current_turn

            for p in g.players.exclude(target):
                if p.dead: continue
                if not p.has_skill(ExtremeIntelligence): continue
                if p.tags['ran_ei'] >= p.tags['turn_count'] + 1: continue

                try:
                    tl = act.target_list
                except AttributeError:
                    tl = [act.target]
                if any(t.dead for t in tl): return act

                if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                    continue

                g.process_action(ExtremeIntelligenceAction(p, act.target, act))

        elif evt_type == 'game_begin':
            g = Game.getgame()
            for p in g.players:
                if isinstance(p, Ran):
                    p.tags['ran_ei'] = 0  # for ui

        return act


class NakedFox(Skill):
    associated_action = None
    target = t_None


class NakedFoxAction(GenericAction):
    def __init__(self, dmg):
        self.source = self.target = dmg.target
        self.dmgact = dmg
        self.dmgamount = dmg.amount  # for UI

    def apply_action(self):
        self.dmgact.amount -= 1
        return True


class NakedFoxHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(NakedFox): return act
            pact = g.action_stack[-1]
            if not isinstance(pact, SpellCardAction): return act
            if tgt.cards or tgt.showncards: return act
            if act.amount < 1: return act

            g.process_action(NakedFoxAction(act))
            return act

        return act


@register_character
class Ran(Character):
    skills = [Prophet, ExtremeIntelligence, NakedFox]
    eventhandlers_required = [
        ProphetHandler,
        ExtremeIntelligenceHandler,
        NakedFoxHandler,
    ]
    maxlife = 3
