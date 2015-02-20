# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import LaunchCard, UserAction, migrate_cards, random_choose_card
from ..cards import AttackCard, Skill, TreatAs, VirtualCard, t_OtherOne
from ..inputlets import ChoosePeerCardInputlet
from .baseclasses import Character, register_character
from game.autoenv import Game, user_input


# -- code --
class Daze(TreatAs, VirtualCard):
    treat_as = AttackCard


class BorrowAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()

        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards', 'equips')))
        c = c or random_choose_card([tgt.cards, tgt.showncards])
        if not c: return False
        src.reveal(c)
        migrate_cards([c], src.cards)
        src.tags['borrow_tag'] = src.tags['turn_count']

        g.process_action(LaunchCard(tgt, [src], Daze(tgt), bypass_check=True))

        return True

    def is_valid(self):
        src = self.source
        tgt = self.target
        if src.tags['turn_count'] <= src.tags['borrow_tag']:
            return False

        if not (tgt.cards or tgt.showncards or tgt.equips):
            return False

        return True


class Borrow(Skill):
    associated_action = BorrowAction
    skill_category = ('character', 'active')
    target = t_OtherOne

    def check(self):
        if self.associated_cards: return False
        return True


@register_character
class Marisa(Character):
    skills = [Borrow]
    eventhandlers_required = []
    maxlife = 4
