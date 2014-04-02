# -*- coding: utf-8 -*-
from ..actions import Damage, DrawCardStage, DrawCards, DropCards, FatetellStage, DropCardStage
from ..actions import UserAction, GenericAction, user_choose_cards, ShowCards
from ..cards import Wine, Skill, t_None, Card, SoberUp, VirtualCard
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


class Ciguatera(Skill):
    associated_action = None
    target = t_None


class CiguateraAction(UserAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        g.process_action(Wine(tgt, tgt))
        tags = tgt.tags
        tags['ciguatera_tag'] = g.turn_count
        tags['ciguatera_src'] = self.source

        return True


class CiguateraTurnEnd(GenericAction):
    card_usage = 'drop'

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()
        g.process_action(SoberUp(tgt, tgt))
        
        draw = DrawCards(src, amount=1)
        
        if draw.can_fire():
            cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        else:
            cards = None

        if cards:
            g.process_action(DropCards(tgt, cards))
            g.process_action(draw)
        else:
            g.process_action(Damage(None, tgt))

        return True

    def cond(self, cl):
        return len(cl) == 1

    def is_valid(self):
        return self.target.tags.get('wine', False)


class CiguateraHandler(EventHandler):
    card_usage = 'drop'
    execute_before = ('LunaClockHandler', )
    execute_after = ('TreasureHuntHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            g = Game.getgame()
            for p in g.players:
                if p.dead: continue
                if not p.has_skill(Ciguatera): continue

                cards = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
                if cards:
                    g.process_action(DropCards(p, cards))
                    g.process_action(CiguateraAction(p, act.target))

        if evt_type == 'action_after' and isinstance(act, DropCardStage):
            tgt = act.target
            tags = tgt.tags
            g = Game.getgame()
            if tags.get('ciguatera_tag') == g.turn_count:
                src = tgt.tags['ciguatera_src']
                g.process_action(CiguateraTurnEnd(src, tgt))

        return act

    def cond(self, cl):
        if len(cl) != 1:
            return False

        return cl[0].color == Card.BLACK


class Melancholy(Skill):
    associated_action = None
    target = t_None


class MelancholyAction(GenericAction):
    def __init__(self, source, target, amount):
        self.source = source
        self.target = target
        self.amount = amount

    def apply_action(self):
        src = self.source
        tgt = self.target
        draw = DrawCards(src, self.amount)
        g = Game.getgame()
        g.process_action(draw)
        g.process_action(ShowCards(src, draw.cards))
        if [c for c in draw.cards if c.suit != Card.CLUB]:  # any non-club
            tgt.tags['melancholy_tag'] = g.turn_count

        return True 


class MelancholyHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            tgt = act.target
            src = act.source

            if not src: return act
            if not tgt.has_skill(Melancholy): return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(MelancholyAction(tgt, src, amount=act.amount))

        elif evt_type == 'action_limit':
            arg, permitted = act
            if not permitted: return act
            if arg.usage not in ('use', 'launch'): return act

            src = arg.actor
            g = Game.getgame()
            if src.tags.get('melancholy_tag') == g.turn_count:
                cards = VirtualCard.unwrap(arg.cards)
                zone = src.cards, src.showncards
                return arg, all([c.resides_in not in zone for c in cards])

        return act

@register_character
class Medicine(Character):
    skills = [Ciguatera, Melancholy]
    eventhandlers_required = [CiguateraHandler, MelancholyHandler]
    maxlife = 3
