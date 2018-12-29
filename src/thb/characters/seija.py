# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Sequence, Tuple, List

# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import DrawCards, LaunchCard, Pindian, UserAction
from thb.cards.base import Skill, VirtualCard
from thb.cards.classes import AttackCard, BaseAttack, DuelCard, TreatAs, t_None
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler, THBattle


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

        g = self.game
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
        Pindian(src, tgt).action_shootdown_exception()
        return LaunchCard(tgt, [victim], InciteAttack(tgt)).can_fire()


class Incite(Skill):
    associated_action = InciteAction
    skill_category = ['character', 'active']
    usage = 'none'

    def target(self, g: THBattle, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        tl = [t for t in tl if not t.dead and t is not src]

        if not tl:
            return ([], False)

        tl_, valid = AttackCard.target(None, g, tl[0], tl[1:])
        tl = tl[:1]
        tl.extend(tl_)
        return tl, valid

    def check(self):
        return not self.associated_cards


class Reversal(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class ReversalDuel(TreatAs, VirtualCard):
    treat_as = DuelCard

    def check(self):
        return not self.associated_cards


class ReversalHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = [
        'HouraiJewelHandler',
        'RejectHandler',
        'FreakingPowerHandler',
        'RoukankenEffectHandler',
    ]

    execute_after = ['DeathSickleHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            if hasattr(act, 'roukanken_tag'):
                return act

            src = act.source
            tgt = act.target
            g = self.game

            # if tgt is g.current_player: return act
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


@register_character_to('common', '-kof')
class Seija(Character):
    skills = [Incite, Reversal]
    eventhandlers = [ReversalHandler]
    maxlife = 3
