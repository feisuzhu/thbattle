# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DrawCards, ForEach, LaunchCard, PlayerDeath, UserAction
from gamepack.thb.actions import user_choose_players
from gamepack.thb.cards import AttackCard, Duel, InstantSpellCardAction, Reject, Skill, TreatAs
from gamepack.thb.cards import t_None
from gamepack.thb.characters.baseclasses import Character, register_character_to
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class ReversedScales(TreatAs, Skill):
    skill_category = ('character', 'active', 'compulsory')
    treat_as = AttackCard

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1:
            return False

        if Game.getgame().current_player is self.player:
            return False

        return cl[0].resides_in.type in ('cards', 'showncards')


class Sadist(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SadistKOF(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SadistKOFDrawCards(DrawCards):
    pass


class SadistKOFDamageAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        return g.process_action(Damage(src, tgt, 1))


class SadistKOFHandler(EventHandler):
    interested = ('action_after', 'character_debut')
    execute_after = ('DeathHandler', )

    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, PlayerDeath):
            tgt = arg.target
            g = Game.getgame()
            op = g.get_opponent(tgt)
            if arg.source is op and op.has_skill(SadistKOF):
                g.process_action(SadistKOFDrawCards(op, 2))
                op.tags['sadist_kof_fire'] = True

        elif evt_type == 'character_debut':
            old, new = arg
            if not old: return arg

            g = Game.getgame()
            op = g.get_opponent(new)

            if op.has_skill(SadistKOF) and op.tags['sadist_kof_fire']:
                op.tags['sadist_kof_fire'] = False
                g.process_action(SadistKOFDamageAction(op, new))

        return arg


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
    interested = ('action_after', 'action_before')
    card_usage = 'drop'
    execute_before = ('WineHandler', )
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

        elif evt_type == 'action_before' and isinstance(act, Damage):
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


@register_character_to('kof')
class YuukaKOF(Character):
    skills = [ReversedScales, SadistKOF]
    eventhandlers_required = [ReversedScalesHandler, SadistKOFHandler]
    maxlife = 4
