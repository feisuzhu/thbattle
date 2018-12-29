# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from thb.actions import Damage, DrawCards, DropCards, GenericAction, LaunchCard, MaxLifeChange
from thb.actions import PlayerTurn, UserAction, migrate_cards, random_choose_card
from thb.cards.base import Skill
from thb.cards.classes import t_None, t_OtherOne
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler


# -- code --
class RiversideAction(UserAction):
    def apply_action(self):
        g = self.game
        src, tgt = self.source, self.target
        src.tags['riverside_tag'] = src.tags['turn_count']
        tgt.tags['riverside_target'] = g.turn_count
        minhp = min([p.life for p in g.players if not p.dead])
        if tgt.life == minhp:
            has_card = tgt.cards or tgt.showncards or tgt.equips
            if has_card and user_input([src], ChooseOptionInputlet(self, ('drop', 'draw'))) == 'drop':
                self.action = 'drop'
                catnames = ('cards', 'showncards', 'equips')
                card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
                card = card or random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
                g.players.reveal(card)
                g.process_action(DropCards(src, tgt, [card]))
            else:
                self.action = 'draw'
                g.process_action(DrawCards(src, 1))

        return True

    def is_valid(self):
        src = self.source
        # Fire with Exinwan -> dead -> skills cleared -> assertion fail
        # assert src.has_skill(Riverside)
        return not src.tags['riverside_tag'] >= src.tags['turn_count']


class RiversideHandler(THBEventHandler):
    interested = ['calcdistance']

    def handle(self, evt_type, arg):
        if evt_type == 'calcdistance':
            src, card, dist = arg
            if not src.has_skill(Riverside):
                return arg

            turn_count = self.game.turn_count
            for p in dist:
                if p.tags.get('riverside_target') == turn_count:
                    dist[p] -= 10000

        return arg


class Riverside(Skill):
    associated_action = RiversideAction
    skill_category = ['character', 'active']
    target = t_OtherOne
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if len(cl) != 1: return False
        return cl[0].resides_in.type in ('cards', 'showncards', 'equips')


class ReturningAwake(GenericAction):
    def apply_action(self):
        g = self.game
        tgt = self.target
        tgt.skills.remove(Returning)
        tgt.skills.append(FerryFee)
        g.process_action(MaxLifeChange(tgt, tgt, -1))

        return True


class ReturningHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Returning): return act
            g = self.game
            ncards = len(tgt.cards) + len(tgt.showncards)
            if tgt.life <= 2 and tgt.life < ncards:
                g.process_action(ReturningAwake(tgt, tgt))

        return act


class Returning(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'awake']
    target = t_None


class FerryFee(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
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


class FerryFeeHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            tgt = act.target
            if not (src and src.has_skill(FerryFee)): return act
            if not (tgt.cards or tgt.showncards or tgt.equips): return act
            dist = LaunchCard.calc_distance(src, FerryFee(src))
            if not dist.get(tgt, 10000) <= 0: return act
            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                g = self.game
                catnames = ('cards', 'showncards', 'equips')
                card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
                card = card or random_choose_card(g, [tgt.cards, tgt.showncards, tgt.equips])
                if not card: return act
                g = self.game
                g.process_action(FerryFeeEffect(src, tgt, card))

        return act


@register_character_to('common')
class Komachi(Character):
    skills = [Riverside, Returning]
    eventhandlers = [RiversideHandler, ReturningHandler, FerryFeeHandler]
    maxlife = 4
