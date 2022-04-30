# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import IntEnum
from typing import Any, Callable, List, Optional, Sequence, Tuple, Union
import random

# -- third party --
# -- own --
from thb import actions
from thb.cards.base import Card, CardList, VirtualCard
from thb.meta import view
from thb.meta.common import ui_meta, N
from utils.misc import BatchList


# -- code --
@ui_meta(actions.DrawCards)
class DrawCards:
    def effect_string(self, act):
        if act.back:
            direction = u'从牌堆底'
        else:
            direction = u''

        return f'{N.char(act.target)}{direction}摸了{act.amount}张牌。'


class PutBack:
    def effect_string(self, act):
        if act.direction == -1:
            direction = u'底'
        else:
            direction = u''

        return f'{N.char(act.target)}将{len(act.cards)}张牌放回了牌堆{direction}。'


@ui_meta(actions.ActiveDropCards)
class ActiveDropCards:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, 'OK，就这些了')
        else:
            return (False, f'请弃掉{act.dropn}张牌…')

    def effect_string(self, act):
        if act.dropn > 0 and act.cards:
            return f'{N.char(act.target)}弃掉了{act.dropn}张牌：{N.card(act.cards)}。'


@ui_meta(actions.Damage)
class Damage:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(self, act):
        s, t = act.source, act.target
        if s:
            return f'{N.char(s)}对{N.char(t)}造成了{act.amount}点伤害。'
        else:
            return f'{N.char(t)}受到了{act.amount}点无来源的伤害。'

    def sound_effect(self, act):
        return 'thb-sound-hit'


@ui_meta(actions.LifeLost)
class LifeLost:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(self, act):
        return f'{N.char(act.target)}流失了{act.amount}点体力。'


@ui_meta(actions.LaunchCard)
class LaunchCard:
    def effect_string_before(self, act: actions.LaunchCard) -> Optional[str]:
        s, tl = act.source, BatchList(act.target_list)
        c = act.card
        if not c:
            return None

        es = None

        meta = getattr(c, 'ui_meta', None)
        effect_string = getattr(meta, 'effect_string', None)
        if effect_string:
            es = effect_string(act)

        s = es or f'{N.char(s)}对{N.char(tl)}使用了{N.card(act.card)}。'

        return s

    def sound_effect_before(self, act):
        c = act.card
        if not c:
            return

        meta = getattr(c, 'ui_meta', None)
        se = getattr(meta, 'sound_effect', None)
        return se and se(act)

    def ray(self, act):
        if getattr(act.card.ui_meta, 'custom_ray', False):
            return []

        s = act.source
        return [(s, t) for t in act.target_list]

    def detach_cards_tip(self, trans: actions.MigrateCardsTransaction, cards: List[Card]) -> str:
        g = self.game
        act = trans.action
        assert isinstance(act, actions.LaunchCard)

        tl = set(act.target_list)
        tl2 = set([t for t in g.players if not t.dead])

        td = ''
        if tl == set([act.source]):
            td = '自己'
        elif tl == tl2:
            td = '全体'
        elif tl == tl2 - set([act.source]):
            td = '全体'
        else:
            td = N.char(act.target_list)

        return f'{N.char(act.source)}对{td}'

    def drop_cards_tip(self, trans: actions.MigrateCardsTransaction) -> str:
        return ''


@ui_meta(actions.AskForCard)
class AskForCard:
    def sound_effect_after(self, act):
        c = act.card
        if not c:
            return

        if act.card_usage != 'use':
            return

        meta = getattr(c, 'ui_meta', None)
        se = getattr(meta, 'sound_effect', None)
        return se and se(act)


@ui_meta(actions.PlayerDeath)
class PlayerDeath:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(self, act):
        tgt = act.target
        return f'{N.char(tgt)}被击坠了。'

    def sound_effect(self, act):
        meta = act.target.ui_meta
        se = getattr(meta, 'miss_sound_effect', None)
        if isinstance(se, (list, tuple)):
            return random.choice(se)
        else:
            return se


@ui_meta(actions.PlayerRevive)
class PlayerRevive:
    update_portrait = True

    def effect_string(self, act):
        tgt = act.target
        return f'{N.char(tgt)}重新回到了场上。'


@ui_meta(actions.TurnOverCard)
class TurnOverCard:
    def effect_string(self, act):
        tgt = act.target
        return f'{N.char(tgt)}翻开了牌堆顶的一张牌，{N.card(act.card)}。'


@ui_meta(actions.RevealRole)
class RevealRole:
    def effect_string(self, act: actions.RevealRole):
        g: Any = self.game
        me = self.me
        p = me.get_player()

        while True:
            if p is act.to:
                break
            if isinstance(act.to, list):
                if p in act.to:
                    break
            return

        p = act.player
        role = act.role

        try:
            ch = g.find_character(p)
            name = f'<style=Char.Name>{ch.ui_meta.name}</style>'
        except Exception:
            name = f'*[pid:{p.pid}]'

        role = g.ui_meta.roles[role.get().name]
        return f'{name}的身份是：<style=B>{role}</style>。'


@ui_meta(actions.Pindian)
class Pindian:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '不服来战！')
        else:
            return (False, '请选择一张牌用于拼点')

    def effect_string_before(self, act):
        return f'{N.char(act.source)}对{N.char(act.target)}发起了拼点：'

    def effect_string(self, act):
        winner = act.source if act.succeeded else act.target
        return f'{N.char(winner)}是人生赢家！'


@ui_meta(actions.ShowCards)
class ShowCards:
    def is_relevant_to_me(self, act):
        if self.me in act.to:
            return True


@ui_meta(actions.DropCards)
class DropCards:

    def drop_cards_tip(self, trans: actions.MigrateCardsTransaction) -> str:
        act = trans.action
        return f'{N.char(act.target)}弃置'


@ui_meta(actions.Reforge)
class Reforge:

    def drop_cards_tip(self, trans: actions.MigrateCardsTransaction) -> str:
        act = trans.action
        return f'{N.char(act.target)}重铸'


@ui_meta(actions.Fatetell)
class Fatetell:

    def fatetell_prompt_string(self, act):
        act_name = None

        try:
            card = act.initiator.associated_card
            act_name = card.ui_meta.name
        except AttributeError:
            pass

        try:
            act_name = act.initiator.ui_meta.fatetell_display_name
        except AttributeError:
            pass

        if act_name:
            prompt = f'{N.char(act.target)}进行了一次判定（{act_name}），结果为{N.card(act.card)}。'
        else:
            prompt = f'{N.char(act.target)}进行了一次判定，结果为{N.card(act.card)}。'

        return prompt

    def detach_cards_tip(self, trans: actions.MigrateCardsTransaction, cards: List[Card]) -> str:
        c = cards[0]
        return f'{N.char(trans.action.target)}判定（<style=Card.Name>{c.ui_meta.name}</style>）'

    def drop_cards_tip(self, trans: actions.MigrateCardsTransaction) -> str:
        return ''


@ui_meta(actions.ActionShootdown)
class ActionShootdown:
    target_independent = False
    shootdown_message = '您不能这样出牌'


@ui_meta(actions.BaseActionStage)
class BaseActionStage:
    idle_prompt = '请出牌…'

    def choose_card_text(self, act, cards):
        if not act.cond(cards):
            return False, '您选择的牌不符合出牌规则'
        else:
            return True, '不会显示'


@ui_meta(actions.VitalityLimitExceeded)
class VitalityLimitExceeded:
    target_independent = True
    shootdown_message = '你没有干劲了'


class MigrateOp(IntEnum):
    NOP      = 0
    DUP      = 1  # Duplicate top elem
    GET      = 2  # Get a CardSprite, find in hand/dropped area. Create if not found. args: Card, create_in return value: CardSprite.
    MOVE     = 3  # Move CardSprite to another Area. arg: CardSprite, Area, no return value.
    FADE     = 4  # Fade CardSprite, arg: CardSprite, no ret val.
    GRAY     = 5  # Set CardSprite gray, arg: CardSprite, no ret val.
    UNGRAY   = 6  # Unset CardSprite gray, arg: CardSprite, no ret val.
    FT_SUCC  = 7  # Play Fatetell animation, arg: CardSprite, no ret val.
    FT_FAIL  = 8  # Play Fatetell animation, arg: CardSprite, no ret val.
    SHOW     = 9
    UNSHOW   = 10
    DECKAREA = 11
    DROPAREA = 12
    HANDAREA = 13


class MigrateInstructionType(IntEnum):
    OP   = 1
    CARD = 2
    DESC = 3
    AREA = 4


MigrateInstruction = Tuple[MigrateInstructionType, Union[Tuple[MigrateOp], Tuple[int], Tuple[view.CardMetaView], Tuple[str]]]

DUP: MigrateInstruction      = (MigrateInstructionType.OP, (MigrateOp.DUP,))
GET: MigrateInstruction      = (MigrateInstructionType.OP, (MigrateOp.GET,))
MOVE: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.MOVE,))
FADE: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.FADE,))
GRAY: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.GRAY,))
UNGRAY: MigrateInstruction   = (MigrateInstructionType.OP, (MigrateOp.UNGRAY,))
FT_SUCC: MigrateInstruction  = (MigrateInstructionType.OP, (MigrateOp.FT_SUCC,))
FT_FAIL: MigrateInstruction  = (MigrateInstructionType.OP, (MigrateOp.FT_FAIL,))
SHOW: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.SHOW,))
UNSHOW: MigrateInstruction   = (MigrateInstructionType.OP, (MigrateOp.UNSHOW,))
DECKAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.DECKAREA,))
DROPAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.DROPAREA,))
HANDAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.HANDAREA,))

CARD: Callable[[Card], MigrateInstruction] = lambda c: (MigrateInstructionType.CARD, (view.card(c),))
DESC: Callable[[str], MigrateInstruction] = lambda s: (MigrateInstructionType.DESC, (s,))


def AREA(cl: Any) -> MigrateInstruction:
    t: int

    if isinstance(cl, CardList):
        if cl.type == 'deckcard':
            return DECKAREA
        elif cl.type == 'droppedcard':
            return DROPAREA
        elif cl.owner is None:
            return DECKAREA
        else:
            t = cl.owner.player.pid
    elif cl == 'dropped':
        return DROPAREA
    elif cl == 'hand':
        return HANDAREA
    else:
        raise Exception("WTF")

    return (MigrateInstructionType.AREA, (t,))


@ui_meta(actions.MigrateCardsTransaction)
class MigrateCardsTransaction:

    def get_tip(self, trans: actions.MigrateCardsTransaction, fn: str) -> str:
        if not (meta := getattr(trans.action, 'ui_meta', None)):
            return trans.action.__class__.__name__

        if f := getattr(meta, fn, None):
            return f(trans)
        else:
            return trans.action.__class__.__name__

    def animation_instructions(self, trans: actions.MigrateCardsTransaction) -> List[MigrateInstruction]:
        me = self.me
        ops: List[MigrateInstruction] = []

        tip = None

        for m in trans.movements:
            # -- card actions --
            cops = [CARD(m.card), AREA(m.fr), GET]

            if m.to.type == 'showncards':
                cops += [DUP, SHOW]
            else:
                cops += [DUP, UNSHOW]

            if m.to in (me.cards, me.showncards):
                cops += [DUP, UNGRAY, AREA('hand'), MOVE]
            elif m.to.type == 'droppedcard':
                if tip is None:
                    meta = getattr(trans.action, 'ui_meta', None)
                    if f := getattr(meta, 'drop_cards_tip', None):
                        tip = f(trans)
                    else:
                        tip = trans.action.__class__.__name__
                cops += [DUP, GRAY, DUP, DESC(tip), AREA('dropped'), MOVE]
            elif m.to.owner and m.to.type != 'special':
                cops += [DUP, UNGRAY, DUP, FADE, AREA(m.to), MOVE]
            else:
                continue  # no animation

            ops += cops

        return ops

    def detach_animation_instructions(self, trans: Optional[actions.MigrateCardsTransaction], cards: Sequence[Card]) -> List[MigrateInstruction]:
        ops: List[MigrateInstruction] = []

        tip = None
        if trans:
            meta = getattr(trans.action, 'ui_meta', None)
            if f := getattr(meta, 'detach_cards_tip', None):
                tip = f(trans, cards)
            else:
                tip = trans.action.__class__.__name__

        for c in VirtualCard.unwrap(cards):
            fr = c.resides_in

            ops += [CARD(c), AREA(fr), GET]

            if fr.type == 'showncards':
                ops += [DUP, UNSHOW]

            if trans:
                if isinstance(trans.action, actions.BaseFatetell):
                    ops += [DUP, FT_SUCC if trans.action.succeeded else FT_FAIL, DUP, DESC(tip), AREA('dropped'), MOVE]
                elif trans:
                    ops += [DUP, UNGRAY, DUP, DESC(tip), AREA('dropped'), MOVE]
            else:
                ops += [DUP, UNGRAY, AREA('dropped'), MOVE]

        return ops
