# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, FatetellAction, FatetellMalleateHandler, LaunchCard
from gamepack.thb.actions import MigrateCardsTransaction, PostCardMigrationHandler, UseCard
from gamepack.thb.actions import detach_cards, migrate_cards, user_choose_cards
from gamepack.thb.cards import Skill, t_None
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


class MiracleMalletAction(UseCard):
    def __init__(self, source, target, ft, card):
        self.source, self.target, self.ft, self.card = \
            source, target, ft, card

    def apply_action(self):
        g = Game.getgame()
        c = self.card
        ft = self.ft
        src = self.source
        g.players.exclude(src).reveal(c)
        with MigrateCardsTransaction(self) as trans:
            migrate_cards([ft.card], src.cards, unwrap=True, trans=trans)
            detach_cards([c], trans=trans)
            self.ft.set_card(c, self)

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
        self.act = act
        cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))

        if cards:
            c = cards[0]
            Game.getgame().process_action(MiracleMalletAction(p, act.target, act, c))

        return act

    def cond(self, cards):
        if len(cards) != 1 or cards[0].is_card(Skill):
            return False

        return cards[0].number > self.number

    def ask_for_action_verify(self, p, cl, tl):
        act = self.act
        return MiracleMalletAction(p, act.target, act, cl[0]).can_fire()


class VengeOfTsukumogamiAction(FatetellAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card
        self.fatetell_target = source
        self.fatetell_cond = lambda c: 9 <= c.number <= 13

    def fatetell_action(self, ft):
        if ft.succeeded:
            Game.getgame().process_action(Damage(self.source, self.target))

        return True


class VengeOfTsukumogamiHandler(EventHandler):
    interested = ('post_card_migration',)
    group = PostCardMigrationHandler

    def handle(self, p, trans):
        if not p.has_skill(VengeOfTsukumogami):
            return True

        if isinstance(trans.action, (LaunchCard, UseCard)):
            return True

        for cards, _from, to, is_bh in trans.get_movements():
            if _from is None or _from.type != 'equips':
                continue

            if _from.owner is p:
                continue

            if to.type != 'droppedcard':
                continue

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
