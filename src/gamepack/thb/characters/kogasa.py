# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DrawCardStage, DrawCards, UserAction, detach_cards
from gamepack.thb.actions import migrate_cards, user_choose_players
from gamepack.thb.cards import Card, Skill, VirtualCard, t_None, t_One, t_OtherOne
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class Jolly(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class SurpriseAction(UserAction):

    def apply_action(self):
        src = self.source
        tgt = self.target
        options = (
            Card.SPADE, Card.HEART,
            Card.CLUB, Card.DIAMOND,
        )

        card = self.associated_card
        detach_cards([card])
        suit = user_input([tgt], ChooseOptionInputlet(self, options))

        src.tags['surprise_tag'] = src.tags['turn_count']
        assert card

        g = Game.getgame()
        g.players.reveal(card.associated_cards)
        migrate_cards([card], tgt.showncards, unwrap=True)

        if card.suit != suit:
            g.process_action(Damage(src, tgt))
            rst = True
        else:
            rst = False

        return rst

    def is_valid(self):
        t = self.source.tags
        if t['turn_count'] <= t['surprise_tag']: return False
        return True


class Surprise(Skill):
    associated_action = SurpriseAction
    skill_category = ('character', 'active')
    target = t_OtherOne
    no_reveal = True
    no_drop = True
    usage = 'handover'

    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        c, = cl
        if c.is_card(VirtualCard):
            return False

        if c.resides_in.type not in ('cards', 'showncards'):
            return False

        return True


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
    skills = [Surprise, Jolly]
    eventhandlers_required = [JollyHandler]
    maxlife = 3
