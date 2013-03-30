# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *
from utils import check, check_type, CheckFailed


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
        rst = tgt.user_input('ran_prophet', cards, timeout=40)
        if not rst: return False
        try:
            check_type([[int, Ellipsis]]*2, rst)
            upcards = rst[0]
            downcards = rst[1]
            check(sorted(upcards+downcards) == range(n))
        except CheckFailed as e:
            try:
                print 'RAN PROPHET:', upcards, downcards
            except:
                pass
            return act

        deck = g.deck.cards
        for i, j in enumerate(downcards):
            deck[i] = cards[j]
        deck.rotate(-len(downcards))
        for i, j in enumerate(upcards):
            deck[i] = cards[j]

        cl = [cards[i] for i in upcards]
        assert g.deck.getcards(len(upcards)) == cl

        return True

class ProphetHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Prophet): return act
            if not user_choose_option(self, tgt): return act
            Game.getgame().process_action(ProphetAction(tgt, tgt))

        return act

class ExtremeIntelligenceAction(GenericAction):
    def __init__(self, source, target, act):
        self.source, self.target, self.action = \
            source, act.target, act

    def apply_action(self):
        p = self.source
        cards = user_choose_cards(self, p, [p.cards, p.showncards, p.equips])
        if not cards: return False
        p.tags['ran_ei_tag'] = p.tags['turn_count'] + 1
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

        nact.associated_card = cards[0]

        g.process_action(nact)
        return True

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
                if p.tags['ran_ei_tag'] >= p.tags['turn_count'] + 1: continue

                try:
                    tl = act.target_list
                except AttributeError:
                    tl = [act.target]
                if any(t.dead for t in tl): return act

                if not user_choose_option(self, p): continue

                g.process_action(ExtremeIntelligenceAction(p, act.target, act))

        return act

class NakedFox(Skill):
    associated_action = None
    target = t_None

class NakedFoxAction(GenericAction):
    def __init__(self, dmg):
        self.source = self.target = dmg.target
        self.dmgact = dmg
        self.dmgamount = dmg.amount # for UI

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
