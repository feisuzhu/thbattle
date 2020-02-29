# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import Damage, GenericAction, UserAction, migrate_cards
from thb.cards import Attack, Skill
from thb.cards import t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class Unconsciousness(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class UnconsciousnessAction(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source, self.target = act.source, act.target

    def apply_action(self):
        self.action.amount += 1 - 2 * bool(len(self.target.cards) + len(self.target.showncards))
        return True


class UnconsciousnessHandler(EventHandler):
    interested = ('action_before',) # active char > weapon > passive char > protection > game-state (wine)
    execute_before = (
        'RepentanceStickHandler',
        'DeathSickleHandler',
        'DevotedHandler',
        'FourOfAKindHandler',
        'UmbrellaHandler',
        'WineHandler',
        )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):

            g = Game.getgame()
            src = act.source
            if not src or not src.has_skill(Unconsciousness): return act
            tgt = act.target
            tgt.dead or g.process_action(UnconsciousnessAction(act))

        return act


class Paranoia(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ParanoiaAction(UserAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        if not (tgt.cards or tgt.showncards): return False

        c = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards', 'showncards')))
        if not c: return False
        src.reveal(c)
        migrate_cards([c], src.cards)

        return True


class ParanoiaHandler(EventHandler):
    interested = ('action_after',)
    execute_before = ( # 2 weapon and 6 passive char
        'AyaRoundfanHandler',
        'NenshaPhoneHandler',
        'DilemmaHandler',
        'DecayDamageHandler',
        'EchoHandler',
        'MelancholyHandler',
        'MajestyHandler',
        'MasochistHandler',
    )

    execute_after = (
        'IbukiGourdHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):

            if act.amount: return act

            g = Game.getgame()

            src, tgt = act.source, act.target
            if not src or not src.has_skill(Paranoia) or tgt.dead: return act
            if not (tgt.cards or tgt.showncards): return act

            pact = g.action_stack[-1]
            if isinstance(pact, Attack) and g.current_player is src:
                src.tags['vitality'] += 1

            if user_input([src], ChooseOptionInputlet(self, (False, True))): 
                g.process_action(ParanoiaAction(src, tgt))

        return act


@register_character_to('common')
class Koishi(Character):
    skills = [Unconsciousness, Paranoia]
    eventhandlers_required = [UnconsciousnessHandler, ParanoiaHandler]
    maxlife = 4
