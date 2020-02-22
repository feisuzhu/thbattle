# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import DrawCards, ForEach, LaunchCard, PlayerTurn, UserAction
from thb.cards.base import Skill
from thb.cards.classes import AttackCard, DollControlCard, Heal, InstantSpellCardAction, RejectCard
from thb.cards.classes import t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class FlyingSkandaAction(ForEach):
    @property
    def action_cls(self):
        skill = self.associated_card
        card = skill.associated_cards[0]
        action = card.associated_action
        return action

    def is_valid(self):
        p = self.source
        if p.tags['turn_count'] <= p.tags['flying_skanda']:
            return False
        if any(t.dead for t in self.target_list):
            return False
        return True

    def get_actual_action(self, act):
        return None


class FlyingSkanda(Skill):
    associated_action = FlyingSkandaAction
    skill_category = ['character', 'active']
    usage = 'launch'

    def target(self, g, source, tl):
        tl = [ch for ch in tl if not ch.dead]
        cl = self.associated_cards
        if not cl: return ([], False)
        c = cl[0]
        if len(tl) < 2:
            return c.target(g, source, tl)
        else:
            rst = c.target(g, source, tl[:-1])
            a = tl[-1]
            if a is source:
                return rst[0], False
            else:
                return rst[0] + [a], rst[1]

    @property
    def distance(self):
        cl = self.associated_cards
        if not cl: return 0
        return cl[0].distance

    def check(self):
        cl = self.associated_cards
        if len(cl) != 1: return False
        c = cl[0]
        if c.is_card(AttackCard): return True

        if c.is_card(DollControlCard): return False
        if c.is_card(RejectCard): return False

        act = c.associated_action
        if not act: return False
        if not issubclass(act, InstantSpellCardAction): return False

        return True

    def is_card(self, cls):
        cl = self.associated_cards
        if cl and cl[0].is_card(cls): return True
        return isinstance(self, cls)


class FlyingSkandaHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, LaunchCard):
            if not act.card.is_card(FlyingSkanda): return act
            act.source.tags['flying_skanda'] = act.source.tags['turn_count']
        return act


class ShikigamiAction(UserAction):
    def apply_action(self):
        tgt = self.target
        src = self.source

        g = self.game

        if tgt.life < tgt.maxlife and g.user_input(
            [tgt], ChooseOptionInputlet(self, (False, True))
        ):
            g.process_action(Heal(src, tgt))
        else:
            g.process_action(DrawCards(tgt, 2))

        tgt.tags['shikigami_target'] = src
        src.tags['shikigami_target'] = tgt
        src.tags['shikigami_tag'] = src.tags['turn_count']

        return True

    def is_valid(self):
        return 'shikigami_tag' not in self.source.tags


class Shikigami(Skill):
    associated_action = ShikigamiAction
    skill_category = ['character', 'active', 'once']
    target = t_OtherOne

    def check(self):
        return not self.associated_cards


class ShikigamiHandler(THBEventHandler):
    interested = ['post_calcdistance']

    def handle(self, evt_type, arg):
        if evt_type == 'post_calcdistance':
            src, card, dist = arg
            if not card.is_card(AttackCard): return arg

            tgt = src.tags.get('shikigami_target')
            if not tgt or tgt.dead: return arg

            g = self.game
            current = PlayerTurn.get_current(g).target
            if current is not src: return arg

            origin = src if 'shikigami_tag' in src.tags else tgt
            if origin.tags['shikigami_tag'] != origin.tags['turn_count']:
                return arg

            dist2 = LaunchCard.calc_raw_distance(g, tgt, AttackCard())

            for k in dist2:
                if dist[k] > 0 and dist2[k] <= 1:
                    dist[k] = 0

        return arg


@register_character_to('common', '-kof')
class Chen(Character):
    skills = [FlyingSkanda, Shikigami]
    eventhandlers = [FlyingSkandaHandler, ShikigamiHandler]
    maxlife = 4
