# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import Game, user_input
from game.base import EventHandler
from thb.actions import DropCards, GenericAction, LaunchCard, ShowCards, UserAction, migrate_cards
from thb.actions import random_choose_card, ttags
from thb.cards import AttackCard, Heal, t_One
from thb.cards.base import Card, HiddenCard, PhysicalCard, Skill, TreatAs, VirtualCard
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class EirinHeal(Heal):
    pass


class SkySilkAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ['cards', 'showncards', 'equips']))
        c = c or random_choose_card([tgt.cards, tgt.showncards, tgt.equips])
        g.players.reveal(c)

        g.process_action(DropCards(src, tgt, [c]))

        action = 'draw'
        if tgt.life < tgt.maxlife:
            action = user_input([tgt], ChooseOptionInputlet(self, ('heal', 'draw'))) or 'draw'

        if action == 'heal':
            g.process_action(EirinHeal(src, tgt))
        else:
            g.deck.getcards(3)
            g.deck.cards.rotate(3)
            cl = g.deck.getcards(3)
            g.process_action(ShowCards(tgt, cl))

            drop = [c for c in cl if 'basic' in c.category]
            get = [c for c in cl if c not in drop]

            if get:
                migrate_cards(get, tgt.cards)

            if drop:
                migrate_cards(drop, g.deck.droppedcards)

        ttags(src)['sky_silk'] = True
        return True

    def is_valid(self):
        src, tgt = self.source, self.target
        return (tgt.cards or tgt.showncards or tgt.equips) and not ttags(src)['sky_silk']


class SkySilk(Skill):
    associated_action = SkySilkAction
    skill_category = ('character', 'active')
    target = t_One
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return bool(not cl)


class LunaStringPlaceCard(GenericAction):
    def __init__(self, target, card):
        self.source = self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        place = user_input([tgt], ChooseOptionInputlet(self, ('top', 'bottom')))
        sk = self.card
        assert sk.is_card(LunaString)
        c = sk.associated_cards[0]
        sk.associated_cards[:] = []
        sk.cost_detached = True
        self.place = place  # for ui
        migrate_cards([c], g.deck.cards, unwrap=True, front=(place == 'top'))
        return True


class LunaStringLaunchCardHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('SolidShieldHandler',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if not isinstance(act, LaunchCard):
                return act

            c = act.card

            def walk(c):
                if c.is_card(LunaString):
                    return c

                if c.is_card(PhysicalCard) or c.is_card(HiddenCard):
                    return None

                assert isinstance(c, VirtualCard)

                for c1 in c.associated_cards:
                    r = walk(c1)
                    if r:
                        return r

                return None

            c = walk(c)

            if c:
                g = Game.getgame()
                g.process_action(LunaStringPlaceCard(c.player, c))

        return act


class LunaString(TreatAs, Skill):
    treat_as = AttackCard

    skill_category = ('character', 'active')
    no_reveal = True
    use_action = LunaStringPlaceCard  # UseCard hook

    color  = Card.NOTSET
    suit   = Card.NOTSET
    number = 0

    cost_detached = False

    def check(self):
        if self.cost_detached:
            return True

        cl = self.associated_cards
        if not len(cl) == 1:
            return False

        c = cl[0]

        if not (c.is_card(PhysicalCard) or c.is_card(HiddenCard)):  # HiddenCard for other viewpoints
            return False

        return c.resides_in.type in ('cards', 'showncards')


@register_character_to('common', '-kof')
class Eirin(Character):
    skills = [SkySilk, LunaString]
    eventhandlers_required = [LunaStringLaunchCardHandler]
    maxlife = 3
