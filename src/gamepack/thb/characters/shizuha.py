# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DrawCards, DropCards, LaunchCard, PostCardMigrationHandler
from gamepack.thb.actions import UseCard, UserAction, user_choose_cards
from gamepack.thb.cards import AttackCardHandler, Card, Skill, t_None, t_OtherOne
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class DecayAction(UserAction):
    def apply_action(self):
        g = Game.getgame()

        src = self.source
        tgt = self.target
        hand = list(tgt.cards) + list(tgt.showncards)
        cards = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))

        if not cards:
            cl = hand + list(tgt.equips)
            cards = cl[:2]

        decay = hand and set(cards) >= set(hand)

        g.players.reveal(cards)
        g.process_action(DropCards(src, tgt, cards))
        if decay:
            g.process_action(Damage(src, tgt))

        return True

    def cond(self, cl):
        if not cl:
            return False

        if len(cl) > 2:
            return False

        if any(c.is_card(Skill) for c in cl):
            return False

        if len(cl) == 2:
            return True

        return 'basic' in cl[0].category

    def is_valid(self):
        tgt = self.target
        return bool(tgt.cards or tgt.showncards or tgt.equips)


class Decay(Skill):
    associated_action = DecayAction
    skill_category = ('character', 'active')
    target = t_OtherOne
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if any(c.is_card(Skill) or c.color != Card.BLACK for c in cl):
            return False

        return len(cl) == 2

    @property
    def distance(self):
        return 1 + AttackCardHandler.attack_range_bonus(self.player)


class AutumnLeaves(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class AutumnLeavesHandler(EventHandler):
    group = PostCardMigrationHandler

    def handle(self, p, trans):
        if not p.has_skill(AutumnLeaves):
            return True

        if isinstance(trans.action, (LaunchCard, UseCard)):
            return True

        cond = False
        for cards, _from, to in trans:
            if not to or to.type != 'droppedcard':
                continue

            if _from is None:
                continue

            for c in cards:
                if 'basic' not in c.category:
                    continue

                if c.color != Card.RED:
                    continue

                if _from is None or _from.type not in ('cards', 'showncards', 'equips'):
                    continue

                if _from.owner is p:
                    continue

                cond = True
                break

        if cond and user_input([p], ChooseOptionInputlet(self, (False, True))):
            Game.getgame().process_action(DrawCards(p, 1))

        return True


@register_character
class Shizuha(Character):
    skills = [Decay, AutumnLeaves]
    eventhandlers_required = [AutumnLeavesHandler]
    maxlife = 3
