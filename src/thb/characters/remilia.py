# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import ActionShootdown, Damage, GenericAction, LaunchCard, PrepareStage, UserAction
from thb.cards import Attack, AttackCard, Card, DummyCard, Heal, InevitableAttack, Skill, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class SpearTheGungnir(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SpearTheGungnirAction(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        self.act.__class__ = InevitableAttack
        return True


class SpearTheGungnirHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('ScarletRhapsodySwordHandler', )
    execute_after = (
        'HakuroukenEffectHandler',
        'HouraiJewelHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Attack):
            src = act.source
            if not src.has_skill(SpearTheGungnir): return act
            if isinstance(act, InevitableAttack): return act

            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            if user_input([act.source], ChooseOptionInputlet(self, (False, True))):
                Game.getgame().process_action(SpearTheGungnirAction(act))

        return act


class VampireKiss(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class VampireKissAction(GenericAction):
    def apply_action(self):
        return Game.getgame().process_action(
            Heal(self.target, self.source)
        )


class VampireKissHandler(EventHandler):
    interested = ('action_apply', 'calcdistance')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (src and src.has_skill(VampireKiss)): return act
            if src.life >= src.maxlife: return act
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            card = pact.associated_card
            if (not card) or card.color != Card.RED: return act
            g.process_action(VampireKissAction(src, tgt))

        elif evt_type == 'calcdistance':
            src, card, dist = act

            if not card.is_card(AttackCard): return act
            if not src.has_skill(VampireKiss): return act
            if card.color != Card.RED: return act

            for p in dist:
                dist[p] -= 99999

        return act


class ScarletMistAttackLimit(ActionShootdown):
    pass


class ScarletMistHandler(EventHandler):
    interested = (
        'action_after',
        'action_apply',
        'action_shootdown',
        'post_calcdistance',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown' and isinstance(act, LaunchCard):
            if act.bypass_check: return act
            c = act.card
            if not c.is_card(AttackCard): return act

            src, tgt  = act.source, act.target
            if not src.tags['scarlet_mist'] == 'nerf':
                return act

            dist = LaunchCard.calc_raw_distance(src, DummyCard())
            if dist[tgt] > 1:
                raise ScarletMistAttackLimit

        elif evt_type == 'post_calcdistance':
            src, c, dist = act

            if not c.is_card(AttackCard):
                return act

            if src.tags['scarlet_mist'] != 'buff':
                return act

            for k in dist:
                dist[k] = 0

        elif evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not (src and src.tags['scarlet_mist'] == 'buff'): return act
            if src.life >= src.maxlife: return act

            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            if not pact.associated_card: return act

            g.process_action(Heal(src, src, act.amount))

        elif evt_type == 'action_apply' and isinstance(act, PrepareStage):
            tgt = act.target
            if not tgt.has_skill(ScarletMist): return act
            if not tgt.tags['scarlet_mist']: return act
            g = Game.getgame()
            g.process_action(ScarletMistEndAction(None, None))

        return act


class ScarletMistAction(UserAction):
    def apply_action(self):
        src, tl = self.source, self.target_list
        src.tags['scarlet_mist_used'] = True
        g = Game.getgame()
        for p in g.players:
            p.tags['scarlet_mist'] = 'nerf'
        for p in tl:
            p.tags['scarlet_mist'] = 'buff'

        return True

    def is_valid(self):
        src = self.source
        return not src.tags['scarlet_mist_used']


class ScarletMistEndAction(GenericAction):
    def apply_action(self):
        g = Game.getgame()
        for p in g.players:
            p.tags['scarlet_mist'] = False

        return True


class ScarletMist(Skill):
    associated_action = ScarletMistAction
    skill_category = ('character', 'active', 'once', 'boss')

    def check(self):
        return not len(self.associated_cards)

    def target(self, g, source, tl):
        from thb.thbidentity import Identity
        n = sum(i == Identity.TYPE.ACCOMPLICE for i in g.identities)
        n -= sum(p.dead and p.identity.type == Identity.TYPE.ACCOMPLICE for p in g.players)

        tl = [t for t in tl if not t.dead]
        try:
            tl.remove(source)
        except ValueError:
            pass

        tl.insert(0, source)
        return (tl[:n+1], bool(len(tl)))


@register_character_to('common', 'boss')
class Remilia(Character):
    skills = [SpearTheGungnir, VampireKiss]
    boss_skills = [ScarletMist]
    eventhandlers_required = [SpearTheGungnirHandler, VampireKissHandler, ScarletMistHandler]
    maxlife = 4
