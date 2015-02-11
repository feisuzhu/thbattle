import test
from test import CardSelector
from gamepack.thb.thb3v3 import THBattle
from gamepack.thb.characters.seiga import Seiga as Dummy
from gamepack.thb.characters.reisen import Reisen
from gamepack.thb.cards import AttackCard, HealCard
from game.autoenv import Game


class TestCase(test.TestCase):
    def setUp(self):
        self.create_game(THBattle, True)

        chars = [
            Reisen,
            Dummy,
            Dummy,
            Dummy,
            Dummy,
            Dummy,
        ]

        @self.wait
        def first(evt_type, data):
            if evt_type == 'game_roll_result':
                self.result = Game.getgame().players.index(data)
                return True

            return False

        self.players = (range(6) * 2)[first:first+6]

        for i, char in zip(THBattle.order_list, chars):
            self.choose_girl(self.players[i], char)

        for i in xrange(6):
            self.draw_cards(
                i,
                [CardSelector(AttackCard)] * (3 + (i != first))
            )

    def tearDown(self):
        self.kill_game()

    def test_lunatic(self):
        first, next = self.players[:2]

        self.draw_cards(first, [
            CardSelector(AttackCard),
            CardSelector(AttackCard)
        ])

        self.launch_card(first, selectors=[
            CardSelector(AttackCard)
        ], pids=[next])

        self.choose_option('Lunatic', True)

        self.draw_cards(next, [
            CardSelector(HealCard),
            CardSelector(AttackCard)
        ])

        self.assertFalse(self.can_launch_card(next, selectors=[
            CardSelector(HealCard)
        ]))

        self.assertFalse(self.can_launch_card(next, selectors=[
            CardSelector(AttackCard)
        ], pids=[next]))

        self.assertTrue(self.can_launch_card(next, selectors=[
            CardSelector(AttackCard)
        ], pids=[first]))

        # the second turn
        self.draw_cards(next, [
            CardSelector(HealCard),
            CardSelector(AttackCard)
        ])

        self.assertTrue(self.can_launch_card(next, selectors=[
            CardSelector(HealCard)
        ]))
