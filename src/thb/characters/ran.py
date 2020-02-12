# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionLimitExceeded, ActionStageLaunchCard, Damage, DropCards, GenericAction
from thb.actions import PlayerTurn, ttags, user_choose_cards
from thb.cards.base import DummyCard, Skill, VirtualCard, t_None
from thb.cards.classes import InstantSpellCardAction, Reject, SpellCardAction, TreatAs
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ProphetInputlet
from thb.mode import THBEventHandler


# -- code --
class Prophet(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ExtremeIntelligence(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ProphetAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = self.game
        n = min(len([p for p in g.players if not p.dead]), 5)
        cards = g.deck.getcards(n)

        assert cards == g.deck.getcards(n)

        tgt.reveal(cards)

        upcards, downcards = g.user_input([tgt], ProphetInputlet(self, cards), timeout=45) or [list(range(n)), []]

        deck = g.deck.cards
        for i, c in enumerate(downcards):
            deck[i] = c
        deck.rotate(-len(downcards))

        for i, c in enumerate(upcards):
            deck[i] = c

        assert g.deck.getcards(len(upcards)) == upcards

        return True


class ProphetHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Prophet): return act
            g = self.game
            if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

        return act


class ExtremeIntelligenceAction(GenericAction):
    card_usage = 'drop'

    def __init__(self, source, target, act):
        self.source, self.target, self.action = \
            source, act.target, act

    def activate_action(self):
        p = self.source
        self.cards = cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
        if not cards: return False
        p.tags['ran_ei'] = p.tags['turn_count'] + 1
        return True

    def apply_action(self):
        p = self.source
        cards = self.cards
        g = self.game
        g.process_action(DropCards(p, p, cards))

        act = self.action
        nact = act.__class__(source=p, target=act.target)
        try:
            nact.target_list = act.target_list
        except AttributeError:
            pass

        try:
            # HACK: This is for actions triggered by ForEach action.
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

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(Skill)


class ExtremeIntelligenceHandler(THBEventHandler):
    interested = ['action_after', 'game_begin']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, InstantSpellCardAction):
            if isinstance(act, Reject): return act
            g = self.game
            target = g.current_player

            for p in g.players.exclude(target):
                if p.dead:
                    continue

                if not p.has_skill(ExtremeIntelligence):
                    continue

                if p.tags['ran_ei'] >= p.tags['turn_count'] + 1:
                    continue

                try:
                    tl = act.target_list
                except AttributeError:
                    tl = [act.target]

                if any(t.dead for t in tl):
                    return act

                if not act.can_fire():
                    return act  # act cannot fire again

                nact = ExtremeIntelligenceAction(p, act.target, act)

                if nact.activate_action():
                    g.process_action(nact)

        elif evt_type == 'game_begin':
            g = self.game
            for p in g.players:
                if isinstance(p, Ran):
                    p.tags['ran_ei'] = 0  # for ui

        return act


class ExtremeIntelligenceKOF(TreatAs, Skill):
    skill_category = ['character', 'active']

    def __init__(self, player):
        Skill.__init__(self, player)
        self.treat_as = ttags(player).get('ran_eikof_card') or DummyCard

    def check(self):
        cards = self.associated_cards
        if len(cards) != 1: return False
        c = cards[0]
        if c.resides_in is None: return False
        if c.resides_in.type not in ('cards', 'showncards'): return False
        return True


class ExtremeIntelligenceKOFHandler(THBEventHandler):
    interested = ['action_apply', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStageLaunchCard):
            if not act.card.is_card(VirtualCard):
                src = act.source
                if not src.has_skill(ExtremeIntelligenceKOF): return act
                c = act.card
                if 'instant_spellcard' not in c.category: return act
                ttags(src)['ran_eikof_card'] = c.__class__

            elif act.card.is_card(ExtremeIntelligenceKOF):
                src = act.source
                ttags(src)['ran_eikof_tag'] = True

        elif evt_type == 'action_shootdown' and isinstance(act, ActionStageLaunchCard) and act.card.is_card(ExtremeIntelligenceKOF):
            src = act.source
            tt = ttags(src)
            if tt['ran_eikof_tag'] or not tt['ran_eikof_card']:
                raise ActionLimitExceeded

        return act


class NakedFox(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class NakedFoxAction(GenericAction):
    def __init__(self, dmg):
        self.source = self.target = dmg.target
        self.dmgact = dmg
        self.dmgamount = dmg.amount  # for UI

    def apply_action(self):
        self.dmgact.amount -= 1
        return True


class NakedFoxHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            g = self.game
            tgt = act.target
            if not tgt.has_skill(NakedFox): return act
            pact = g.action_stack[-1]
            if not isinstance(pact, SpellCardAction): return act
            if tgt.cards or tgt.showncards: return act
            if act.amount < 1: return act

            g.process_action(NakedFoxAction(act))
            return act

        return act


@register_character_to('common', '-kof')
class Ran(Character):
    skills = [Prophet, ExtremeIntelligence, NakedFox]
    eventhandlers = [
        ProphetHandler,
        ExtremeIntelligenceHandler,
        NakedFoxHandler,
    ]
    maxlife = 3


@register_character_to('kof')
class RanKOF(Character):
    skills = [Prophet, ExtremeIntelligenceKOF, NakedFox]
    eventhandlers = [
        ProphetHandler,
        ExtremeIntelligenceKOFHandler,
        NakedFoxHandler,
    ]
    maxlife = 3
