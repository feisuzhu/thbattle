# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, user_input
from gamepack.thb.actions import ActionStageLaunchCard, DrawCards, DropCards, GenericAction
from gamepack.thb.actions import UserAction, ask_for_action, random_choose_card, user_choose_cards
from gamepack.thb.cards import AttackCard, Skill, VirtualCard, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class WindWalk(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class WindWalkLaunch(GenericAction):
    card_usage = 'launch'

    def __init__(self, target, card):
        self.target = target
        self.card = card

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target

        with InputTransaction('ActionStageAction', [tgt]) as trans:
            p, rst = ask_for_action(
                self, [tgt], ('cards', 'showncards'), g.players, trans
            )

        if p is not tgt:
            return False

        cl, tl = rst
        g.players.reveal(cl)
        c, = cl

        g.process_action(ActionStageLaunchCard(tgt, tl, c))

        return True

    def cond(self, cl):
        if not (cl and len(cl) == 1): return False
        return bool(cl[0].associated_action) and [self.card] == VirtualCard.unwrap(cl)

    def ask_for_action_verify(self, p, cl, tl):
        assert len(cl) == 1
        return ActionStageLaunchCard(p, tl, cl[0]).can_fire()

    def choose_player_target(self, tl):
        return tl, True


class WindWalkDropCards(DropCards):
    pass


class WindWalkAction(UserAction):

    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        dc = DrawCards(tgt, 1)
        g.process_action(dc)
        c, = dc.cards

        if not g.process_action(WindWalkLaunch(tgt, c)):
            c, = user_choose_cards(self, tgt, ('cards', 'showncards')) or (None,)
            c = c or random_choose_card([tgt.cards, tgt.showncards])
            g.process_action(WindWalkDropCards(tgt, tgt, [c]))

        return True

    def cond(self, cl):
        tgt = self.target
        return len(cl) == 1 and cl[0].resides_in in (tgt.cards, tgt.showncards)


class WindWalkHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):

        if evt_type == 'action_after' and isinstance(act, ActionStageLaunchCard):
            src = act.source

            if not src.has_skill(WindWalk):
                return act

            c = act.card

            if not c.is_card(AttackCard) and 'instant_spellcard' not in c.category:
                return act

            if 'group_effect' in c.category:
                return act

            if not act.card_action.succeeded:
                return act

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
