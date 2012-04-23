# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *
from utils import check, check_type, CheckFailed


class Fengshui(Skill):
    associated_action = None
    target = t_None

class ExtremeIntelligence(Skill):
    associated_action = None
    target = t_None

class FengshuiHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Fengshui): return act
            if not tgt.user_input('choose_option', self): return act
            g = Game.getgame()
            n = min(len([p for p in g.players if not p.dead]), 5)
            cards = g.deck.getcards(n)
            tgt.reveal(cards)
            rst = tgt.user_input('ran_fengshui', cards, timeout=40)
            if not rst: return act
            try:
                check_type([[int, Ellipsis]]*2, rst)
                upcards = rst[0]
                downcards = rst[1]
                check(sorted(upcards+downcards) == range(n))
            except CheckFailed as e:
                return act

            deck = g.deck.cards
            for i, j in enumerate(downcards):
                deck[i] = cards[j]
            deck.rotate(-len(downcards))
            for i, j in enumerate(upcards):
                deck[i] = cards[j]
        return act

class ExtremeIntelligenceHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, InstantSpellCardAction):
            if isinstance(act, Reject): return act
            g = Game.getgame()
            for a in reversed(g.action_stack):
                if isinstance(a, ActionStage):
                    actor = a.actor
                    break
            else:
                assert False, 'Should not happen'

            for p in g.players.exclude(actor):
                if p.dead: continue
                if not p.has_skill(ExtremeIntelligence): continue
                if p.tags['ran_ei_tag'] >= p.tags['turn_count']: continue
                if not p.user_input('choose_option', self): continue

                p.tags['ran_ei_tag'] = p.tags['turn_count']
                cards = user_choose_cards(self, p, [p.cards, p.showncards, p.equips])
                if not cards: continue

                g.process_action(DropCards(p, cards))

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

        return act

    def cond(self, cl):
        return len(cl) == 1

@register_character
class Ran(Character):
    skills = [Fengshui, ExtremeIntelligence]
    eventhandlers_required = [FengshuiHandler, ExtremeIntelligenceHandler]
    maxlife = 4
