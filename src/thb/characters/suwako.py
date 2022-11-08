# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionStage, DrawCards, DropCardStage, LaunchCard, PrepareStage, UserAction
from thb.actions import migrate_cards, random_choose_card, user_choose_players
from thb.cards.base import DummyCard, Skill, VirtualCard, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseIndividualCardInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class DivineFetch(DummyCard):
    distance = 2


class DivineFetchAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = self.game

        if src.tags['divine_picker']:
            return False

        c = g.user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards')))
        c = c or random_choose_card(g, [tgt.cards, tgt.showncards])
        if not c: return False

        src.reveal(c)
        migrate_cards([c], src.cards)

        src.tags['divine_picker'] = tgt

        return True


class DivineFetchHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PrepareStage):
            tgt = act.target
            if not tgt.has_skill(Divine) or act.cancelled: return act
            g = self.game
            pl = [p for p in g.players if not p.dead and p is not tgt]
            pl = [p for p in pl if LaunchCard.calc_distance(g, tgt, DivineFetch()).get(p, 2) <= 0]
            pl = [p for p in pl if any(p.cards or p.showncards)]
            pl = pl and user_choose_players(self, tgt, pl)
            pl and len(pl) == 1 and g.process_action(DivineFetchAction(tgt, pl[0]))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class DivinePickAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = self.game
        src = self.source

        cards_avail = list(self.cards)
        if not cards_avail or src.dead: return False

        assert not any(c.is_card(VirtualCard) for c in cards_avail)

        card = g.user_input(
            [src],
            ChooseIndividualCardInputlet(self, cards_avail)
        ) or random_choose_card(g, [cards_avail])

        migrate_cards([card], src.cards)

        self.card = card

        return True


class DivinePickHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DropCardStage):
            dropper = act.target
            g = self.game
            if not dropper.has_skill(Divine):
                return act

            pl = [p for p in g.players if not p.dead and p is not dropper and p is dropper.tags['divine_picker']]
            assert len(pl) <= 1, 'Multiple divine picker!'

            dropper.tags['divine_picker'] = None

            if not pl:
                return act

            picker = pl[0]
            dropn = getattr(act, 'dropn', 0)
            dropped = getattr(act, 'cards', [])

            if dropn and dropped and len(dropped) == dropn:
                g.process_action(DivinePickAction(picker, dropper, dropped))

        return act


class Divine(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None()


class SpringSignDrawCards(DrawCards):
    pass


class SpringSignHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStage):
            if act.target and act.target.has_skill(SpringSign):
                g = self.game
                g.process_action(SpringSignDrawCards(act.target, 2))
        return act


class SpringSign(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None()


@register_character_to('common')
class Suwako(Character):
    skills = [Divine, SpringSign]
    eventhandlers = [DivineFetchHandler, DivinePickHandler, SpringSignHandler]
    maxlife = 3
