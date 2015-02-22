# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import DropCards, Fatetell, FatetellAction, FatetellMalleateHandler
from gamepack.thb.actions import LaunchCard, PostCardMigrationHandler, UserAction, user_choose_cards
from gamepack.thb.cards import AttackCard, Skill, TreatAs, VirtualCard, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class MiracleMallet(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class VengeOfTsukumogami(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MiracleMalletAction(UserAction):
    def __init__(self, source, target, ft, card):
        self.source, self.target, self.ft, self.card = \
            source, target, ft, card

    def apply_action(self):
        g = Game.getgame()
        c = self.card
        g.players.exclude(self.source).reveal(c)
        g.process_action(DropCards(self.source, [c]))
        self.ft.set_card(c)
        return True


class MiracleMalletHandler(EventHandler):
    interested = ('fatetell', )
    execute_before = ('YinYangOrbHandler', )
    group = FatetellMalleateHandler
    card_usage = 'use'

    def handle(self, p, act):
        if p.dead: return act
        if not p.has_skill(MiracleMallet): return act

        self.number = act.card.number
        cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))

        if cards:
            c = cards[0]
            Game.getgame().process_action(MiracleMalletAction(p, act.target, act, c))

        return act

    def cond(self, cards):
        if len(cards) != 1:
            return False

        return cards[0].number > self.number


class VengeOfTskumogamiAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class VengeOfTsukumogamiAction(FatetellAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        src = self.source
        tgt = self.target
        ft = Fatetell(tgt, lambda c: c.number > 9)
        g = Game.getgame()
        if g.process_action(ft):
            g.process_action(LaunchCard(src, [tgt], VengeOfTskumogamiAttack(src), bypass_check=True))

        return True


class VengeOfTsukumogamiHandler(EventHandler):
    group = PostCardMigrationHandler

    def handle(self, p, cards, _from, to):
        if not p.has_skill(VengeOfTsukumogami): return True

        if _from is None or _from.type != 'equips':
            return True

        if _from.owner is p:
            return True

        if to.type != 'droppedcard':
            return True

        self.target = tgt = _from.owner
        for c in cards:
            self.card = c

            if tgt.dead:
                break

            if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                break

            Game.getgame().process_action(VengeOfTsukumogamiAction(p, tgt, c))

        return True


@register_character
class Shinmyoumaru(Character):
    skills = [MiracleMallet, VengeOfTsukumogami]
    eventhandlers_required = [MiracleMalletHandler, VengeOfTsukumogamiHandler]
    maxlife = 4
