# -*- coding: utf-8 -*-

from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import user_choose_cards, Damage, LaunchCard
from ..cards import Card, AttackCard, BaseAttack, Attack, Skill, t_None, t_OtherOne, VirtualCard
from ..inputlets import ChooseOptionInputlet


class SentryHandler(EventHandler):
    execute_after = ('RepentanceStickHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            pcard = getattr(pact, 'associated_card', None)
            if not pcard: return act
            if pcard.is_card(SentryAttack):
                # Sentry effect
                src = pact.source
                assert src.has_skill(Sentry)
                if user_input([src], ChooseOptionInputlet(self, (False, True))):
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
                    if not dist[tgt] <= 0: continue
                    cl = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
                    if not cl: continue
                    c = SentryAttack.wrap(cl, p)
                    c.target_damage = act
                    c.resides_in = p.cards
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


@register_character
class Momiji(Character):
    skills = [Sentry]
    eventhandlers_required = [SentryHandler]
    maxlife = 4
