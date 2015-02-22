# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, LaunchCard, user_choose_cards
from ..cards import AttackCard, BaseAttack, Card, RedUFOSkill, Skill, TreatAs, VirtualCard, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class SentryHandler(EventHandler):
    interested = ('action_before',)
    execute_after = (
        'RepentanceStickHandler',
        'UmbrellaHandler',
    )
    card_usage = 'launch'

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
                    cl = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
                    if not cl: continue
                    c = SentryAttack.wrap(cl, p)
                    c.target_damage = act
                    g.process_action(LaunchCard(p, [tgt], c))
            else:
                return act

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        c = cl[0]
        if not (c.is_card(AttackCard) or c.suit == Card.CLUB):
            return False

        return True


class SentryAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class Sentry(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SharpEye(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


@register_character
class Momiji(Character):
    skills = [Sentry, SharpEye]
    eventhandlers_required = [SentryHandler]
    maxlife = 4
