# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCards, LaunchCard, PlayerTurn, UserAction, user_choose_cards
from ..cards import AttackCard, BaseDuel, Skill, t_None, t_OtherN, Attack
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class DarknessDuel(BaseDuel):
    pass


class DarknessAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        attacker, victim = self.target_list
        src = self.source
        g = Game.getgame()
        tags = self.source.tags
        tags['darkness_tag'] = tags['turn_count']

        cards = user_choose_cards(self, attacker, ('cards', 'showncards'))
        if cards:
            c = cards[0]
            g.process_action(LaunchCard(attacker, [victim], c))
        else:
            g.process_action(Damage(src, attacker, 1))

        return True

    def cond(self, cl):
        if len(cl) != 1: return False
        c = cl[0]
        if not c.associated_action: return False
        if not issubclass(c.associated_action, Attack): return False

        attacker, victim = self.target_list
        return LaunchCard(attacker, [victim], c).can_fire()

    def is_valid(self):
        tags = self.source.tags
        if tags['turn_count'] <= tags['darkness_tag']:
            return False

        attacker, victim = self.target_list
        if not LaunchCard(attacker, [victim], AttackCard()).can_fire():
            return False

        return True


class Darkness(Skill):
    associated_action = DarknessAction
    skill_category = ('character', 'active')
    target = t_OtherN(2)
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if not(cl and len(cl) == 1): return False
        c = cl[0]
        if c.resides_in is None or c.resides_in.type not in (
            'cards', 'showncards', 'equips'
        ): return False
        return True


class Cheating(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class CheatingDrawCards(DrawCards):
    pass


class CheatingHandler(EventHandler):
    interested = ('action_after',)
    execute_before = ('CiguateraHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if tgt.has_skill(Cheating) and not tgt.dead:
                g = Game.getgame()
                g.process_action(CheatingDrawCards(tgt, 1))
        return act


@register_character
class Rumia(Character):
    skills = [Darkness, Cheating]
    eventhandlers_required = [CheatingHandler]
    maxlife = 3
