# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
# -- own --
from game.base import GameItem
from thb.characters.baseclasses import Character
from utils import exceptions


# -- code --
@GameItem.register
class ImperialChoice(GameItem):
    key = 'imperial-choice'
    args = [str]

    def __init__(self, char):
        if char == 'Akari' or char not in Character.character_classes:
            raise exceptions.CharacterNotFound

        self.char_cls = Character.character_classes[char]

    @property
    def title(self):
        return u'选将卡（%s）' % self.char_cls.ui_meta.char_name

    @property
    def description(self):
        return u'你可以选择%s出场。2v2模式不可用。' % self.char_cls.ui_meta.char_name

    def should_usable_in_game(self, uid, mgr):
        g = mgr.game
        from thb.thb2v2 import THBattle2v2
        if isinstance(g, THBattle2v2):
            raise exceptions.IncorrectGameMode

        for l in mgr.game_items.values():
            if self.char_cls.__name__ in l:
                raise exceptions.ChooseCharacterConflict

    @classmethod
    def get_chosen(cls, items, pl):
        chosen = []
        for p in pl:
            uid = p.account.userid
            if uid not in items:
                continue

            for i in items[uid]:
                i = GameItem.from_sku(i)
                if not isinstance(i, cls):
                    continue

                chosen.append((p, i.char_cls))
                break

        return chosen


@GameItem.register
class IdentityChooser(GameItem):
    key = 'id-chooser'
    args = [str]

    def __init__(self, id):
        if id not in ('attacker', 'accomplice', 'curtain', 'boss'):
            raise exceptions.InvalidIdentity

        self.id = id
        mapping = {
            'attacker':   u'城管',
            'boss':       u'BOSS',
            'accomplice': u'道中',
            'curtain':    u'黑幕',
        }
        self.disp_name = mapping[id]

    @property
    def title(self):
        return u'身份卡（%s）' % self.disp_name

    @property
    def description(self):
        return u'你可以选择%s身份。身份场可用。' % self.disp_name

    def should_usable_in_game(self, uid, mgr):
        g = mgr.game
        from thb.thbidentity import THBattleIdentity
        if not isinstance(g, THBattleIdentity):
            raise exceptions.IncorrectGameMode

        threshold = {
            'attacker': 4,
            'boss': 1,
            'accomplice': 2,
            'curtain': 1,
        }
        if mgr.game_params['double_curtain']:
            threshold['curtain'] += 1
            threshold['attacker'] -= 1

        threshold[self.id] -= 1

        for l in mgr.game_items.values():
            for i in l:
                i = GameItem.from_sku(i)
                if not isinstance(i, self.__class__):
                    continue

                if i.id not in threshold:  # should not happen
                    raise exceptions.WTF_InvalidIdentity

                threshold[i.id] -= 1

        if any(i < 0 for i in threshold.values()):
            # 谢谢辣条～
            raise exceptions.ChooseIdentityConflict


@GameItem.register
class European(GameItem):
    key = 'european'
    args = []

    title = u'欧洲卡'
    description = u'Roll点保证第一。身份场、抢书不可用。'

    def should_usable_in_game(self, uid, mgr):
        from thb.thbbook import THBattleBook
        from thb.thbidentity import THBIdentity
        if isinstance(mgr.game, (THBattleBook, THBIdentity)):
            raise exceptions.IncorrectGameMode

        for l in mgr.game_items.values():
            if self.key in l:
                raise exceptions.EuropeanConflict

    @classmethod
    def is_european(cls, g, items, p):
        uid = p.account.userid
        return uid in items and cls.key in items[uid]
