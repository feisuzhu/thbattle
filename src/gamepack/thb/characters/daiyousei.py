# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import ActionStage, DrawCardStage, migrate_cards, UserAction
from ..cards import Skill, Heal, t_None, t_OtherOne


class Support(UserAction):
    def apply_action(self):
        cl = self.associated_card.associated_cards
        src = self.source
        tgt = self.target
        l = src.tags.get('daiyousei_spnum', 0)
        n = len(cl)
        if l < 3 <= l + n:
            g = Game.getgame()
            g.process_action(Heal(src, src))
        src.tags['daiyousei_spnum'] = l + n
        tgt.reveal(cl)
        migrate_cards([self.associated_card], tgt.cards, unwrap=True)
        self.cards = cl
        return True


class SupportSkill(Skill):
    associated_action = Support
    target = t_OtherOne
    usage = 'handover'
    no_drop = True
    no_reveal = True

    def check(self):
        cl = self.associated_cards
        return cl and all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards', 'equips')
            for c in cl
        )


class Moe(Skill):
    associated_action = None
    target = t_None


class MoeDrawCard(DrawCardStage):
    pass


class DaiyouseiHandler(EventHandler):
    # Well, well, things are getting messy
    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, DrawCardStage):
                tgt = act.target
                if tgt.has_skill(Moe):
                    act.amount += tgt.maxlife - tgt.life
                    act.__class__ = MoeDrawCard
            elif isinstance(act, ActionStage):
                tgt = act.target
                if tgt.has_skill(SupportSkill):
                    tgt.tags['daiyousei_spnum'] = 0
        return act


@register_character
class Daiyousei(Character):
    skills = [SupportSkill, Moe]
    eventhandlers_required = [DaiyouseiHandler]
    maxlife = 3
