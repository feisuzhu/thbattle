# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import DrawCards, LaunchCard, Reforge, UseCard, UserAction
from gamepack.thb.actions import random_choose_card, ttags
from gamepack.thb.cards import Attack, AttackCard, GrazeCard, Skill, VirtualCard, t_One, t_OtherOne
from gamepack.thb.characters.baseclasses import Character, register_character_to
from gamepack.thb.inputlets import ChoosePeerCardInputlet


# -- code --
class DismantleAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        ttags(src)['dismantle'] = True

        g = Game.getgame()
        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('equips', )))
        c = c or random_choose_card([tgt.equips])

        if c:
            g.process_action(Reforge(src, tgt, c))
            g.process_action(DrawCards(tgt, 1))

        return True

    def is_valid(self):
        return not ttags(self.source)['dismantle'] and bool(self.target.equips)


class Dismantle(Skill):
    associated_action = DismantleAction
    skill_category = ('character', 'active')
    target = t_One

    def check(self):
        return not self.associated_cards


class Craftsman(Skill):
    associated_action = Attack
    target = t_OtherOne
    skill_category = ('character', 'active')
    category = ('basic', )
    distance = 1
    usage = 'launch'

    def is_card(self, cls):
        for c in (AttackCard, GrazeCard, self.__class__):
            if issubclass(c, cls):
                return True

        return False

    def check(self):
        cl = self.associated_cards
        p = self.player
        return cl and set(cl) == (set(p.cards) | set(p.showncards))


class CraftsmanHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, (LaunchCard, UseCard)):
            c = act.card
            s = VirtualCard.find_in_hierarchy(c, Craftsman)
            if not s: return act
            cards = VirtualCard.unwrap([s])
            if not all('basic' in i.category for i in cards): return act
            g = Game.getgame()
            g.process_action(DrawCards(act.source, 1))

        return act


@register_character_to('common', '-kof')
class Nitori(Character):
    skills = [Dismantle, Craftsman]
    eventhandlers_required = [CraftsmanHandler]
    maxlife = 3
