# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import ActionStage, DrawCards, DropCards, Fatetell, FatetellAction
from gamepack.thb.actions import LaunchCard, Reforge, UseCard, UserAction, migrate_cards
from gamepack.thb.actions import random_choose_card, user_choose_players
from gamepack.thb.cards import Skill, VirtualCard, t_None, t_OtherOne, t_Self
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class ScienceAction(FatetellAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

    def fatetell_action(self, ft):
        return True

    def fatetell_cond(self, c):
        return 'basic' not in c.category

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Science(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ScienceHandler(EventHandler):
    interested = ('action_after', )
    execute_before = ('PostCardMigrationHandler', 'ScarletPerceptionHandler')
    execute_after = ('FatetellMalleateHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, (LaunchCard, UseCard, DropCards)):
            if isinstance(act, (LaunchCard, UseCard)):
                cards = [act.card]
                src = act.source
            elif isinstance(act, DropCards):
                cards = list(act.cards)
                src = act.target
            else:
                return act

            if not src.has_skill(Science): return act

            cards = VirtualCard.unwrap(cards)
            if not cards: return act
            if not any(['basic' in c.category for c in cards]): return act

            g = Game.getgame()
            if g.current_turn is src: return act

            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(ScienceAction(src, src))
            return act

        elif evt_type == 'action_after' and isinstance(act, Fatetell):
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, ScienceAction): return act
            if not act.succeeded: return act

            c = act.card
            if not c.detached:
                return act

            tl = [p for p in g.players if not p.dead]
            tgt, = user_choose_players(pact, pact.source, tl) or (pact.source, )
            migrate_cards([c], tgt.cards)
            return act

        return act


class Dismantle(Skill):
    skill_category = ('character', 'active')

    def __new__(cls, player):
        if cls is Dismantle:
            kind = player.tags['dismantle_kind']
            if kind == 'own':
                cls = DismantleOwn
            elif kind == 'forced':
                cls = ForcedDismantle
            else:
                cls = DismantleOwn

        return Skill.__new__(cls, player)


class DismantleOwnAction(UserAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        cards = self.associated_card.associated_cards
        assert len(cards) == 1

        g = Game.getgame()
        src = self.source
        tgt = self.target

        return g.process_action(Reforge(src, tgt, cards[0]))


class DismantleOwn(Dismantle):
    skill_category = ('character', 'active')
    associated_action = DismantleOwnAction
    target = t_Self

    usage = 'reforge'
    no_drop = True

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1:
            return False

        if cl[0].resides_in.type not in ('cards', 'showncards', 'equips'):
            return False

        return 'equipment' in cl[0].category


class ForcedDismantleAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        src.tags['dismantle_kind'] = 'used'

        g = Game.getgame()
        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('equips', )))
        c = c or random_choose_card([tgt.equips])

        if c:
            g.process_action(Reforge(src, tgt, c))
            g.process_action(DrawCards(tgt, 1))

        return True

    def is_valid(self):
        return bool(self.target.equips)


class ForcedDismantle(Dismantle):
    associated_action = ForcedDismantleAction
    skill_category = ('character', 'active')
    target = t_OtherOne

    def check(self):
        return not self.associated_cards


class DismantleHandler(EventHandler):
    interested = ('action_apply', 'action_shootdown')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            tgt = act.target
            if not tgt.has_skill(Dismantle):
                return act

            kind = user_input([tgt], ChooseOptionInputlet(self, ('own', 'forced')))
            tgt.tags['dismantle_kind'] = kind

        return act


@register_character
class Nitori(Character):
    skills = [Science, Dismantle]
    eventhandlers_required = [ScienceHandler, DismantleHandler]
    maxlife = 3
