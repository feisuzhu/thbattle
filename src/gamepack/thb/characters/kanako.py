# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import GenericAction, UserAction, LaunchCardAction, DrawCardStage, ask_for_drop, PlayerTurn, UseCardAction, ForEach, Damage, ActionStage, DrawCards
from ..cards import RedUFOSkill, AttackCard, Skill, t_None, RejectCard, InstantSpellCardAction, VirtualCard
from ..inputlets import ChooseOptionInputlet


class Divinity(RedUFOSkill):
    associated_action = None
    target = t_None

    @staticmethod
    def increment(src):
        if Game.getgame().current_turn is not src: return 0
        return src.tags.get('divinity', 0)


class DivinityAction(GenericAction):
    def __init__(self, target, amount):
        self.source = self.target = target
        self.amount = amount

    def apply_action(self):
        tags = self.target.tags
        tags['divinity'] = self.amount
        return True

class DivinityTarget(GenericAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.amount = source.tags['divinity']

    def apply_action(self):
        tgt = self.target
        drop = ask_for_drop(self, tgt, ('cards', 'showncards', 'equips'))
        if drop:
            self.cards = drop.cards
            Game.getgame().process_action(drop)
        else:
            self.cards = None
            self.target.tags['divinity_target'] = True

        return True

    def cond(self, cl):
        if len(cl) != self.amount: return False
        
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards, t.equips):
            return False
            
        return True

    def is_valid(self):
        return self.amount > 0


class DivinityHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(Divinity): return act
            rst = user_input([tgt], ChooseOptionInputlet(self, (0, 1, 2)))

            if not rst: rst = 0
            Game.getgame().process_action(DivinityAction(tgt, rst))
            act.amount = max(0, act.amount - rst)

        elif evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.has_skill(Divinity):
                tgt.tags['divinity'] = 0
            for p in Game.getgame().players:
                p.tags['divinity_target'] = False
        
        elif evt_type == 'action_can_fire':
            act, valid = arg = act
            if not valid: return arg

            if isinstance(act, LaunchCardAction):
                cards = [act.card]
            elif isinstance(act, UseCardAction):
                cards = act.cards
            else:
                return arg

            g = Game.getgame()
            p = g.current_turn
            if not p or not p.has_skill(Divinity): return arg

            src = act.source
            if src.tags.get('divinity_target'):
                cards = VirtualCard.unwrap(cards)
                zone = src.cards, src.showncards
                return act, all([c.resides_in not in zone for c in cards])

            return arg

        elif evt_type == 'before_launch_card':
            src = act.source
            g = Game.getgame()
            if src is not g.current_turn: return act
            if not src.has_skill(Divinity): return act

            dlvl = src.tags['divinity']
            if not dlvl > 0: return act

            if not act.card.is_card(AttackCard):
                if act.card.is_card(RejectCard): return act
                aact = getattr(act.card, 'associated_action', None)
                if not issubclass(aact, InstantSpellCardAction):
                    if not issubclass(aact, ForEach): return act
                    if not issubclass(aact.action_cls, InstantSpellCardAction):
                        return act
                    if len(act.target_list) != 1: return act

            for tgt in act.target_list or act.target:
                if tgt is not src:
                    g.process_action(DivinityTarget(src, tgt))

        return act


class KanakoFaith(Skill):
    associated_action = None
    target = t_None

class KanakoFaithAction(UserAction):
    def apply_action(self):
        tags = self.target.tags
        tags['kanako_faith'] = tags['turn_count']
        return True

class KanakoFaithDrawCards(DrawCards):
    pass

class KanakoFaithHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after':
            if isinstance(act, Damage):
                src = act.source
                tgt = act.target
                if not src or src is tgt: return act
                if not src.has_skill(KanakoFaith): return act

                g = Game.getgame()
                if g.current_turn is not src: return act
                g.process_action(KanakoFaithAction(src, src))
            
            elif isinstance(act, ActionStage):
                tgt = act.target
                if not tgt.has_skill(KanakoFaith): return act
                if not tgt.tags['kanako_faith'] >= tgt.tags['turn_count']:
                    return act
                Game.getgame().process_action(KanakoFaithDrawCards(tgt, 1))

        return act

@register_character
class Kanako(Character):
    skills = [Divinity, KanakoFaith]
    eventhandlers_required = [DivinityHandler, KanakoFaithHandler]
    maxlife = 4
