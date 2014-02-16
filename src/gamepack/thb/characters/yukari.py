# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, GenericAction, FatetellStage, DropCards, DrawCardStage, LaunchCard, ActionStage, DropCardStage, ActiveDropCards
from ..actions import user_choose_cards, random_choose_card, migrate_cards, user_input_action
from ..cards import Skill, t_None
from ..inputlets import ChooseIndividualCardInputlet, ChooseOptionInputlet, ChoosePeerCardInputlet


class Realm(Skill):
    associated_action = None
    target = t_None


class RealmAction(UserAction):
    def __init__(self, target, stage, pl):
        self.source = self.target = target
        self.stage = stage
        self.cards = cards
        self.pl = pl

    def apply_action(self):
        g = Game.getgame()
        g.process_action(ActiveDropCards(self.target, self.cards))
        self.stage.cancelled = True
        return True

    def is_valid(self):
        return ActiveDropCards(self.target, self.cards).can_fire()

def user_input_realm_action(self, act, stage, tgt, candidates=[]):
    action = lambda p, cl, pl: act(tgt, cl, stage, pl)
    return user_input_action(self, action, [tgt], ['cards', 'showncards'], candidates)

class RealmSkipFatetell(RealmAction):
    def apply_action(self):
        RealmAction.apply_action(self)
        tgt = self.target
        if not tgt.fatetell: return True
        card = user_input([tgt], ChooseIndividualCardInputlet(self, tgt.fatetell))
        card and Game.getgame().process_action(DropCards(tgt, [card]))
        return True


class RealmSkipFatetellHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act
            if not tgt.fatetell: return act

            action = user_input_realm_action(self, RealmSkipFatetell, act, tgt)
            
            if action:
                Game.getgame().process_action(action)

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards):
            return False

        return True


class RealmSkipDrawCard(RealmAction):
    def apply_action(self):
        RealmAction.apply_action(self)
        tgt = self.target

        for p in self.pl:
            c = user_input([tgt], ChoosePeerCardInputlet(self, p, ('cards', 'showncards')))
            c = c or random_choose_card([p.cards, p.showncards])
            if not c: continue
            tgt.reveal(c)
            migrate_cards([c], tgt.cards)

        return True


class RealmSkipDrawCardHandler(EventHandler):
    execute_after = ('FrozenFrogHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act

            g = Game.getgame()

            pl = [p for p in g.players if not p.dead and (p.cards or p.showncards)]

            action = user_input_realm_action(self, RealmSkipDrawCard, act, tgt, pl)

            if action:
                g.process_action(action)

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards):
            return False

        return True

    def choose_player_target(self, tl):
        try:
            tl.remove(self.target)
        except:
            pass

        if not tl:
            return (tl, False)

        return (tl[:2], True)


class RealmSkipAction(RealmAction):
    def apply_action(self):
        RealmAction.apply_action(self)
        _from, _to = self.pl
        tgt = self.target
        from itertools import chain
        allcards = list(chain.from_iterable([_from.equips, _from.fatetell]))

        if not allcards:
            # Dropped by Exinwan
            return False

        card = user_input([tgt], ChooseIndividualCardInputlet(self, allcards))
        if not card:
            card = random_choose_card([_from.equips, _from.fatetell])

        if card.resides_in is _from.fatetell:
            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                migrate_cards([card], _to.fatetell)
            else:
                migrate_cards([card], _to.cards, unwrap=True)

        elif card.resides_in is _from.equips:
            cats = set([c.equipment_category for c in _to.equips])
            migrate_cards([card], _to.cards)
            if card.equipment_category not in cats:
                if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                    Game.getgame().process_action(
                        LaunchCard(_to, [_to], card)
                    )
        else:
            assert False, 'WTF?!'

        return True


class RealmSkipActionHandler(EventHandler):
    execute_after = ('SealingArrayHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            self.target = tgt = act.target
            if act.cancelled: return act
            if not tgt.has_skill(Realm): return act

            g = Game.getgame()

            pl = [p for p in g.players if not p.dead]

            action = user_input_realm_action(self, RealmSkipAction, act, tgt, pl)

            if action:
                g.process_action(action)

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards):
            return False

        return True

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[:2], bool(len(tl) == 2 and (tl[0].equips or tl[0].fatetell)))


class RealmSkipDropCard(RealmAction):
    pass

class RealmSkipDropCardHandler(EventHandler):
    execute_after = ('SuwakoHatHandler',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            if act.dropn < 1: return act
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act

            action = user_input_realm_action(self, RealmSkipDropCard, act, tgt)
            
            if action:
                Game.getgame().process_action(action)

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards):
            return False

        return True


@register_character
class Yukari(Character):
    skills = [Realm]
    eventhandlers_required = [
        RealmSkipFatetellHandler,
        RealmSkipDrawCardHandler,
        RealmSkipActionHandler,
        RealmSkipDropCardHandler,
    ]
    maxlife = 4
