# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCardStage, DrawCards, UserAction, migrate_cards
from ..actions import random_choose_card, user_choose_players
from ..cards import Card, Skill, t_None, t_One, t_OtherOne
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class Jolly(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class Surprise(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        options = (
            Card.SPADE, Card.HEART,
            Card.CLUB, Card.DIAMOND,
        )

        suit = user_input([tgt], ChooseOptionInputlet(self, options))
        card = user_input([tgt], ChoosePeerCardInputlet(self, src, ('cards', 'showncards')))
        card = card or random_choose_card([src.cards, src.showncards])

        src.tags['surprise_tag'] = src.tags['turn_count']
        assert card

        g = Game.getgame()
        g.players.exclude(src).reveal(card)
        migrate_cards([card], tgt.showncards)

        if card.suit != suit:
            g.process_action(Damage(src, tgt))
            rst = True
        else:
            rst = False

        g.process_action(DrawCards(src, 1))

        return rst

    def is_valid(self):
        src = self.source
        if self.associated_card.associated_cards: return False
        if src.tags.get('turn_count', 0) <= src.tags.get('surprise_tag', 0):
            return False
        if not (src.cards or src.showncards):
            return False
        return True


class SurpriseSkill(Skill):
    associated_action = Surprise
    skill_category = ('character', 'active')
    target = t_OtherOne

    def check(self):
        return not self.associated_cards


class JollyDrawCard(DrawCards):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.amount = 1


class JollyHandler(EventHandler):
    interested = ('action_after',)
    choose_player_target = t_One

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DrawCardStage):
            tgt = act.target

            if not tgt.has_skill(Jolly): return act

            g = Game.getgame()
            pl = user_choose_players(self, tgt, [p for p in g.players if not p.dead])
            if not pl: pl = [tgt]

            p = pl[0]

            g.process_action(JollyDrawCard(tgt, p))

        return act

    def cond(self, cards):
        return not cards

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)


@register_character
class Kogasa(Character):
    skills = [SurpriseSkill, Jolly]
    eventhandlers_required = [JollyHandler]
    maxlife = 3
