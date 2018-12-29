# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import user_input
from game.base import ActionShootdown, InputTransaction
from thb.actions import ActionStage, ActionStageLaunchCard, DrawCards, DropCardStage, FinalizeStage
from thb.actions import GenericAction, LaunchCard, PlayerTurn, ShowCards, UserAction, ask_for_action
from thb.cards.base import Card, Skill, VirtualCard
from thb.cards.classes import PhysicalCard, t_None, t_Self
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class WindWalkLaunch(ActionStageLaunchCard):
    pass


class WindWalkSkipAction(GenericAction):
    def apply_action(self) -> bool:
        g = self.game
        ActionStage.force_break(g)
        turn = PlayerTurn.get_current(g)
        try:
            turn.pending_stages.remove(DropCardStage)
            turn.pending_stages.remove(FinalizeStage)
        except Exception:
            pass

        return True


class WindWalkAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        g = self.game
        tgt = self.target

        while True:
            dc = DrawCards(tgt, 1)
            g.process_action(dc)
            c, = dc.cards
            self.card = c
            g.process_action(ShowCards(tgt, [c]))

            with InputTransaction('ActionStageAction', [tgt]) as trans:
                p, rst = ask_for_action(
                    self, [tgt], ('cards', 'showncards'), g.players, trans=trans
                )

            if p is not tgt:
                g.process_action(WindWalkSkipAction(tgt, tgt))
                break

            assert p
            assert rst

            cl, tl = rst
            g.players.reveal(cl)
            c, = cl

            g.process_action(WindWalkLaunch(p, tl, c))

        return True

    def cond(self, cl):
        if not (cl and len(cl) == 1):
            return False

        return bool(cl[0].associated_action) and [self.card] == VirtualCard.unwrap(cl)

    def ask_for_action_verify(self, p, cl, tl):
        assert len(cl) == 1
        return WindWalkLaunch(p, tl, cl[0]).can_fire()

    def choose_player_target(self, tl):
        return tl, True


class WindWalkTargetLimit(ActionShootdown):
    pass


class WindWalkHandler(THBEventHandler):
    interested = ['action_apply', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, LaunchCard):
            src = act.source
            if act.card.is_card(WindWalk):
                return act

            if not src.has_skill(WindWalk):
                return act

            src.tags['windwalk_last_targets'] = set(act.target_list)

        elif evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            src = act.source
            if not src.has_skill(WindWalk):
                return act

            src.tags['windwalk_last_targets'] = set()

        elif evt_type == 'action_shootdown' and isinstance(act, LaunchCard):
            g = self.game
            if not isinstance(g.action_stack[-1], WindWalkAction):
                return act

            src, tl = act.source, set(act.target_list)
            last_tl = src.tags['windwalk_last_targets'] or set()

            if not tl <= last_tl:
                raise WindWalkTargetLimit

            return act

        return act


class WindWalk(Skill):
    associated_action = WindWalkAction
    skill_category = ['character', 'active']
    target = t_Self
    usage = 'drop'

    def check(self):
        cl = self.associated_cards
        if not(cl and len(cl) == 1):
            return False

        if cl[0].is_card(Skill):
            return False

        return True


class Dominance(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class DominanceAction(PlayerTurn):
    pass


class DominanceHandler(THBEventHandler):
    interested = ['action_after', 'action_apply']

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            t = act.target.tags
            t['dominance_suits']        = set()
            t['dominance_suit_SPADE']   = False
            t['dominance_suit_CLUB']    = False
            t['dominance_suit_HEART']   = False
            t['dominance_suit_DIAMOND'] = False

        elif evt_type == 'action_apply' and isinstance(act, LaunchCard):
            if not act.source.has_skill(Dominance):
                return act

            card = act.card
            if not card.is_card(PhysicalCard):
                return act

            suit = card.suit
            if suit not in (Card.SPADE, Card.CLUB, Card.HEART, Card.DIAMOND):
                return act

            try:
                t = act.source.tags
                t['dominance_suits'].add(suit)
                t['dominance_suit_%s' % Card.SUIT_REV[suit]] = True

            except AttributeError:
                pass

        elif evt_type == 'action_after' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Dominance):
                return act

            if len(tgt.tags['dominance_suits'] or set()) != 4:
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            self.game.process_action(DominanceAction(tgt))

        return act


@register_character_to('imperial')
class SpAya(Character):
    skills = [WindWalk, Dominance]
    eventhandlers = [WindWalkHandler, DominanceHandler]
    maxlife = 4
