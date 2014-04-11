# -*- coding: utf-8 -*-
from ..actions import ActionStage, Damage, DrawCardStage, DrawCards, DropCards
from ..actions import ForEach, GenericAction, PlayerTurn, UserAction, user_choose_cards
from ..cards import AttackCard, InstantSpellCardAction, RedUFOSkill, RejectCard
from ..cards import Skill, VirtualCard, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


class Onbashira(RedUFOSkill):
    associated_action = None
    target = t_None

    @staticmethod
    def increment(src):
        if Game.getgame().current_turn is not src: return 0
        return src.tags.get('divinity', 0)


class OnbashiraAction(GenericAction):
    def __init__(self, target, amount):
        self.source = self.target = target
        self.amount = amount

    def apply_action(self):
        tags = self.target.tags
        tags['divinity'] = self.amount
        return True


class OnbashiraTarget(GenericAction):
    card_usage = 'drop'

    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        tgt = self.target
        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))

        if cards:
            self.cards = cards
            g = Game.getgame()
            g.process_action(DropCards(tgt, cards=cards))
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


class OnbashiraHandler(EventHandler):
    execute_after = ('CiguateraHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            tgt = act.target
            if not tgt.has_skill(Onbashira): return act
            rst = user_input([tgt], ChooseOptionInputlet(self, (0, 1, 2)))

            if not rst: rst = 0
            Game.getgame().process_action(OnbashiraAction(tgt, rst))
            act.amount = max(0, act.amount - rst)

        elif evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.has_skill(Onbashira):
                tgt.tags['divinity'] = 0
            for p in Game.getgame().players:
                p.tags['divinity_target'] = False

        elif evt_type == 'action_limit':
            arg, permitted = act
            if not permitted: return act
            if arg.usage not in ('use', 'launch'): return act

            g = Game.getgame()
            p = g.current_turn
            if not p or not p.has_skill(Onbashira): return act

            src = arg.actor
            if src.tags.get('divinity_target'):
                cards = VirtualCard.unwrap(arg.cards)
                zone = src.cards, src.showncards
                return arg, all([c.resides_in not in zone for c in cards])

            return act

        elif evt_type == 'post_choose_target':
            act, tl = arg = act
            src = act.source
            g = Game.getgame()
            if src is not g.current_turn: return arg
            if not src.has_skill(Onbashira): return arg

            dlvl = src.tags['divinity']
            if not dlvl > 0: return arg

            if not act.card.is_card(AttackCard):
                if act.card.is_card(RejectCard): return arg
                aact = getattr(act.card, 'associated_action', None)
                if not aact: return arg
                if not issubclass(aact, InstantSpellCardAction):
                    if not issubclass(aact, ForEach): return arg
                    if not issubclass(aact.action_cls, InstantSpellCardAction):
                        return arg
                    if len(tl) != 1: return arg

            for tgt in tl:
                if tgt is not src:
                    g.process_action(OnbashiraTarget(src, tgt, src.tags['divinity']))

            return arg

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
    skills = [Onbashira, KanakoFaith]
    eventhandlers_required = [OnbashiraHandler, KanakoFaithHandler]
    maxlife = 4
