# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import user_input_action, Damage, LaunchCard
from ..cards import Card, AttackCard, RedUFOSkill, BaseAttack, Attack, Skill, t_None, t_OtherOne, VirtualCard
from ..inputlets import ChooseOptionInputlet


class SentryHandler(EventHandler):
    execute_after = (
        'RepentanceStickHandler',
        'UmbrellaHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            pcard = getattr(pact, 'associated_card', None)
            if not pcard: return act
            if pcard.is_card(SentryAttack):
                # Sentry effect
                src = pact.source
                if not src.dead and user_input([src], ChooseOptionInputlet(self, (False, True))):
                    # Guard
                    dmg = pcard.target_damage
                    dmg.amount = max(0, dmg.amount - 1)
                    act.cancelled = True
                else:
                    # Attack
                    pass

            elif pcard.is_card(AttackCard) and isinstance(pact, BaseAttack):
                # Sentry fire
                for p in g.players:
                    if p.dead: continue
                    if not p.has_skill(Sentry): continue
                    if p is pact.source: continue

                    tgt = pact.source
                    self.target = tgt  # for ui
                    dist = LaunchCard.calc_distance(p, AttackCard())
                    if dist.get(tgt, 1) > 0: continue

                    def action(p, cl, pl):
                        c = SentryAttack.wrap(cl, p)
                        c.target_damage = act
                        c.resides_in = p.cards
                        return LaunchCard(p, [tgt], c)
                    
                    action = user_input_action(self, action, [p], ('cards', 'showncards', 'equips'), [])
                    if not action: continue
                    g.process_action(action)
            else:
                return act

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        c = cl[0]
        if not (c.is_card(AttackCard) or c.suit == Card.CLUB):
            return False

        return True


class SentryAttack(VirtualCard):
    associated_action = Attack
    target = t_OtherOne
    category = ('basic', )

    def is_card(self, cls):
        from ..cards import AttackCard
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)


class Sentry(Skill):
    associated_action = None
    target = t_None


class SharpEye(RedUFOSkill):
    increment = 1


@register_character
class Momiji(Character):
    skills = [Sentry, SharpEye]
    eventhandlers_required = [SentryHandler]
    maxlife = 4
