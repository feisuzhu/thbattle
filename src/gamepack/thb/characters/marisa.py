# -*- coding: utf-8 -*-
from game.autoenv import Game, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, migrate_cards, random_choose_card, LaunchCard
from ..cards import Skill, AttackCard, t_OtherOne, TreatAsSkill
from ..inputlets import ChoosePeerCardInputlet


class Daze(TreatAsSkill):
    treat_as = AttackCard
    distance = 99999

    def check(self):
        if self.associated_cards: return False
        return True


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

        g.process_action(LaunchCard(tgt, [src], Daze(tgt)))

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
    target = t_OtherOne

    def check(self):
        if self.associated_cards: return False
        return True


@register_character
class Marisa(Character):
    skills = [Borrow]
    eventhandlers_required = []
    maxlife = 4
