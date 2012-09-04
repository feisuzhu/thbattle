# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class FlyingSkanda(Skill):
    associated_action = None
    target = t_None

class FlyingSkandaAction(GenericAction):
    def __init__(self, source, target, card, ori_action):
        self.source = source
        self.target = target
        self.card = card
        self.ori_action = ori_action

    def apply_action(self):
        g = Game.getgame()
        src = self.source
        tgt = self.target
        card = self.card
        ori = self.ori_action

        src.tags['flyingskanda'] = src.tags['turn_count']

        act = ori.card.associated_action(src, tgt)
        act.associated_card = card

        g.process_action(DropUsedCard(src, [card]))
        return g.process_action(act)

class FlyingSkandaHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, LaunchCard):
            g = Game.getgame()
            src = g.current_turn
            if not src.has_skill(FlyingSkanda): return act
            tags = src.tags
            if not tags['flyingskanda'] < tags['turn_count']: return act
            card = act.card
            if not ( # assoc_act of multiple targeted SC is ForEach
                card.is_card(AttackCard) or
                issubclass(card.associated_action, InstantSpellCardAction)
            ): return act

            if not src.user_input('choose_option', self):
                return act

            self.source = src
            self.ori_action = act

            rst = user_choose_cards_and_players(
                self, src, [src.cards, src.showncards, src.equips],
                g.players.exclude(src, act.target),
            )

            if not rst: return act
            cl, tl = rst
            card = cl[0]; tgt = tl[0]

            g.process_action(FlyingSkandaAction(src, tgt, card, act))

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        src = self.source
        if cl[0].resides_in not in (src.cards, src.showncards, src.equips):
            return False
        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        ori = self.ori_action
        dist = CalcDistance(self.source, ori.card)
        Game.getgame().process_action(dist)
        if ori.card.is_card(AttackCard):
            # FIXME+HACK: AttackCard's constraint is implemented
            # by limiting attack range below 0
            # and should be fixed.
            if dist.correction < 0:
                dist.correction += 10000

        rst = dist.validate()

        tl = [t for t in tl if rst[t]]

        if not tl:
            return (tl, False)

        return (tl[-1:], True)

@register_character
class Chen(Character):
    skills = [FlyingSkanda]
    eventhandlers_required = [FlyingSkandaHandler]
    maxlife = 4
