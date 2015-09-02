# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import Damage, LaunchCard, UserAction, ttags
from ..actions import migrate_cards, user_choose_players, DropCards
from ..cards import AttackCard, Skill, t_None, Attack, VirtualCard, TreatAs
from ..inputlets import ChoosePeerCardInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class Echo(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class EchoDropCards(DropCards):
    pass


class EchoAction(UserAction):
    def __init__(self, source, target, card):
        self.source, self.target, self.card = source, target, card

    def apply_action(self):
        src, tgt, card = self.source, self.target, self.card
        src.reveal(card)
        migrate_cards([card], src.cards)

        g = Game.getgame()
        pl = [p for p in g.players
              if p.cards or p.showncards or p.equips or p.fatetell]

        pl = pl and user_choose_players(self, tgt, pl)
        if pl:
            catnames = ['cards', 'showncards', 'equips', 'fatetell']
            card = user_input([tgt], ChoosePeerCardInputlet(self, pl[0], catnames))
            if card:
                g.players.reveal(card)
                g.process_action(EchoDropCards(tgt, pl[0], [card]))

        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class EchoHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if tgt.dead:
                return act

            if not src or not src.has_skill(Echo):
                return act

            if ttags(src)['kyouko_echo']:
                return act

            g = Game.getgame()
            if g.current_turn is not src:
                return act

            dists = LaunchCard.calc_raw_distance(tgt, AttackCard())
            pl = [p for p, d in dists.items()
                  if d <= 1 and (p.cards or p.showncards or p.equips)]
            pl = pl and user_choose_players(self, src, pl)
            if not pl:
                return act

            catnames = ['cards', 'showncards', 'equips']
            card = user_input([src], ChoosePeerCardInputlet(self, pl[0], catnames))
            if not card:
                return act

            ttags(src)['kyouko_echo'] = True
            g.process_action(EchoAction(tgt, pl[0], card))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Resonance(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ResonanceAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class ResonanceHandler(EventHandler):
    __name__ = 'ResonanceBHandler'
    interested = ('action_done',)

    def handle(self, evt_type, act):
        if evt_type == 'action_done' and isinstance(act, Attack):
            if act.done and act.succeeded:
                return act

            src = act.source
            tgt = act.target

            if not src or not src.has_skill(Resonance):
                return act

            dists = LaunchCard.calc_raw_distance(src, Resonance(src))
            dists = {p: max(d, 1) for p, d in dists.items()}
            dist = dists[tgt] - 1

            if dists[tgt] <= 0:
                return act

            pl = [p for p, d in dists.items() if d == dist and p is not src]
            pl = pl and user_choose_players(self, src, pl)

            if not pl:
                return act

            g = Game.getgame()
            g.process_action(LaunchCard(src, pl, ResonanceAttack(src)))

        return act

    def ask_for_action_verify(self, p, cl, tl):
        return LaunchCard(p, tl, ResonanceAttack(p)).can_fire()

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


@register_character
class KyoukoB(Character):
    skills = [Echo, Resonance]
    eventhandlers_required = [EchoHandler, ResonanceHandler]
    maxlife = 4

EchoHandler.__name__ = 'EchoBHandler'
ResonanceHandler.__name__ = 'ResonanceBHandler'
