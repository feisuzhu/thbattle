# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import BaseFatetell, BaseFatetellResult, Fatetell, FatetellMalleateHandler
from thb.actions import FatetellResult, TurnOverCard, TurnOverCardResult
from thb.cards.equipment import YinYangOrbHandler
from thb.characters.shikieiki import TrialHandler
from thb.characters.shinmyoumaru import MiracleMalletHandler


# -- code --
class TestFatetellResult:

    def test_base_fatetell_result_hierarchy(self):
        assert issubclass(FatetellResult, BaseFatetellResult)
        assert issubclass(TurnOverCardResult, BaseFatetellResult)

    def test_result_cls_binding(self):
        assert Fatetell.result_cls is FatetellResult
        assert TurnOverCard.result_cls is TurnOverCardResult

    def test_fatetell_malleate_handler_interested(self):
        assert FatetellMalleateHandler.interested == ('action_before',)

    def test_yinyangorb_handler_interested(self):
        assert YinYangOrbHandler.interested == ('action_before',)

    def test_trial_handler_interested(self):
        assert TrialHandler.interested == ('action_before',)

    def test_miracle_mallet_handler_interested(self):
        assert MiracleMalletHandler.interested == ('action_before',)

    def test_trial_handler_arbiter(self):
        assert TrialHandler.arbiter is FatetellMalleateHandler

    def test_miracle_mallet_handler_arbiter(self):
        assert MiracleMalletHandler.arbiter is FatetellMalleateHandler
