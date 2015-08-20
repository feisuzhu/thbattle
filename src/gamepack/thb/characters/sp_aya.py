# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, user_input
from gamepack.thb.actions import ActionStage, ActionStageLaunchCard, DrawCards, DropCardStage
from gamepack.thb.actions import GenericAction, PlayerTurn, UserAction, ask_for_action, ttags
from gamepack.thb.cards import AttackCard, Skill, VirtualCard, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class WindWalk(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class WindWalkLaunch(ActionStageLaunchCard):
    pass


class WindWalkSkipAction(GenericAction):
    def apply_action(self):
        tgt = self.target
        ActionStage.force_break()
        turn = PlayerTurn.get_current(tgt)
        try:
            turn.pending_stages.remove(DropCardStage)
        except Exception:
            pass

        return True


class WindWalkAction(UserAction):
    card_usage = 'launch'

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        dc = DrawCards(tgt, 1)
        g.process_action(dc)
        c, = dc.cards
        self.card = c

        ttags(tgt)['aya_windwalk'] = True

        with InputTransaction('ActionStageAction', [tgt]) as trans:
            p, rst = ask_for_action(
                self, [tgt], ('cards', 'showncards'), g.players, trans
            )

        if p is not tgt:
            g.process_action(WindWalkSkipAction(tgt, tgt))
            return True

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
        if not (cl and len(cl) == 1): return False
        return bool(cl[0].associated_action) and [self.card] == VirtualCard.unwrap(cl)

    def ask_for_action_verify(self, p, cl, tl):
        assert len(cl) == 1
        return WindWalkLaunch(p, tl, cl[0]).can_fire()

    def choose_player_target(self, tl):
        return tl, True


class WindWalkHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):

        if evt_type == 'action_after' and isinstance(act, ActionStageLaunchCard):
            src = act.source

            if not src.has_skill(WindWalk):
                return act

            c = act.card

            if not all([
                WindWalkAction.is_windwalk_card(c),
                act.card_action.succeeded,
                isinstance(act, WindWalkLaunch) or not ttags(src)['aya_windwalk'],
            ]): return act

            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            g = Game.getgame()
            g.process_action(WindWalkAction(src, src))

        return act


@register_character
class SpAya(Character):
    skills = [WindWalk]
    eventhandlers_required = [WindWalkHandler]
    maxlife = 4
