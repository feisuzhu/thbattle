# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *


class Passthru(Skill):
    associated_action = None
    target = t_None

# 被八云梦否决了
class PassthruAction(DrawCards):
    def __init__(self, target):
        self.source = target
        self.target = target
        self.amount = 1


class PassthruHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and hasattr(act, 'parent_action'):
            tgt = act.target
            if not tgt.has_skill(Passthru): return act
            if not user_choose_option(self, tgt): return act
            act.cancelled = True
            g = Game.getgame()
            g.process_action(PassthruAction(tgt))

        return act
# -------------------


class HeterodoxySkipAction(GenericAction):
    def apply_action(self):
        return True


class HeterodoxyHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and hasattr(act, 'parent_action'):
            tgt = act.target
            if not tgt.has_skill(Heterodoxy): return act

            g = Game.getgame()
            for a in reversed(g.action_stack):
                if isinstance(a, HeterodoxyAction):
                    break
            else:
                return act

            if not user_choose_option(self, tgt): return act
            act.cancelled = True
            g.process_action(HeterodoxySkipAction(tgt, tgt))

        return act


class HeterodoxyAction(GenericAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card.associated_cards[0]
        src = self.source
        victim = self.target
        tgts = self.target_list[1:]

        g.players.reveal(card)
        migrate_cards([self.associated_card], victim.cards, unwrap=migrate_cards.SINGLE_LAYER)

        if card.is_card(AttackCard):
            src.tags['attack_num'] -= 1

        lc = LaunchCard(victim, tgts, card)

        def choose_peer_card_hook(ori, source, target, categories):
            source = src if source is victim else source
            cid = source.user_input('choose_peer_card', (target, categories))
            return choose_peer_card_logic(cid, source, target, categories)

        def choose_individual_card_hook(ori, source, cards):
            source = src if source is victim else source
            cid = source.user_input('choose_individual_card', cards)
            return choose_individual_card_logic(cid, source, cards)

        def user_choose_option_hook(ori, act, target):
            target = src if target is victim else target
            return target.user_input('choose_option', act)

        try:
            choose_peer_card.hook(choose_peer_card_hook)
            choose_individual_card.hook(choose_individual_card_hook)
            user_choose_option.hook(user_choose_option_hook)

            g = Game.getgame()
            g.process_action(lc)

        finally:
            choose_peer_card.unhook(choose_peer_card_hook)
            choose_individual_card.unhook(choose_individual_card_hook)
            user_choose_option.unhook(user_choose_option_hook)


        return True
    
    def is_valid(self):
        card = self.associated_card.associated_cards[0]
        if card.is_card(AttackCard) and self.source.tags['attack_num'] < 1:
            return False
        victim = self.target
        tgts = self.target_list[1:]
        lc = LaunchCard(victim, tgts, card)
        return lc.can_fire()


class Heterodoxy(Skill):
    no_drop = True
    associated_action = HeterodoxyAction

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].target.__name__ in {
                't_Self', 't_One', 't_OtherOne', 't_All', 't_AllInclusive'
            }
        )

    def target(self, g, src, tl):
        cl = self.associated_cards
        if not cl: return ([], False)
        c = cl[0]
        tname = c.target.__name__

        tl = [t for t in tl if not t.dead]

        if not tl: return [], False
        if tl[0] is self.player: return [], False

        if tname in { 't_Self', 't_All', 't_AllInclusive' }:
            return tl[-1:], True
        else:
            return tl[:2], len(tl) >= 2


@register_character
class Seiga(Character):
    # skills = [Heterodoxy, Passthru]
    skills = [Heterodoxy]
    # eventhandlers_required = [PassthruHandler]
    eventhandlers_required = [HeterodoxyHandler]
    maxlife = 4
