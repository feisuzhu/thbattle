# -*- coding: utf-8 -*-
from game.autoenv import Game, EventHandler, user_input
from .baseclasses import Character, register_character
from ..actions import UserAction, GenericAction, FatetellStage, DropCards, DrawCardStage, ActionStage, DropCardStage
from ..actions import user_choose_cards, random_choose_card, migrate_cards, ask_for_action
from ..cards import Skill, t_None
from ..inputlets import ChooseIndividualCardInputlet, ChooseOptionInputlet, ChoosePeerCardInputlet


class Realm(Skill):
    associated_action = None
    skill_category = ('character', 'active')
    target = t_None


class RealmSkipFatetell(UserAction):
    def __init__(self, target, fts):
        self.source = self.target = target
        self.fts = fts

    def apply_action(self):
        self.fts.cancelled = True
        return True


class RealmSkipFatetellHandler(EventHandler):
    execute_after = ('CiguateraHandler', )
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act
            if not tgt.fatetell: return act

            cl = user_choose_cards(self, tgt, ['cards', 'showncards', 'equips'])
            if not cl: return act

            g = Game.getgame()
            g.process_action(DropCards(tgt, cl))
            g.process_action(RealmSkipFatetell(tgt, act))

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        t = self.target
        if cl[0].resides_in not in (t.cards, t.showncards):
            return False

        return True


class RealmSkipDrawCard(GenericAction):
    def __init__(self, target, dcs, pl):
        self.source = self.target = target
        self.dcs = dcs
        self.pl = pl

    def apply_action(self):
        self.dcs.cancelled = True
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
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled: return act
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act

            g = Game.getgame()

            pl = [p for p in g.players if not p.dead and (p.cards or p.showncards)]

            _, rst = ask_for_action(self, [tgt], ('cards', 'showncards', 'equips'), pl)
            if not rst: return act

            cl, pl = rst

            g = Game.getgame()
            g.process_action(DropCards(tgt, cl))
            g.process_action(RealmSkipDrawCard(tgt, act, pl))

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

        return (tl[:2], True)


class RealmSkipAction(UserAction):
    def __init__(self, target, act, pl):
        self.source = self.target = target
        self.act = act
        self.pl = pl

    def apply_action(self):
        self.act.cancelled = True
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
            to_equips = card.equipment_category not in cats
            to_equips = to_equips and user_input([tgt], ChooseOptionInputlet(self, (False, True)))
            migrate_cards([card], _to.equips if to_equips else _to.cards)
        else:
            assert False, 'WTF?!'

        return True


class RealmSkipActionHandler(EventHandler):
    execute_after = ('SealingArrayHandler', )
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            self.target = tgt = act.target
            if act.cancelled: return act
            if not tgt.has_skill(Realm): return act

            g = Game.getgame()

            pl = [p for p in g.players if not p.dead]

            _, rst = ask_for_action(self, [tgt], ('cards', 'showncards', 'equips'), pl)
            if not rst: return act
            cl, pl = rst
            if len(pl) != 2: return act

            g.process_action(DropCards(tgt, cl))
            g.process_action(RealmSkipAction(tgt, act, pl))

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

        tl = tl[:2]
        return (tl, bool(len(tl) == 2 and (tl[0].equips or tl[0].fatetell)))


class RealmSkipDropCard(UserAction):
    def __init__(self, target, fts):
        self.source = self.target = target
        self.fts = fts

    def apply_action(self):
        self.fts.cancelled = True
        return True


class RealmSkipDropCardHandler(EventHandler):
    execute_after = ('SuwakoHatHandler',)
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            if act.dropn < 1: return act
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act

            cl = user_choose_cards(self, tgt, ['cards', 'showncards', 'equips'])
            if not cl: return act

            g = Game.getgame()
            g.process_action(DropCards(tgt, cl))
            g.process_action(RealmSkipDropCard(tgt, act))

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
