# -*- coding: utf-8 -*-

from game.autoenv import Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, GenericAction, UserAction, user_choose_players, user_choose_cards, ttags, random_choose_card, migrate_cards
from ..cards import Skill, Heal, t_Self, VirtualCard


class MiracleHeal(Heal):
    pass


class MiracleAction(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        g.process_action(DrawCards(tgt, 1))
        ttags(tgt)['miracle_times'] += 1
        if ttags(tgt)['miracle_times'] == 3:
            candidates = [p for p in g.players if not p.dead and p.life < p.maxlife]
            if candidates:
                beneficiery, = user_choose_players(self, tgt, candidates) or (None,)
                if beneficiery:
                    g.process_action(MiracleHeal(tgt, beneficiery))

        return True

    def choose_player_target(self, tl):
        return tl[-1:], bool(tl)

    def cond(self, cl):
        return True

    def is_valid(self):
        tgt = self.target
        return len(self.associated_card.associated_cards) == ttags(tgt)['miracle_times'] + 1


class Miracle(Skill):
    associated_action = MiracleAction
    skill_category = ('character', 'active')
    target = t_Self
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        return cl and all(
            c.resides_in is not None and
            c.resides_in.type in (
                'cards', 'showncards', 'equips'
            ) for c in self.associated_cards
        )


class SanaeFaithCollectCardAction(GenericAction):
    card_usage = 'handover'
    no_reveal = True

    def apply_action(self):
        src, tgt = self.source, self.target
        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        c = cards[0] if cards else random_choose_card([tgt.cards, tgt.showncards])
        src.reveal(c)
        migrate_cards([c], src.cards)

        return True

    def cond(self, cl):
        return len(cl) == 1 and \
            cl[0].resides_in.type in ('cards', 'showncards') and \
            not cl[0].is_card(VirtualCard)


class SanaeFaithReturnCardAction(GenericAction):
    card_usage = 'handover'
    no_reveal = True

    def apply_action(self):
        src, tgt = self.source, self.target
        cards = user_choose_cards(self, src, ('cards', 'showncards', 'equips'))
        c = cards[0] if cards else random_choose_card([src.cards, src.showncards, src.equips])
        if not c:
            return False

        tgt.reveal(c)
        migrate_cards([c], tgt.cards)

        return True

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)


class SanaeFaithAction(UserAction):
    def apply_action(self):
        src = self.source
        tl = self.target_list
        g = Game.getgame()

        for p in tl:
            g.process_action(SanaeFaithCollectCardAction(src, p))

        for p in tl:
            g.process_action(SanaeFaithReturnCardAction(src, p))

        ttags(src)['faith'] = True

        return True

    def is_valid(self):
        src = self.source
        return not ttags(src)['faith']


class SanaeFaith(Skill):
    associated_action = SanaeFaithAction
    skill_category = ('character', 'active')
    usage = 'launch'

    @staticmethod
    def target(g, source, tl):
        tl = [t for t in tl if not t.dead and (t.cards or t.showncards)]
        try:
            tl.remove(source)
        except ValueError:
            pass

        return (tl[:2], bool(len(tl)))

    def check(self):
        return not self.associated_cards


@register_character
class Sanae(Character):
    skills = [Miracle, SanaeFaith]
    eventhandlers_required = []
    maxlife = 3
