# -*- coding: utf-8 -*-

from ..actions import *

class SpellCardAction(UserAction): pass

class Demolition(SpellCardAction):
    # 城管执法
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        if not len(target.cards): return False

        card = random_choose_card(target)
        self.card = card
        g.players.exclude(target).reveal(card)
        g.process_action(
            DropCards(target=target, cards=[card])
        )
        return True

class Reject(SpellCardAction):
    # 好人卡
    def __init__(self, source, target_act):
        self.source = source
        self.target_act = target_act
        self.target = target_act.target

    def apply_action(self):
        if not isinstance(self.target_act, SpellCardAction):
            return False
        self.target_act.cancelled = True
        return True

@register_eh
class RejectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            g = Game.getgame()

            p, input = g.players.user_input_any(
                'choose_card', self._expects, self
            )

            if p:
                sid_list, cid_list = input
                cards = g.deck.lookupcards(cid_list) # card was already revealed

                if sid_list: # skill selected
                    cards = skill_wrap(actor, sid_list, cards)

                card = cards[0]

                action = Reject(source=p, target_act=act)
                action.associated_card = card
                g.process_action(DropUsedCard(p, [card]))
                g.process_action(action)
        return act

    def _expects(self, p, input):
        from utils import check, CheckFailed
        try:
            check_type([[int, Ellipsis], [int, Ellipsis]], input)

            sid_list, cid_list = input

            g = Game.getgame()
            card, = g.deck.lookupcards(cid_list)
            check(card in p.cards)

            g.players.exclude(p).reveal(card)

            check(self.cond([card]))
            return True
        except CheckFailed as e:
            return False

    def cond(self, cardlist):
        from utils import check, CheckFailed
        from .. import cards
        try:
            check(len(cardlist) == 1)
            check(isinstance(cardlist[0], cards.RejectCard))
            return True
        except CheckFailed:
            return False

class DelayedSpellCardAction(SpellCardAction): # 延时SC
    def clean_up(self):
        g = Game.getgame()
        target = self.target
        g.process_action(DropCards(target, [self.associated_card]))

# TODO: code like this only allow ONE such behavior change.

class DelayedLaunchCard(LaunchCard):
    def apply_action(self):
        g = Game.getgame()
        card = self.card
        target_list = self.target_list
        if not card: return False
        action = card.associated_action

        assert issubclass(action, DelayedSpellCardAction)
        assert len(target_list) == 1
        t = target_list[0]
        migrate_cards([card], t.fatetell)
        return True

@register_eh
class DelayedSpellCardActionHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, LaunchCard):
            card = act.card
            aa = card.associated_action
            if issubclass(aa, DelayedSpellCardAction):
                act.__class__ = DelayedLaunchCard

        return act

class SealingArray(FatetellAction, DelayedSpellCardAction):
    # 封魔阵
    def __init__(self, source, target):
        assert source == target
        self.source = self.target = target

    def apply_action(self):
        g = Game.getgame()
        target = self.target
        from ..cards import Card
        ft = Fatetell(target, lambda card: card.suit != Card.HEART)
        g.process_action(ft)
        if ft.succeeded:
            target.tags['sealed'] = True
        return True

@register_eh
class SealingArrayHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            actor = act.actor
            if actor.tags.get('sealed'):
                del actor.tags['sealed']
                act.cancelled = True
        return act

class NazrinRod(SpellCardAction):
    # 纳兹琳的探宝棒
    def __init__(self, source, target):
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        g.process_action(DrawCards(self.target, amount=2))
        return True
