# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, user_input
from gamepack.thb.actions import ActionStage, ActionStageLaunchCard, DrawCards, DropCardStage
from gamepack.thb.actions import FinalizeStage, GenericAction, LaunchCard, PlayerTurn, UserAction
from gamepack.thb.actions import ask_for_action
from gamepack.thb.cards import AttackCard, Card, PhysicalCard, Skill, VirtualCard, t_None, t_Self
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class WindWalkLaunch(ActionStageLaunchCard):
    pass


class WindWalkSkipAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        ActionStage.force_break()
        turn = PlayerTurn.get_current(tgt)
        try:
            turn.pending_stages.remove(DropCardStage)
            turn.pending_stages.remove(FinalizeStage)
        except Exception:
            pass

        return True


class WindWalkAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target

        while True:
            dc = DrawCards(tgt, 1)
            g.process_action(dc)
            c, = dc.cards
            self.card = c

            with InputTransaction('ActionStageAction', [tgt]) as trans:
                p, rst = ask_for_action(
                    self, [tgt], ('cards', 'showncards'), g.players, trans
                )

            if p is not tgt:
                g.process_action(WindWalkSkipAction(tgt, tgt))
                break

            cl, tl = rst
            g.players.reveal(cl)
            c, = cl

            g.process_action(WindWalkLaunch(p, tl, c))

        return True

    @staticmethod
    def is_windwalk_card(c):
        return all([
            c.is_card(AttackCard) or 'instant_spellcard' in c.category,
            'group_effect' not in c.category,
        ])

    def cond(self, cl):
        if not (cl and len(cl) == 1):
            return False

        return bool(cl[0].associated_action) and [self.card] == VirtualCard.unwrap(cl)

    def ask_for_action_verify(self, p, cl, tl):
        assert len(cl) == 1
        return WindWalkLaunch(p, tl, cl[0]).can_fire()

    def choose_player_target(self, tl):
        return tl, True


class WindWalk(Skill):
    associated_action = WindWalkAction
    skill_category = ('character', 'active')
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
    skill_category = ('character', 'passive')
    target = t_None


class DominanceHandler(EventHandler):
    interested = ('action_after', 'action_apply')

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            t = act.target.tags
            t['dominance_suits']        = set()
            t['dominance_suit_SPADE']   = False
            t['dominance_suit_CLUB']    = False
            t['dominance_suit_HEART']   = False
            t['dominance_suit_DIAMOND'] = False

        elif evt_type == 'action_apply' and isinstance(act, LaunchCard):
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

            if len(tgt.tags['dominance_suits']) != 4:
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(PlayerTurn(tgt))

        return act


@register_character
class SpAya(Character):
    skills = [WindWalk, Dominance]
    eventhandlers_required = [DominanceHandler]
    maxlife = 4
