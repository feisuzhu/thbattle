# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCards, DropCards, FatetellStage, GenericAction, LifeLost
from ..actions import ShowCards, UserAction, user_choose_cards, LaunchCard, UseCard
from ..cards import Card, Skill, VirtualCard, Wine, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input, ActionShootdown


# -- code --
class Ciguatera(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class CiguateraAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        tgt = self.target
        src = self.source
        g = Game.getgame()
        g.process_action(DropCards(src, src, self.cards))
        g.process_action(LifeLost(src, tgt, 1))
        g.process_action(Wine(src, tgt))

        return True


class CiguateraHandler(EventHandler):
    interested = ('action_after', 'action_before')
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            g = Game.getgame()
            for p in g.players:
                if p.dead:
                    continue

                if not p.has_skill(Ciguatera):
                    continue

                cards = user_choose_cards(self, p, ('cards', 'showncards'))
                if cards:
                    g.process_action(CiguateraAction(p, act.target, cards))

        return act

    def cond(self, cl):
        if len(cl) != 1 or cl[0].is_card(Skill):
            return False

        return cl[0].resides_in.type in ('cards', 'showncards')


class Melancholy(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MelancholyPoison(VirtualCard):
    associated_action = None
    target = t_None


class MelancholyLimit(ActionShootdown):
    pass


class MelancholyAction(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        src = self.source
        tgt = self.target
        draw = DrawCards(src, self.amount)
        g = Game.getgame()
        g.process_action(draw)
        g.process_action(ShowCards(src, draw.cards))
        if [c for c in draw.cards if c.suit != Card.CLUB]:  # any non-club
            tgt.tags['melancholy_tag'] = g.turn_count
            self.effective = True

        else:
            self.effective = False

        return True


class MelancholyHandler(EventHandler):
    interested = ('action_after', 'action_shootdown')

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            act = act
            tgt = act.target
            src = act.source

            if not src:
                return act

            if not tgt.has_skill(Melancholy):
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(MelancholyAction(tgt, src, amount=1))

        elif evt_type == 'action_shootdown' and isinstance(act, (LaunchCard, UseCard)):
            src = act.source
            g = Game.getgame()
            if src.tags.get('melancholy_tag') != g.turn_count:
                return act

            def walk(c):
                if not c.is_card(VirtualCard):
                    return [c]

                if c.usage not in ('launch', 'use'):
                    return []

                cards = c.associated_cards
                return walk(cards[0]) if len(cards) == 1 else cards

            cards = walk(act.card)
            zone = src.cards, src.showncards
            for c in cards:
                if c.resides_in in zone:
                    raise MelancholyLimit

        return act


@register_character
class Medicine(Character):
    skills = [Ciguatera, Melancholy]
    eventhandlers_required = [CiguateraHandler, MelancholyHandler]
    maxlife = 3
