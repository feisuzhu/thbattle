# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

class Assault(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target
        src.tags['yugi_assault'] = src.tags['turn_count']
        cards = self.associated_card.associated_cards
        g = Game.getgame()
        if not cards:
            dmg = Damage(src, src)
            dmg.associated_action = self
            g.process_action(dmg)

        dmg = Damage(src, tgt)
        dmg.associated_action = self
        g.process_action(dmg)
        return True

    def is_valid(self):
        p = self.source
        if p.tags.get('turn_count', 0) <= p.tags.get('yugi_assault', 0):
            return False
        return True

class AssaultSkill(Skill):
    associated_action = Assault
    target = t_OtherOne
    distance = 1
    def check(self):
        try:
            cl = self.associated_cards
            if not cl: return True
            if not len(cl) == 1: return False
            if cl[0].is_card(WineCard): return True
            if cl[0].equipment_category == 'weapon': return True
            return False
        except AttributeError:
            return False

class FreakingPowerSkill(Skill):
    associated_action = None
    target = t_None

class FreakingPower(FatetellAction):
    def __init__(self, atkact):
        self.atkact = atkact
        self.source = atkact.source
        self.target = atkact.target

    def apply_action(self):
        act = self.atkact
        src = act.source
        tgt = act.target
        ft = Fatetell(tgt, lambda c: c.suit in (Card.HEART, Card.DIAMOND))
        g = Game.getgame()
        if g.process_action(ft):
            dmg = Damage(src, tgt, act.damage)
            dmg.associated_action = act
            act.cancelled = True
            g.process_action(dmg)
        else:
            act.yugifptag = True
            if g.process_action(act):
                cats = [
                    tgt.cards, tgt.showncards,
                    tgt.equips, tgt.fatetell,
                ]
                card = choose_peer_card(src, tgt, cats)
                if card:
                    g.process_action(DropCards(tgt, [card]))
        return True

class YugiHandler(EventHandler):
    execute_before = (DistanceValidator, )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack) and not hasattr(act, 'yugifptag'):
            src = act.source
            if not src.has_skill(FreakingPowerSkill): return act
            if not src.user_input('choose_option', self): return act
            tgt = act.target
            Game.getgame().process_action(FreakingPower(act))
        elif evt_type == 'action_after' and isinstance(act, CalcDistance):
            card = act.card
            if card.is_card(AssaultSkill):
                src = act.source
                skills = [s for s in src.skills if issubclass(s, WeaponSkill)]
                cl = card.associated_cards
                try:
                    if cl[0].resides_in.type == CardList.EQUIPS:
                        skills.remove(cl[0].equipment_skill)
                except (IndexError, AttributeError, ValueError) as e:
                    pass
                l = [s.range-1 for s in skills]
                if l: act.correction += min(l)
        return act

@register_character
class Yugi(Character):
    skills = [AssaultSkill, FreakingPowerSkill]
    eventhandlers_required = [YugiHandler]
    maxlife = 3
