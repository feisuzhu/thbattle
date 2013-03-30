# -*- coding: utf-8 -*-
from baseclasses import *
from ..actions import *
from ..cards import *

class Realm(Skill):
    associated_action = None
    target = t_None


class RealmSkipFatetell(UserAction):
    def __init__(self, target, fts):
        self.source = self.target = target
        self.fts = fts

    def apply_action(self):
        self.fts.cancelled = True
        tgt = self.target
        if not tgt.fatetell: return True
        card = choose_individual_card(tgt, tgt.fatetell)
        if card:
            Game.getgame().process_action(DropCards(tgt, [card]))
        return True


class RealmSkipFatetellHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, FatetellStage):
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act
            if not tgt.fatetell: return act

            cats = [
                tgt.cards, tgt.showncards, tgt.equips
            ]
            cl = user_choose_cards(self, tgt, cats)
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

        g = Game.getgame()

        for p in self.pl:
            c = random_choose_card([p.cards, p.showncards])
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
            cats = [
                tgt.cards, tgt.showncards, tgt.equips
            ]
            g = Game.getgame()

            pl = [p for p in g.players if not p.dead and (p.cards or p.showncards)]

            rst = user_choose_cards_and_players(self, tgt, cats, pl)
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

        card = choose_individual_card(tgt, allcards)
        if not card:
            card = random_choose_card([_from.equips, _from.fatetell])

        if card.resides_in is _from.fatetell:
            if user_choose_option(self, tgt):
                migrate_cards([card], _to.fatetell)
            else:
                migrate_cards([card], _to.cards, unwrap=True)

        elif card.resides_in is _from.equips:
            cats = set([c.equipment_category for c in _to.equips])
            migrate_cards([card], _to.cards)
            if card.equipment_category not in cats:
                if user_choose_option(self, tgt):
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

            cats = [
                tgt.cards, tgt.showncards, tgt.equips
            ]
            g = Game.getgame()

            pl = [p for p in g.players if not p.dead]

            rst = user_choose_cards_and_players(self, tgt, cats, pl)
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

        return (tl[:2], bool(len(tl) == 2 and (tl[0].equips or tl[0].fatetell)))


class RealmSkipDropCard(UserAction):
    def __init__(self, target, fts):
        self.source = self.target = target
        self.fts = fts

    def apply_action(self):
        self.fts.cancelled = True
        return True


class RealmSkipDropCardHandler(EventHandler):
    execute_after = ('SuwakoHatHandler',)
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            if act.dropn < 1: return act
            self.target = tgt = act.target
            if not tgt.has_skill(Realm): return act

            cats = [
                tgt.cards, tgt.showncards, tgt.equips
            ]
            cl = user_choose_cards(self, tgt, cats)
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
