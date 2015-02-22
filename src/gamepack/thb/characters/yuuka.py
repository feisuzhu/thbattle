# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, ForEach, LaunchCard, PlayerDeath, UserAction, user_choose_players
from ..cards import AttackCard, Duel, InstantSpellCardAction, Reject, Skill, TreatAs, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character_to
from game.autoenv import EventHandler, Game, user_input


# -- code --
class ReversedScales(TreatAs, Skill):
    skill_category = ('character', 'active', 'compulsory')
    treat_as = AttackCard

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
    interested = ('action_before',)
    execute_before = ('MaidenCostumeHandler', )

    def handle(self, evt_type, act):
        if evt_type != 'action_before':
            return act

        if not isinstance(act, InstantSpellCardAction):
            return act

        if isinstance(act, Reject):
            # HACK
            return act

        if ForEach.is_group(act):
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
        g.process_action(Damage(src, tgt, 1))
        return True


class SadistHandler(EventHandler):
    interested = ('action_after', 'action_apply')
    card_usage = 'drop'
    execute_after = ('DeathHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerDeath):
            src = act.source
            if not src or not src.has_skill(Sadist):
                return act

            dist = LaunchCard.calc_distance(src, AttackCard())
            candidates = [k for k, v in dist.items() if v <= 0 and k is not src]

            if not candidates:
                return act

            pl = user_choose_players(self, src, candidates)
            if pl:
                Game.getgame().process_action(SadistAction(src, pl[0]))

        elif evt_type == 'action_apply' and isinstance(act, Damage):
            src = act.source
            tgt = act.target

            if not src or src is tgt:
                return act

            if not src.has_skill(Sadist):
                return act

            if tgt.life == 1:
                act.amount += 1

        return act

    def choose_player_target(self, pl):
        return pl[-1:], len(pl)


@register_character_to('common', '-kof')
class Yuuka(Character):
    skills = [ReversedScales, Sadist]
    eventhandlers_required = [ReversedScalesHandler, SadistHandler]
    maxlife = 4
