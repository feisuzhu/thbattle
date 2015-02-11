from gevent.event import Event
from gevent.greenlet import GreenletExit
from utils import BatchList, check, CheckFailed
from gamepack.thb.actions import BaseDrawCards, ActionStageLaunchCard, skill_wrap, handle_action_transform, skill_check
from gamepack.thb.cards import VirtualCard
from game.autoenv import Game
import gevent
import unittest
# import gevent


def event_handler(h):
    def wrapper(self, *a, **k):
        h(self, *a, **k)
        self.fill_evt.set()
        self.empty_evt.wait()
        self.empty_evt.clear()
        return self.result

    return wrapper


class Test(object):
    KEEP = 2
    REFILL = 3
    SYNC = 4
    SYNC_NEXT = 5
    result = None
    sync_tag = None
    step = 0

    def __init__(self):
        self.sync_cnt = 0
        self.handlers = []
        self.empty_evt = Event()
        self.fill_evt = Event()
        self.games = BatchList()
        self.greenlet = gevent.getcurrent()

    def sync(self, tag):
        if self.sync_cnt == 0:
            import traceback
            self.sync_stack = traceback.format_stack()
            self.sync_tag = tag
            self.sync_evt = event = Event()
        else:
            if tag != self.sync_tag:
                print ''.join(self.sync_stack)
                assert False
            assert tag == self.sync_tag
            event = self.sync_evt

        self.sync_cnt += 1

        if self.sync_cnt >= len(self.games):
            self.sync_cnt = 0
            event.set()
        else:
            event.wait()

    def handler(self, h):
        self.handlers.append(h)

    def input_handler(self, h):
        @self.handler
        def handle(evt_type, data):
            if evt_type != 'user_input':
                return False

            p, trans, ilet = data
            return h(p, trans, ilet)

    def handle_user_input(self, p, trans, ilet):
        self.handle_event('user_input', (p, trans, ilet))

    def handle_event(self, evt_type, act):
        need_fill = True
        while need_fill:
            need_fill = False

            if not self.handlers:
                self.fill_handlers()

            for h in self.handlers:
                rst = h(evt_type, act)
                if rst:
                    if rst & Test.SYNC:
                        if rst == Test.SYNC:
                            rst = Test.REFILL

                        self.sync('E' + str(h))

                        if Game.SERVER_SIDE:
                            self.handlers.remove(h)

                        self.sync('e' + str(h))

                    elif rst != Test.KEEP:
                        self.handlers.remove(h)

                    if rst == Test.REFILL:
                        need_fill = True

                    break

        if not self.handlers:
            self.fill_handlers()

        return act

    @event_handler
    def batch(self, f):
        @self.handler
        def b(evt_type, data):
            self.result = f()
            return Test.SYNC

    def create_game(self, gamecls, clients=False, **params):
        ngames = 1 + clients * gamecls.n_persons
        self.killed = False

        def report(g):
            gevent.kill(self.greenlet, g.exception)

        # is Group better?
        self.games = games = BatchList()
        for i in xrange(ngames):
            g = gamecls()
            g.pid = i - 1
            g.test = self
            g.params = params
            g.link_exception(report)
            games.append(g)

        games.start()
        self.empty_evt.wait()
        self.empty_evt.clear()

    def kill_game(self):
        self.killed = True
        for g in self.games:
            try:
                g.kill()
            except Exception:
                pass
        self.games.kill()
        self.games = BatchList()
        self.sync_cnt = 0

    def put_sync(self, tag, data):
        self.sync_data = data
        self.sync('S'+str(tag))
        self.sync('s'+str(tag))

    def get_sync(self, tag):
        self.sync('S'+str(tag))
        data = self.sync_data
        self.sync('s'+str(tag))
        return data

    def fill_handlers(self):
        if self.killed:
            raise GreenletExit

        self.empty_evt.set()
        self.fill_evt.wait()
        self.fill_evt.clear()

    @event_handler
    def draw_cards(self, pid, cards):
        @self.handler
        def draw(evt_type, act):
            if evt_type != 'action_apply' or not isinstance(act, BaseDrawCards):
                return False

            g = Game.getgame()
            if g.get_playerid(act.target) != pid:
                return False

            assert len(cards) == act.amount

            # FIXME: may be wrong if cards not enough
            cl = g.deck.getcards(act.amount)

            self.sync('DRAW')
            if g.CLIENT_SIDE:
                return Test.SYNC_NEXT

            for i, c in enumerate(cards):
                dc = cl[i]
                if c.cls:
                    dc.__class__ = c.cls

                if c.kind is not None:
                    dc.kind = c.kind

                if c.number is not None:
                    dc.number = c.number

            return Test.SYNC_NEXT

    @event_handler
    def wait(self, cond):
        @self.handler
        def wait(evt_type, data):
            return cond(evt_type, data) and Test.SYNC_NEXT

    def select_player_cards(self, p, selectors):
        cards = []
        for s in selectors:
            cl = []
            for r in s.regions:
                cl.extend(getattr(p, r))

            cards.append(s.apply([c for c in cl if c not in cards]))

        assert None not in cards
        return cards

    @event_handler
    def try_launch_card(self, pid, skills=[], selectors=[], pids=[], params={}):
        @self.input_handler
        def handle(p, trans, ilet):
            g = Game.getgame()
            if g.get_playerid(p) != pid:
                return False

            if trans.name != 'ActionStageAction':
                return False

            cards = self.select_player_cards(p, selectors)
            players = [g.players[px] for px in pids]
            ilet.set_result(skills, cards, players, params)
            data = ilet.data()
            rst = ilet.parse(data)
            initiator = ilet.initiator

            def post_process(actor, rst):
                g = Game.getgame()
                usage = getattr(initiator, 'card_usage', 'none')
                try:
                    check(rst)
                    skills, rawcards, players, params = rst
                    [check(not c.detached) for c in rawcards]
                    [check(actor.has_skill(s)) for s in skills]  # has_skill may be hooked

                    if skills:
                        cards = [skill_wrap(actor, skills, rawcards, params)]
                        usage = cards[0].usage if usage == 'launch' else usage
                    else:
                        cards = rawcards
                        usage = 'launch'

                    cards, players = handle_action_transform(g, actor, ilet, cards, usage, players)

                    if ilet.categories:
                        if len(cards) == 1 and cards[0].is_card(VirtualCard):
                            check(skill_check(cards[0]))

                        check(initiator.cond(cards))
                        assert not (usage == 'none' and rawcards)  # should not pass check
                    else:
                        cards = []

                    if ilet.candidates:
                        players, valid = initiator.choose_player_target(players)
                        check(valid)

                    return cards, players, params

                except CheckFailed:
                    return None

            rst = ilet.post_process(p, rst, no_reveal=True)
            if rst is not None:
                (card,), target_list, _ = rst
                self.result = ActionStageLaunchCard(p, target_list, card).can_fire()
                if self.result:
                    return True

            ilet.set_result([], [], [])
            self.result = False
            return Test.REFILL

    @event_handler
    def can_launch_card(self, pid, skills=[], selectors=[], pids=[], params={}):
        @self.input_handler
        def handle(p, trans, ilet):
            g = Game.getgame()
            if g.get_playerid(p) != pid:
                return False

            if trans.name != 'ActionStageAction':
                return False

            cards = self.select_player_cards(p, selectors)
            players = [g.players[px] for px in pids]
            ilet.set_result(skills, cards, players, params)
            data = ilet.data()
            rst = ilet.parse(data)
            rst = ilet.post_process(p, rst, no_reveal=True)
            if rst is not None:
                (card,), target_list, _ = rst
                self.result = ActionStageLaunchCard(p, target_list, card).can_fire()
            else:
                self.result = False

            ilet.set_result([], [], [])
            return Test.REFILL

    @event_handler
    def choose_girl(self, pid, char_cls):
        @self.input_handler
        def choose(p, trans, ilet):
            g = Game.getgame()
            if g.get_playerid(p) != pid:
                return False

            if trans.name != 'ChooseGirl':
                return False

            assert len(self.handlers) == 2

            cl = ilet.mapping[ilet.actor]
            for i, c in enumerate(cl):
                if not c.chosen:
                    ilet.set_choice(c)
                    return True

            assert False

        @self.handler
        def handle(evt_type, data):
            if evt_type != 'user_input_finish':
                return False

            trans, ilet, rst = data
            if trans.name != 'ChooseGirl':
                return False

            self.sync('CG')
            assert len(self.handlers) == 1

            rst.char_cls = char_cls
            return Test.SYNC_NEXT

    @event_handler
    def choose_option(self, pattern, option, pid=None):
        @self.input_handler
        def choose(p, trans, ilet):
            if pid is not None:
                g = Game.getgame()
                if g.get_playerid(p) != pid:
                    return False

            if trans.name != 'ChooseOption':
                return False

            if not ilet.initiator.__class__.__name__.startswith(pattern):
                return False

            ilet.set_option(option)
            return True


class TestCase(unittest.TestCase, Test):
    def __init__(self, *a, **k):
        unittest.TestCase.__init__(self, *a, **k)
        Test.__init__(self)

    def launch_card(self, *a, **k):
        self.assertTrue(self.try_launch_card(*a, **k))


class CardSelector(object):
    def __init__(self, cls=None, kind=None, number=None, regions=('cards', )):
        self.cls = cls
        self.kind = kind
        self.number = number
        self.regions = regions

    def apply(self, cl):
        for c in cl:
            if self.match(c):
                return c

    def match(self, card):
        if self.kind:
            if card.kind != self.kind:
                return False

        if self.number:
            if card.number != self.number:
                return False

        if not self.cls:
            return True

        return card.is_card(self.cls)
