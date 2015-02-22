# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, DrawCards, DropCards, FatetellStage, GenericAction, PlayerTurn
from ..actions import ShowCards, UserAction, user_choose_cards
from ..cards import Card, Skill, SoberUp, VirtualCard, Wine, t_None
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class Ciguatera(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class CiguateraAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        tgt = self.target
        src = self.source
        g = Game.getgame()
        g.process_action(DropCards(src, self.cards))
        g.process_action(Wine(tgt, tgt))
        tags = tgt.tags
        tags['ciguatera_tag'] = g.turn_count
        tags['ciguatera_src'] = src

        return True


class CiguateraTurnEnd(GenericAction):
    card_usage = 'drop'

    def apply_action(self):
        src = self.source
        tgt = self.target
        g = Game.getgame()
        g.process_action(SoberUp(src, src))

        draw = DrawCards(tgt, amount=1)

        if draw.can_fire():
            cards = user_choose_cards(self, src, ('cards', 'showncards'))
        else:
            cards = None

        if cards:
            assert len(cards) == 1
            self.card = cards[0]
            g.process_action(DropCards(src, cards))
            g.process_action(draw)
        else:
            self.card = None
            g.process_action(Damage(None, src))

        return True

    def cond(self, cl):
        return len(cl) == 1

    def is_valid(self):
        return self.source.tags.get('wine', False)


class CiguateraHandler(EventHandler):
    interested = ('action_after', 'action_before')
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            g = Game.getgame()
            for p in g.players:
                if p.dead: continue
                if not p.has_skill(Ciguatera): continue

                cards = user_choose_cards(self, p, ('cards', 'showncards'))
                if cards:
                    g.process_action(CiguateraAction(p, act.target, cards))

        if evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            tags = tgt.tags
            g = Game.getgame()
            if tags.get('ciguatera_tag') == g.turn_count:
                src = tgt.tags['ciguatera_src']
                g.process_action(CiguateraTurnEnd(tgt, src))

        return act

    def cond(self, cl):
        if len(cl) != 1:
            return False

        return cl[0].resides_in.type in ('cards', 'showncards')


class Melancholy(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MelancholyPoison(VirtualCard):
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
            self.effective = True

        else:
            self.effective = False

        return True


class MelancholyHandler(EventHandler):
    interested = ('action_after', 'action_transform')
    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, Damage):
            act = arg
            tgt = act.target
            src = act.source

            if not src: return act
            if not tgt.has_skill(Melancholy): return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(MelancholyAction(tgt, src, amount=act.amount))

        elif evt_type == 'action_transform':
            if arg.usage not in ('use', 'launch'):
                return arg

            src = arg.actor
            g = Game.getgame()
            if src.tags.get('melancholy_tag') == g.turn_count:
                cards = VirtualCard.unwrap(arg.cards)
                zone = src.cards, src.showncards
                for c in cards:
                    if c.resides_in in zone:
                        arg.cards = [MelancholyPoison(arg.actor)]
                        return arg

        return arg


@register_character
class Medicine(Character):
    skills = [Ciguatera, Melancholy]
    eventhandlers_required = [CiguateraHandler, MelancholyHandler]
    maxlife = 3
