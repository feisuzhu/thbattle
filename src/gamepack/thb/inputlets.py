# -*- coding: utf-8 -*-

# -- stdlib --
import logging
log = logging.getLogger('Inputlets')

# -- third party --
# -- own --
from game import Inputlet
from game.autoenv import Game
from utils import check, check_type, CheckFailed


# -- code --

class ChooseOptionInputlet(Inputlet):
    def init(self, options=(False, True)):
        self.options = options
        self.result = None

    def parse(self, data):
        if data not in self.options:
            return None

        return data

    def data(self):
        return self.result

    def set_option(self, value):
        'For UI'
        self.result = value


class ActionInputlet(Inputlet):
    def init(self, categories, candidates):
        self.categories = categories
        self.candidates = candidates

        self.skills = []
        self.cards = []
        self.players = []

    def parse(self, data):
        # data = [[skill_index1, ...], [card_syncid1, ...], [player_id1, ...]]
        actor = self.actor
        g = Game.getgame()
        categories = self.categories
        categories = [getattr(actor, i) for i in categories] if categories else None
        candidates = self.candidates

        skills = []
        cards = []
        players = []

        try:
            check_type([[int, Ellipsis]] * 3, data)

            sid_list, cid_list, pid_list = data

            if candidates:
                check(candidates)
                pl = [g.player_fromid(i) for i in pid_list]
                check(all([p in candidates for p in pl]))
                players = pl

            if categories:
                cards = g.deck.lookupcards(cid_list)
                check(len(cards) == len(cid_list))  # Invalid id

                cs = set(cards)
                check(len(cs) == len(cid_list))  # repeated ids

                if sid_list:
                    assert actor.cards in categories or actor.showncards in categories
                    check(all(cat.owner is actor for cat in categories))
                    check(all(c.resides_in.owner is actor for c in cards))  # Cards belong to actor?
                    for skill_id in sid_list:
                        check(isinstance(skill_id, int))
                        check(0 <= skill_id < len(actor.skills))
                    skills = [actor.skills[i] for i in sid_list]
                else:
                    check(all(c.resides_in in categories for c in cards))  # Cards in desired categories?

            return [skills, cards, players]

        except CheckFailed:
            return None

    def data(self):
        g = Game.getgame()
        actor_skills = self.actor.skills
        sid_list = [actor_skills.index(s) for s in self.skills]
        cid_list = [c.syncid for c in self.cards]
        pid_list = [g.get_playerid(p) for p in self.players]
        return [sid_list, cid_list, pid_list]

    def set_result(self, skills, cards, players):
        self.skills = skills
        self.cards = cards
        self.players = players


class ChooseIndividualCardInputlet(Inputlet):
    def init(self, cards):
        self.cards = cards
        self.selected = None

    def parse(self, data):
        try:
            cid = data
            check(isinstance(cid, int))
            cards = [c for c in self.cards if c.syncid == cid]
            check(len(cards))  # Invalid id
            return cards[0]

        except CheckFailed:
            return None

    def data(self):
        sel = self.selected
        return sel.syncid if sel else None

    def set_card(self, c):
        assert c in self.cards
        self.selected = c


class ChoosePeerCardInputlet(Inputlet):
    def init(self, target, categories):
        self.target = target
        self.categories = categories
        self.selected = None

    def parse(self, data):
        target = self.target
        categories = self.categories
        categories = [getattr(target, i) for i in categories]

        assert all(c.owner is target for c in categories)
        try:
            check(sum(len(c) for c in categories))  # no cards at all

            cid = data
            g = Game.getgame()

            check(isinstance(cid, int))

            cards = g.deck.lookupcards((cid,))

            check(len(cards) == 1)  # Invalid id
            card = cards[0]

            check(card.resides_in.owner is target)
            check(card.resides_in in categories)

            return card

        except CheckFailed:
            return None

    def data(self):
        sel = self.selected
        return sel.syncid if sel else None

    def set_card(self, c):
        assert c.resides_in.type in self.categories
        self.selected = c


class ProphetInputlet(Inputlet):
    '''For Ran'''
    def init(self, cards):
        self.cards = cards
        self.upcards = []
        self.downcards = []

    def parse(self, data):
        try:
            check_type([[int, Ellipsis]] * 2, data)
            upcards = data[0]
            downcards = data[1]
            check(sorted(upcards+downcards) == range(len(self.cards)))
        except CheckFailed:
            return [self.cards, []]

        cards = self.cards
        upcards = [cards[i] for i in upcards]
        downcards = [cards[i] for i in downcards]

        return [upcards, downcards]

    def data(self):
        cards = self.cards
        upcards = self.upcards
        downcards = self.downcards
        if not set(cards) == set(upcards + downcards):
            return [range(len(self.cards)), []]

        upcards = [cards.index(c) for c in upcards]
        downcards = [cards.index(c) for c in downcards]
        return [upcards, downcards]

    def set_result(self, upcards, downcards):
        cards = self.cards
        assert set(cards) == set(upcards + downcards)
        self.upcards = upcards
        self.downcards = downcards


class ChooseGirlInputlet(Inputlet):
    def init(self, mapping):
        # mapping = {
        #   Player1: [CharChoice1, ...],
        #   ...
        # }
        m = dict(mapping)
        from .common import CharChoice
        for k in m:
            assert all([isinstance(i, CharChoice) for i in m[k]])
            m[k] = m[k][:]

        self.mapping = m
        self.choice = None

    def parse(self, i):
        m = self.mapping
        actor = self.actor
        try:
            check(actor in m)
            check_type(int, i)
            check(0 <= i < len(m[actor]))
            choice = m[actor][i]
            check(not choice.chosen)
            return choice
        except CheckFailed:
            return None

    def data(self):
        if self.choice is None:
            return None

        try:
            return self.mapping[self.actor].index(self.choice)
        except:
            log.error('WTF?!', exc_info=1)
            return None

    def set_choice(self, choice):
        assert choice in self.mapping[self.actor]
        self.choice = choice


class KOFSortInputlet(Inputlet):
    def init(self, mapping):
        # mapping = {
        #     A: [ list of CharChoices ],
        #     B: [ list of CharChoices ],
        # }
        s = set([len(l) for l in mapping.values()])
        assert(len(s) == 1)
        self.num = s.pop()
        self.mapping = mapping
        self.result = None

    def parse(self, data):
        n = self.num
        try:
            check(data)
            check_type([int] * n, data)
            check(set(data) == set(range(n)))
            return data

        except CheckFailed:
            return range(n)

    def data(self):
        assert set(self.result) == set(range(self.num))
        return self.result

    def set_result(self, result):
        assert set(result) == set(range(self.num))
        self.result = result
