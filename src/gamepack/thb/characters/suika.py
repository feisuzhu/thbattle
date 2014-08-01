# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game
from .baseclasses import Character, register_character
from ..actions import DrawCards, GenericAction, MaxLifeChange
from ..cards import Card, Skill, TreatAs, SoberUp, AttackCard, IbukiGourdCard, WineCard, WeaponSkill, t_None


class Drunkard(TreatAs, Skill):
    skill_category = ('character', 'active')
    treat_as = WineCard

    def check(self):
        cl = self.associated_cards
        if not (cl and len(cl) == 1 and cl[0].color == Card.BLACK):
            return False
        if cl[0].resides_in.type not in ('cards', 'showncards', 'equips'):
            return False
        return True


class GreatLandscape(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class GreatLandscapeHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            src, card, dist = arg
            if card.is_card(AttackCard):
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
    skill_category = ('character', 'passive', 'awake')
    target = t_None


class WineDream(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class WineGodAwake(GenericAction):
    def apply_action(self):
        tgt = self.target
        tgt.skills.remove(WineGod)
        tgt.skills.append(WineDream)
        g = Game.getgame()
        g.process_action(MaxLifeChange(tgt, tgt, -1))
        return True


class WineGodHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'card_migration':
            act, cl, _from, to = arg

            if to.type != 'equips': return arg
            tgt = to.owner
            if not tgt.has_skill(WineGod): return arg

            if any(c.is_card(IbukiGourdCard) for c in cl):
                g = Game.getgame()
                g.process_action(WineGodAwake(tgt, tgt))

        return arg


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
        GreatLandscapeHandler,
        WineGodHandler,
        WineDreamHandler
    ]
    maxlife = 4
