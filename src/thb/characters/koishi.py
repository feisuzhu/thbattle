# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import ActionShootdown, Damage, GenericAction, PlayerDeath, PlayerTurn, UserAction, migrate_cards
from thb.cards import Attack, LaunchCard, Skill, UseCard, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class Unconsciousness(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class UnconsciousnessAction(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source, self.target = act.source, act.target

    def apply_action(self):
        if self.action.amount > 0:
            self.action.amount += -1
        return True


class UnconsciousDamageHandler(EventHandler):
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
            tgt = act.target

            p = getattr(g, 'current_player', None)
            if not p or not p.has_skill(Unconsciousness): return act

            if not src or not src.has_skill(Unconsciousness): return act

            len(tgt.cards) + len(tgt.showncards) < tgt.life or tgt.dead or g.process_action(UnconsciousnessAction(act))

        return act


class UnconsciousnessLimit(ActionShootdown):
    pass


class UnconsciousSilenceHandler(EventHandler):
    interested = ('action_shootdown',)

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown' and isinstance(act, (LaunchCard, UseCard)):
            src = act.source
            tgt = act.target

            if not src or src.has_skill(Unconsciousness): return act
            if not tgt or tgt.dead: return act

            g = Game.getgame()
            p = getattr(g, 'current_player', None)

            if not p or not p.has_skill(Unconsciousness): return act

            if len(src.cards) + len(src.showncards) < src.life: return act

            def walk(c):
                if not c.is_card(VirtualCard):
                    return [c]

                if c.usage not in ('launch', 'use'):
                    return []

                cards = c.associated_cards
                return walk(cards[0]) if len(cards) == 1 else cards

            cards = walk(act.card)

            zone = src.cards, src.showncards, src.equips, src.fatetell, src.special
            for c in cards:
                if c.resides_in in zone:
                    raise UnconsciousnessLimit

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
    execute_before = (
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

            g = Game.getgame()

            src, tgt = act.source, act.target
            if not src or not src.has_skill(Paranoia): return act

            pact = g.action_stack[-1]
            if isinstance(pact, Attack) and g.current_player is src:
                if not src.tags['vitality']:
                    src.tags['vitality'] += 1

                if tgt.dead: return act

                tgt.tags['paranoia'] = True
                for s in tgt.skills:
                    if 'character' in s.skill_category:
                        tgt.disable_skill(s, 'paranoia')

            if act.amount: return act
            if not (tgt.cards or tgt.showncards) or tgt.dead: return act

            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                g.process_action(ParanoiaAction(src, tgt))

        return act


class ParanoiaFadeHandler(EventHandler):
    interested = ('action_after', 'action_apply')

    def handle(self, evt_type, arg):
        if ((evt_type == 'action_after' and isinstance(arg, PlayerTurn)) or
            (evt_type == 'action_apply' and isinstance(arg, PlayerDeath) and arg.target.has_skill(Paranoia))):  # noqa

            g = Game.getgame()
            for p in g.players:
                if p.tags.pop('paranoia', ''):
                    p.reenable_skill('paranoia')

        return arg


@register_character_to('common')
class Koishi(Character):
    skills = [Unconsciousness, Paranoia]
    eventhandlers_required = [UnconsciousDamageHandler, UnconsciousSilenceHandler, ParanoiaHandler, ParanoiaFadeHandler]
    maxlife = 4
