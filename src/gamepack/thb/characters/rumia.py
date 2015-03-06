# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import ActionShootdown, EventHandler, Game
from gamepack.thb.actions import Damage, DrawCards, LaunchCard, PlayerTurn, UserAction
from gamepack.thb.actions import user_choose_cards
from gamepack.thb.cards import Attack, AttackCard, BaseDuel, PhysicalCard, RejectCard, Skill, t_None, t_OtherN
from gamepack.thb.characters.baseclasses import Character, register_character_to


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
        return issubclass(c.associated_action, Attack)

    def ask_for_action_verify(self, p, cl, tl):
        attacker, victim = self.target_list
        return LaunchCard(attacker, [victim], cl[0]).can_fire()

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


class DarknessKOF(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class DarknessKOFAction(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        tgt.tags['darkness_kof_tag'] = max(g.turn_count, 1)
        return True


class DarknessKOFLimit(ActionShootdown):
    pass


class DarknessKOFHandler(EventHandler):
    interested = ('character_debut', 'action_shootdown')

    def handle(self, evt_type, arg):
        if evt_type == 'character_debut':
            old, new = arg
            if new.has_skill(DarknessKOF):
                g = Game.getgame()
                g.process_action(DarknessKOFAction(new, new))

        elif evt_type == 'action_shootdown' and isinstance(arg, LaunchCard):
            src = arg.source
            if not src:
                return arg

            g = Game.getgame()
            opp = g.get_opponent(arg.source)
            if opp.tags['darkness_kof_tag'] < g.turn_count:
                return arg

            card = arg.card
            if not card.is_card(PhysicalCard):
                return arg

            if card.is_card(RejectCard):
                return arg

            # XXX: DollControl's second target do not count as target
            # but in KOF the second target is always the launcher,
            # and never be the opp, so the handle can be same.
            if opp in arg.target_list:
                raise DarknessKOFLimit

        return arg


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


@register_character_to('common', '-kof')
class Rumia(Character):
    skills = [Darkness, Cheating]
    eventhandlers_required = [CheatingHandler]
    maxlife = 3


@register_character_to('kof')
class RumiaKOF(Character):
    skills = [DarknessKOF, Cheating]
    eventhandlers_required = [DarknessKOFHandler, CheatingHandler]
    maxlife = 3
