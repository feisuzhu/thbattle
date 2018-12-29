# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import ActionStage, ForEach, GenericAction, LaunchCard, LifeLost, PlayerDeath
from thb.actions import UserAction
from thb.cards.base import Skill
from thb.cards.classes import AttackCard, AttackCardVitalityHandler, t_None, t_Self
from thb.characters.base import Character, register_character_to
from thb.common import CharChoice
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler
from thb.thbkof import KOFCharacterSwitchHandler


# -- code --
class HeterodoxySkipAction(GenericAction):
    def apply_action(self):
        return True


class HeterodoxyHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['MaidenCostumeHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and ForEach.is_group_effect(act):
            tgt = act.target
            if not tgt.has_skill(Heterodoxy): return act

            g = self.game
            for a in reversed(g.action_stack):
                if isinstance(a, HeterodoxyAction):
                    break
            else:
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            act.cancelled = True
            g.process_action(HeterodoxySkipAction(tgt, tgt))

        return act


class HeterodoxyAction(UserAction):
    def apply_action(self):
        g = self.game
        card = self.associated_card.associated_cards[0]
        src = self.source
        victim = self.target
        tgts = self.target_list[1:]

        g.players.reveal(card)

        if card.is_card(AttackCard):
            src.tags['vitality'] -= 1

        # XXX: Use card owned by other
        lc = LaunchCard(victim, tgts, card)

        g = self.game
        g.process_action(lc)

        return True

    def is_valid(self):
        src = self.source
        card = self.associated_card.associated_cards[0]
        if card.is_card(AttackCard) and src.tags['vitality'] < 1:
            if not AttackCardVitalityHandler.is_disabled(src):
                return False

        if card.usage != 'launch':
            return False

        victim = self.target
        tgts = self.target_list[1:]
        lc = LaunchCard(victim, tgts, card)
        return lc.can_fire()


class Heterodoxy(Skill):
    no_drop = True
    associated_action = HeterodoxyAction
    skill_category = ['character', 'active']
    usage = 'handover'

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].resides_in.type in ('cards', 'showncards') and
            not cl[0].is_card(Skill) and
            getattr(cl[0], 'associated_action', None)
        )

    def target(self, g, src, tl):
        cl = self.associated_cards
        if not cl: return ([], False)
        c = cl[0]
        tname = c.target.__name__

        tl = [t for t in tl if not t.dead]

        if not tl: return [], False
        if tl[0] is self.player: return [], False

        if tname in ('t_Self', 't_All', 't_AllInclusive'):
            return tl[-1:], True
        else:
            _tl, valid = c.target(g, tl[0], tl[1:])
            return [tl[0]] + _tl, valid


class Summon(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'once']
    target = t_None


class SummonAction(UserAction):

    def apply_action(self):
        src, tgt = self.source, self.target

        skills = tgt.skills
        skills = [s for s in skills if 'character' in s.skill_category]
        skills = [s for s in skills if 'once' not in s.skill_category]
        skills = [s for s in skills if 'awake' not in s.skill_category]

        if not skills: return False

        mapping = self.mapping = {s.__name__: s for s in skills}
        names = list(sorted(mapping.keys()))

        choice = user_input([src], ChooseOptionInputlet(self, names)) or names[0]

        src.tags['summon_used'] = True
        src.skills.append(mapping[choice])
        self.choice = mapping[choice]

        return True


class SummonHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, PlayerDeath):
            g = self.game
            p = getattr(g, 'current_player', None)

            if not p: return act
            if p is act.target: return act
            if not p.has_skill(Summon): return act
            if p.tags['summon_used']: return act
            if not user_input([p], ChooseOptionInputlet(self, (False, True))): return act

            g.process_action(SummonAction(p, act.target))

        return act


class SummonKOFAction(UserAction):
    def apply_action(self):
        # WHOLE BUNCH OF MEGA HACK
        old = self.target
        g = self.game
        old_life, maxlife_delta = old.life, old.maxlife - old.__class__.maxlife

        ActionStage.force_break(g)

        assert g.current_player is old

        handler = g.dispatcher.find_by_cls(KOFCharacterSwitchHandler)
        tgt = handler.switch(old)
        g.current_player = tgt

        tgt.life = old_life
        tgt.maxlife += maxlife_delta

        for l in ('cards', 'showncards', 'equips', 'fatetell', 'special'):
            s, t = getattr(old, l), getattr(tgt, l)
            for i in list(s):
                i.move_to(t)

        for s in old.skills:
            if 'character' not in s.skill_category:
                tgt.skills.append(s)

        for act in g.action_stack:
            # Meh... good enough
            if act.source is old:
                act.source = tgt

            if act.target is old:
                act.target = tgt

            if isinstance(act, LaunchCard):
                act.target_list = [
                    tgt if p is old else p
                    for p in act.target_list
                ]

        tgt.tags = old.tags

        tgt.choices.append(CharChoice(old.__class__))

        if tgt.life > tgt.maxlife:
            g.process_action(LifeLost(tgt, tgt, tgt.life - tgt.maxlife))

        self.transition = [old, tgt]

        g.emit_event('character_debut', (old, tgt))

        return True


class SummonKOFCollect(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        src.choices.append(CharChoice(tgt.__class__))
        return True


class SummonKOFHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerDeath):
            g = self.game
            src, tgt = act.source, act.target
            p = g.get_opponent(tgt)

            if not (src is p and p.has_skill(SummonKOF)):
                return act

            g.process_action(SummonKOFCollect(p, tgt))

        return act


class SummonKOF(Skill):
    associated_action = SummonKOFAction
    skill_category = ['character', 'active']
    target = t_Self

    def check(self):
        cl = self.associated_cards
        return len(cl) == 0


@register_character_to('common', '-kof')
class Seiga(Character):
    skills = [Heterodoxy, Summon]
    eventhandlers = [HeterodoxyHandler, SummonHandler]
    maxlife = 4


@register_character_to('kof')
class SeigaKOF(Character):
    skills = [SummonKOF]
    eventhandlers = [SummonKOFHandler]
    maxlife = 4
