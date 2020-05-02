# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game, EventHandler, user_input
from thb.actions import ActionStage, DrawCards, DropCardStage, LaunchCard, PrepareStage, UserAction, migrate_cards, random_choose_card, user_choose_players
from thb.cards import DummyCard, Skill, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseIndividualCardInputlet, ChoosePeerCardInputlet


# -- code --
class DivineFetch(DummyCard):
    distance = 2


class DivineFetchAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        if src.tags['divine_picker']:
            return False

        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards')))
        c = c or random_choose_card(g, [tgt.cards, tgt.showncards])
        if not c: return False

        src.reveal(c)
        migrate_cards([c], src.cards)

        src.tags['divine_picker'] = tgt

        return True


class DivineFetchHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PrepareStage):
            tgt = act.target
            if not tgt.has_skill(Divine) or act.cancelled: return act

            pl = [p for p in Game.getgame().players if not p.dead and p is not tgt]
            pl = [p for p in pl if LaunchCard.calc_distance(tgt, DivineFetch()).get(p, 2) <= 0]
            pl = [p for p in pl if any(p.cards or p.showncards)]
            pl = pl and user_choose_players(self, tgt, pl)
            pl and len(pl) == 1 and Game.getgame().process_action(DivineFetchAction(tgt, pl[0]))

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
        src = self.source

        cards_avail = list(self.cards)
        if not cards_avail or src.dead: return False

        assert not any(c.is_card(VirtualCard) for c in cards_avail)

        card = user_input(
            [src],
            ChooseIndividualCardInputlet(self, cards_avail)
        ) or random_choose_card([cards_avail])

        migrate_cards([card], src.cards)

        self.card = card

        return True


class DivinePickHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DropCardStage):
            dropper, g = act.target, Game.getgame()
            if dropper.has_skill(Divine):
                pl = [p for p in g.players if not p.dead and p is not dropper and p is dropper.tags['divine_picker']]
                assert len(pl) <= 1

                dropper.tags['divine_picker'] = None

                if pl:
                    picker = pl[0]
                    dropn = getattr(act, 'dropn', 0)
                    dropped = getattr(act, 'cards', [])
                    dropn and dropped and len(dropped) == dropn and g.process_action(DivinePickAction(picker, dropper, dropped))

        return act


class Divine(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SpringSignDrawCards(DrawCards):
    pass


class SpringSignHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStage):
            if act.target and act.target.has_skill(SpringSign):
                Game.getgame().process_action(SpringSignDrawCards(act.target, 2))
        return act


class SpringSign(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


@register_character_to('common')
class Suwako(Character):
    skills = [Divine, SpringSign]
    eventhandlers_required = [DivineFetchHandler, DivinePickHandler, SpringSignHandler]
    maxlife = 3
