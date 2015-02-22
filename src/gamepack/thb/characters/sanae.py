# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import DrawCards, ForEach, GenericAction, UserAction, migrate_cards
from gamepack.thb.actions import random_choose_card, ttags, user_choose_cards, user_choose_players
from gamepack.thb.cards import Heal, Skill, VirtualCard, t_Self
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
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


class GodDescendant(Skill):
    associated_action = None
    skill_category = ('character', 'passive')


class GodDescendantSkipAction(UserAction):
    def __init__(self, source, target, act):
        self.source = source
        self.target = target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True


class GodDescendantDrawAction(UserAction):
    def __init__(self, source, target, act):
        self.source = source
        self.target = target
        self.action = act

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        g.process_action(DrawCards(tgt, 1))
        return True


class GodDescendantHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('MaidenCostumeHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and ForEach.is_group(act):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(GodDescendant): return act

            opt = user_input([tgt], ChooseOptionInputlet(self, ('skip', 'draw', None)))

            if opt == 'skip':
                g.process_action(GodDescendantSkipAction(tgt, tgt, act))
            elif opt == 'draw':
                g.process_action(GodDescendantDrawAction(tgt, tgt, act))

        return act


@register_character
class Sanae(Character):
    skills = [Miracle, SanaeFaith, GodDescendant]
    eventhandlers_required = [GodDescendantHandler]
    maxlife = 3
