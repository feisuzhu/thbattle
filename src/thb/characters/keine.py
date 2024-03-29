# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionStage, BaseActionStage, Damage, DrawCards, GenericAction, LaunchCard, PlayerTurn
from thb.actions import MaxLifeChange, Reforge, UserAction, migrate_cards, random_choose_card, ttags
from thb.actions import user_choose_cards, user_choose_players
from thb.cards.base import PhysicalCard, Skill, VirtualCard, t_None, t_OtherOne
from thb.cards.basic import Heal
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class TeachTargetReforgeAction(UserAction):
    card_usage = 'reforge'

    def apply_action(self):
        g = self.game
        tgt = self.target
        cl = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        if cl:
            c = cl[0]
        else:
            c = random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
            g.players.reveal(c)
        if not c:
            return False

        g.process_action(Reforge(tgt, tgt, c))
        return True

    def cond(self, cards):
        return len(cards) == 1 and cards[0].is_card(PhysicalCard)


class TeachTargetActionStage(BaseActionStage):
    one_shot = True
    launch_card_cls = LaunchCard


class TeachTargetEffect(GenericAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        tgt = self.target
        c = self.card
        g = self.game
        tgt.reveal(c)
        migrate_cards([c], tgt.cards, unwrap=True)

        choice = g.user_input([tgt], ChooseOptionInputlet(self, ('reforge', 'action')))
        if choice == 'reforge':
            g.process_action(TeachTargetReforgeAction(tgt, tgt))
        else:
            act = TeachTargetActionStage(tgt)
            g.process_action(act)
            if act.action_count == 1:
                return False

            c = random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
            if not c:
                return False

            g.players.reveal(c)
            g.process_action(Reforge(tgt, tgt, c))

        return True


class TeachAction(UserAction):
    no_reveal = True
    card_usage = 'any'

    def apply_action(self):
        src, tgt = self.source, self.target
        cl = VirtualCard.unwrap([self.associated_card])
        assert len(cl) == 1
        g = self.game
        ttags(src)['teach_used'] = True
        g.process_action(Reforge(src, src, cl[0]))
        cl = user_choose_cards(self, src, ('cards', 'showncards', 'equips'))
        c = cl[0] if cl else random_choose_card(g, [src.cards, src.showncards, src.equips])
        if not c:
            return False
        g.process_action(TeachTargetEffect(src, tgt, c))
        return True

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)

    def is_valid(self):
        src = self.source
        return not ttags(src)['teach_used']


class Teach(Skill):
    associated_action = TeachAction
    skill_category = ['character', 'active']
    no_drop = True
    target = t_OtherOne()
    usage = 'reforge'

    def check(self):
        acards = self.associated_cards
        if not acards or len(acards) != 1:
            return False

        c = self.associated_cards[0]
        return c.is_card(PhysicalCard)


class KeineGuard(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'awake', 'once')
    target = t_None()


class KeineGuardAction(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game
        g.process_action(MaxLifeChange(src, src, -1))
        if src.dead:
            return False

        g.process_action(Heal(src, tgt))

        try:
            src.skills.remove(KeineGuard)
        except ValueError:
            pass

        if tgt.life == min(p.life for p in g.players if not p.dead):
            src.skills.append(Devoted)
            src.tags['devoted'] = {
                'to': tgt
            }
            tgt.skills.append(Devoted)
            tgt.tags['devoted'] = {
                'to': src
            }

        return True


class Devoted(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'acquired']
    target = t_None()


class DevotedDrawCards(DrawCards):
    pass


class DevotedHeal(Heal):
    pass


class DevotedHandler(THBEventHandler):
    interested = ['action_before', 'action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            tgt = act.target
            if not tgt.has_skill(Devoted): return act
            cp = tgt.tags['devoted']['to']
            if cp.dead: return act
            if cp.life <= tgt.life: return act
            g = self.game
            g.process_action(DevotedAction(cp, tgt, act))

        elif evt_type == 'action_after' and isinstance(act, Heal):
            tgt = act.target
            if not tgt.has_skill(Devoted): return act
            cp = tgt.tags['devoted']['to']
            if cp.dead: return act
            g = self.game
            if PlayerTurn.get_current(g).target is not cp: return act
            g.process_action(DevotedHeal(tgt, cp, amount=act.amount))

        return act


class DevotedAction(UserAction):
    def __init__(self, source, target, damage):
        self.source = source
        self.target = target
        self.damage = damage

    def apply_action(self):
        src = self.source
        dmg = self.damage
        dmg.target = src
        return True


class KeineGuardHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, ActionStage):
            src = act.target

            g = self.game
            if not src.has_skill(KeineGuard):
                return act

            candidates = list(p for p in g.players if not p.dead and p is not src and p.life < p.maxlife)

            if not (src.has_skill(KeineGuard) and bool(candidates)):
                return act

            tl = user_choose_players(self, src, candidates)
            if not tl:
                return act

            tgt = tl[0]

            g.process_action(KeineGuardAction(src, tgt))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


@register_character_to('common', '-kof')
class Keine(Character):
    skills = [Teach, KeineGuard]
    eventhandlers = [KeineGuardHandler, DevotedHandler]
    maxlife = 4
