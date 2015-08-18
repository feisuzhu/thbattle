# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DrawCards, DropCardStage, DropCards, GenericAction
from gamepack.thb.actions import UserAction, random_choose_card, user_choose_players
from gamepack.thb.cards import Skill, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class AutumnWindEffect(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target

        g = Game.getgame()

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        card = card or random_choose_card(cats)
        if not card:
            return False

        self.card = card
        g.players.exclude(tgt).reveal(card)
        g.process_action(DropCards(src, tgt, cards=[card]))
        return True

    def is_valid(self):
        tgt = self.target
        catnames = ('cards', 'showncards', 'equips')
        return not tgt.dead and any(getattr(tgt, i) for i in catnames)


class AutumnWindAction(UserAction):
    def __init__(self, source, target_list):
        self.source = source
        self.target = None
        self.target_list = target_list

    def apply_action(self):
        g = Game.getgame()
        src = self.source

        for p in self.target_list:
            g.process_action(AutumnWindEffect(src, p))

        return True


class AutumnWindHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DropCardStage):
            self.n = n = act.dropn
            if n <= 0:
                return act

            tgt = act.target
            if not tgt.has_skill(AutumnWind):
                return act

            g = Game.getgame()
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            candidates = [
                p for p in g.players if
                p is not tgt and
                (p.cards or p.showncards or p.equips) and
                not p.dead
            ]

            pl = candidates and user_choose_players(self, tgt, candidates)
            if not pl:
                return act

            g.process_action(AutumnWindAction(tgt, pl))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[:self.n], True)


class AutumnWind(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class DecayDrawCards(DrawCards):
    pass


class DecayDrawCardHandler(EventHandler):
    interested = ('post_card_migration',)
    execute_after = ('PostCardMigrationHandler',)

    def handle(self, evt_type, arg):
        if evt_type != 'post_card_migration':
            return arg

        g = Game.getgame()
        me = getattr(g, 'current_player', None)
        if me is None: return arg
        if me.dead: return arg
        if not me.has_skill(Decay): return arg

        trans = arg

        candidates = {p for p in g.players if not p.dead and not (p.cards or p.showncards)}
        involved = {
            _from.owner for cards, _from, to, is_bh in trans.get_movements()
            if _from is not None and _from.type in ('cards', 'showncards')
        }

        trigger = candidates & involved

        if not trigger: return arg
        if me in involved: return arg

        g.process_action(DecayDrawCards(me, 1))
        import time
        import pprint
        pprint.pprint(g.hybrid_stack)
        pprint.pprint([
            i for i in trans.get_movements()
            if i[1] is not None and i[1].type in ('cards', 'showncards')
        ])
        time.sleep(1)

        return arg


class DecayAction(UserAction):
    def apply_action(self):
        tgt = self.target
        tgt.tags['shizuha_decay'] = True
        return True


class DecayEffect(UserAction):
    def __init__(self, source, target, dcs):
        self.source = source
        self.target = target
        self.dcs = dcs

    def apply_action(self):
        self.dcs.dropn += max(1, self.dcs.dropn + 1)
        return True


class DecayDamageHandler(EventHandler):
    interested = ('action_after', 'action_before')
    execute_after = ('SuwakoHatHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (tgt and tgt.has_skill(Decay)):
                return act

            g = Game.getgame()
            if g.current_player is tgt: return act
            if not g.current_player: return act
            g.process_action(DecayAction(src, g.current_player))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            t = tgt.tags
            if not t['shizuha_decay']: return act

            t['shizuha_decay'] = False
            g = Game.getgame()
            g.process_action(DecayEffect(tgt, tgt, act))

        return act


class Decay(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


@register_character
class Shizuha(Character):
    skills = [Decay, AutumnWind]
    eventhandlers_required = [DecayDamageHandler, DecayDrawCardHandler, AutumnWindHandler]
    maxlife = 3
