# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import Damage, DrawCards, ForEach, LaunchCard, LaunchFatetellCard
from thb.actions import UserAction, ttags
from thb.cards import AttackCard, Reject, Skill, SpellCardAction, TreatAs, VirtualCard
from thb.cards import t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class Tianyi(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class TianyiAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class TianyiAction(UserAction):
    def __init__(self, source, action):
        self.source = self.target = source
        self.action = action

    def apply_action(self):
        src, lc = self.source, self.action
        assert isinstance(lc, (LaunchCard, LaunchFatetellCard))
        lc.card_action.cancelled = True
        ttags(src)['mima_tianyi'] = True

        if isinstance(lc, LaunchCard):
            # HACK! RejectCard has no target, but not implemented this way.
            if lc.force_action and isinstance(lc.force_action, Reject):
                return True

            lst = lc.target_list[:]

        elif isinstance(lc, LaunchFatetellCard):
            lst = [lc.target]

        else:
            assert False, 'WTF?!'

        g = Game.getgame()
        for p in lst:
            g.process_action(LaunchCard(src, [p], TianyiAttack(src), bypass_check=True))

        return True


class TianyiHandler(EventHandler):
    interested = ('action_before',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and hasattr(act, 'associated_card'):
            g = Game.getgame()
            lc = g.action_stack[-1]

            for lc in reversed(g.action_stack):
                if isinstance(lc, (LaunchCard, LaunchFatetellCard)) and lc.card_action is act:
                    break
            else:
                return act

            me = g.current_player
            if not me or not me.has_skill(Tianyi):
                return act

            while True:
                if isinstance(act, SpellCardAction): break
                if isinstance(act, ForEach) and issubclass(act.action_cls, SpellCardAction): break  # Another HACK
                return act

            if ttags(me)['mima_tianyi']:
                return act

            if not user_input([me], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(TianyiAction(me, lc))

        return act


class Eling(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ElingDrawCards(DrawCards):
    pass


class ElingHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            g = Game.getgame()
            if g.current_player is not act.target:
                return act

            for p in g.players:
                if p.dead: continue
                if not p.has_skill(Eling): continue
                g.process_action(ElingDrawCards(p, 2))

        return act


@register_character_to('1week')
class Mima20150705(Character):
    skills = [Tianyi, Eling]
    eventhandlers_required = [TianyiHandler, ElingHandler]
    maxlife = 4
