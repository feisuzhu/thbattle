# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DeadDropCards, DropCards, ForEach, LaunchCard, PlayerDeath, UserAction
from ..actions import ask_for_action
from ..cards import AttackCard, Duel, InstantSpellCardAction, Reject, Skill, TreatAs, VirtualCard
from ..cards import t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler, Game, user_input


# -- code --
class ReversedScales(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class FlowerQueen(TreatAs, Skill):
    treat_as = AttackCard
    skill_category = ('character', 'passive')

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1:
            return False

        if Game.getgame().current_turn is self.player:
            return False

        return cl[0].resides_in.type in ('cards', 'showncards')


class Sadist(Skill):
    distance = 1
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ReversedScalesAction(UserAction):
    def __init__(self, target, action):
        self.source = target
        self.target = target
        self.action = action

    def apply_action(self):
        self.action.__class__ = Duel
        return True


class ReversedScalesHandler(EventHandler):
    execute_before = ('MaidenCostumeHandler', )

    def handle(self, evt_type, act):
        if evt_type != 'action_before':
            return act

        if not isinstance(act, InstantSpellCardAction):
            return act

        if isinstance(act, Reject):
            # HACK
            return act

        if ForEach.get_actual_action(act):
            return act

        src = act.source
        tgt = act.target

        if not src or tgt is src:
            return act

        if not tgt.has_skill(ReversedScales):
            return act

        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        g = Game.getgame()
        g.process_action(ReversedScalesAction(tgt, act))

        return act


class SadistAction(UserAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        tgt.tags['sadist_target'] = False
        g.process_action(Damage(src, tgt, 2))
        return True


class SadistHandler(EventHandler):
    card_usage = 'drop'
    execute_after = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerDeath):
            tgt = act.target.tags.get('sadist_target')
            tgt and Game.getgame().process_action(SadistAction(act.source, tgt))

        elif evt_type == 'action_before' and isinstance(act, DeadDropCards):
            g = Game.getgame()
            src = g.action_stack[-1].source  # source of PlayerDeath
            tgt = act.target

            if not src or src is tgt:
                return act

            if not src.has_skill(Sadist):
                return act

            dist = LaunchCard.calc_distance(tgt, Sadist(src))
            candidates = [k for k, v in dist.items() if v <= 0 and k not in (src, tgt)]

            if not candidates:
                return act

            p, rst = ask_for_action(self, [src], ('cards', 'showncards'), candidates)
            if not p:
                return act

            assert p is src

            cards, pl = rst

            g.process_action(DropCards(src, cards))
            tgt.tags['sadist_target'] = pl[0]

        return act

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)

    def choose_player_target(self, pl):
        return pl[-1:], len(pl)


@register_character_to('common', '-kof')
class Yuuka(Character):
    skills = [ReversedScales, FlowerQueen, Sadist]
    eventhandlers_required = [ReversedScalesHandler, SadistHandler]
    maxlife = 4
