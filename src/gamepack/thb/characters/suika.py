# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Drunkard(TreatAsSkill):
    treat_as = WineCard
    def check(self):
        cl = self.associated_cards
        if not (cl and len(cl) == 1 and cl[0].color == Card.BLACK):
            return False
        if cl[0].resides_in.type not in ('handcard', 'showncard', 'equips'):
            return False
        return True

'''
class DrunkardHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire':
            act, valid = arg
            if not isinstance(act, LaunchCard): return arg
            c = act.card
            if not c.is_card(Drunkard): return arg

            src = act.source
            if src.tags['turn_count'] <= src.tags['drunkard_tag']:
                return (act, False)
        elif evt_type == 'action_apply' and isinstance(arg, LaunchCard):
            c = arg.card
            if c.is_card(Drunkard):
                src = arg.source
                src.tags['drunkard_tag'] = src.tags['turn_count']

        return arg
'''

class GreatLandscape(Skill):
    associated_action = None
    target = t_None

class GreatLandscapeHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            act, dist = arg
            card = act.card
            if card.is_card(AttackCard):
                src = act.source
                if not src.has_skill(GreatLandscape): return arg

                for s in src.skills:
                    if issubclass(s, WeaponSkill):
                        return arg

                correction = src.maxlife - src.life
                for p in dist:
                    dist[p] -= correction
        return arg

class WineGod(Skill):
    associated_action = None
    target = t_None

class WineDream(Skill):
    associated_action = None
    target = t_None

class WineGodAwake(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.skills.remove(WineGod)
        tgt.skills.append(WineDream)
        tgt.maxlife -= 1
        tgt.life = min(tgt.life, tgt.maxlife)
        return True

class WineGodHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, WearEquipmentAction):
            card = act.associated_card
            if not card.is_card(IbukiGourdCard): return act
            tgt = act.target
            if not tgt.has_skill(WineGod): return act
            g = Game.getgame()
            g.process_action(WineGodAwake(tgt, tgt))
        return act

class WineDreamHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, SoberUp):
            src = act.source
            if not src.has_skill(WineDream): return act
            g = Game.getgame()
            g.process_action(DrawCards(src, 1))
        return act

@register_character
class Suika(Character):
    skills = [GreatLandscape, Drunkard, WineGod]
    eventhandlers_required = [
        #DrunkardHandler,
        GreatLandscapeHandler,
        WineGodHandler,
        WineDreamHandler
    ]
    maxlife = 4
