# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards, LaunchCard, Pindian, UserAction
from ..cards import AttackCard, BaseAttack, DuelCard, Skill, TreatAs, VirtualCard, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class InciteAttack(TreatAs, VirtualCard):
    treat_as = AttackCard

    def check(self):
        return not self.associated_cards


class InciteFailAttack(TreatAs, VirtualCard):
    treat_as = AttackCard
    distance = 99999

    def check(self):
        return not self.associated_cards


class InciteSilentFailAction(UserAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        return True


class InciteAction(UserAction):
    def apply_action(self):
        src = self.source
        tags = src.tags
        tgt, victim = self.target_list

        tags['incite_tag'] = tags['turn_count']

        g = Game.getgame()
        if g.process_action(Pindian(src, tgt)):
            g.process_action(LaunchCard(tgt, [victim], InciteAttack(tgt)))

        else:
            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(LaunchCard(tgt, [src], InciteFailAttack(tgt)))
            else:
                g.process_action(InciteSilentFailAction(src, tgt))

        return True

    def is_valid(self):
        src = self.source
        tags = src.tags
        if tags['turn_count'] <= tags['incite_tag']:
            return False

        tgt, victim = self.target_list
        if not Pindian(src, tgt).can_fire(): return False
        return LaunchCard(tgt, [victim], InciteAttack(tgt)).can_fire()


class Incite(Skill):
    associated_action = InciteAction
    skill_category = ('character', 'active')
    usage = 'none'

    def target(self, g, source, tl):
        tl = [t for t in tl if not t.dead]

        if not tl or tl[0] is source:
            return ([], False)

        tl_, valid = AttackCard.target(g, tl[0], tl[1:])
        return tl[:1] + tl_, valid

    def check(self):
        return not self.associated_cards


class Reversal(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ReversalDuel(TreatAs, VirtualCard):
    treat_as = DuelCard

    def check(self):
        return not self.associated_cards


class ReversalHandler(EventHandler):
    interested = ('action_before',)
    execute_before = (
        'HouraiJewelHandler',
        'RejectHandler',
        'YugiHandler',
        'RoukankenEffectHandler',
    )

    execute_after = (
        'DeathSickleHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            if hasattr(act, 'roukanken_tag'):
                return act

            src = act.source
            tgt = act.target
            g = Game.getgame()

            # if tgt is g.current_turn: return act
            if not tgt.has_skill(Reversal):
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            def nhand(p):
                return len(p.cards) + len(p.showncards)

            g.process_action(DrawCards(tgt, 1))
            if nhand(tgt) > nhand(src):
                g.process_action(LaunchCard(src, [tgt], ReversalDuel(src)))
                act.cancelled = True

        return act


@register_character
class Seija(Character):
    skills = [Incite, Reversal]
    eventhandlers_required = [ReversalHandler]
    maxlife = 3
