# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import Damage, DrawCards, DropCards, GenericAction, LaunchCard, MaxLifeChange, migrate_cards, PlayerTurn, random_choose_card, UserAction
from ..cards import Skill, t_None, t_OtherOne, Heal
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


class RiversideAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        tgt = self.target
        src.tags['riverside_tag'] = src.tags['turn_count']
        tgt.tags['riverside_target'] = True
        minhp = min([p.life for p in g.players if not p.dead])
        if tgt.life == minhp:
            has_card = tgt.cards or tgt.showncards or tgt.equips
            if has_card and user_input([src], ChooseOptionInputlet(self, ('drop', 'draw'))) == 'drop':
                self.action = 'drop'
                catnames = ('cards', 'showncards', 'equips')
                card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
                card = card or random_choose_card([tgt.cards, tgt.showncards, tgt.equips])
                g.players.reveal(card)
                g.process_action(DropCards(tgt, [card]))
            else:
                self.action = 'draw'
                g.process_action(DrawCards(src, 1))

        return True

    def is_valid(self):
        src = self.source
        # Fire with Exinwan -> dead -> skills cleared -> assertion fail
        # assert src.has_skill(Riverside)
        return not src.tags['riverside_tag'] >= src.tags['turn_count']


class RiversideHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            src, card, dist = arg
            if not src.has_skill(Riverside): return arg
            for p in dist:
                if p.tags['riverside_target']:
                    dist[p] -= 10000

        elif evt_type == 'action_after' and isinstance(arg, PlayerTurn):
            for p in Game.getgame().players:
                p.tags['riverside_target'] = False

        return arg


class Riverside(Skill):
    associated_action = RiversideAction
    target = t_OtherOne
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if len(cl) != 1: return False
        return cl[0].resides_in.type in ('cards', 'showncards', 'equips')


class ReturningAwake(GenericAction):
    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        tgt.skills.remove(Returning)
        tgt.skills.append(FerryFee)
        g.process_action(MaxLifeChange(tgt, tgt, -1))
        g.process_action(Heal(tgt, tgt, 1))

        return True


class ReturningHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Returning): return act
            g = Game.getgame()
            ncards = len(tgt.cards) + len(tgt.showncards)
            if tgt.life <= 2 and tgt.life < ncards:
                g.process_action(ReturningAwake(tgt, tgt))

        return act


class Returning(Skill):
    associated_action = None
    target = t_None


class FerryFee(Skill):
    associated_action = None
    target = t_None
    distance = 1


class FerryFeeEffect(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        src = self.source
        card = self.card
        src.reveal(card)
        migrate_cards([card], src.cards, unwrap=True)
        return True


class FerryFeeHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            tgt = act.target
            if not (src and src.has_skill(FerryFee)): return act
            if not (tgt.cards or tgt.showncards or tgt.equips): return act
            dist = LaunchCard.calc_distance(src, FerryFee(src))
            if not dist.get(tgt, 10000) <= 0: return act
            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                catnames = ('cards', 'showncards', 'equips')
                card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
                card = card or random_choose_card([tgt.cards, tgt.showncards, tgt.equips])
                if not card: return act
                g = Game.getgame()
                g.process_action(FerryFeeEffect(src, tgt, card))

        return act


@register_character
class Komachi(Character):
    skills = [Riverside, Returning]
    eventhandlers_required = [RiversideHandler, ReturningHandler, FerryFeeHandler]
    maxlife = 4
