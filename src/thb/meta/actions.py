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
from thb.meta.common import ui_meta
from utils.misc import BatchList


# -- code --
@ui_meta(actions.DrawCards)
class DrawCards:
    def effect_string(self, act):
        if act.back:
            direction = u'从牌堆底'
        else:
            direction = u''

        return u'|G【%s】|r%s摸了%d张牌。' % (
            act.target.ui_meta.name, direction, act.amount,
        )


class PutBack:
    def effect_string(self, act):
        if act.direction == -1:
            direction = u'底'
        else:
            direction = u''

        return u'|G【%s】|r将%d张牌放回了牌堆%s。' % (
            act.target.ui_meta.name, len(act.cards), direction,
        )


@ui_meta(actions.ActiveDropCards)
class ActiveDropCards:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, 'OK，就这些了')
        else:
            return (False, '请弃掉%d张牌…' % act.dropn)

    def effect_string(self, act):
        if act.dropn > 0 and act.cards:
            return '|G【%s】|r弃掉了%d张牌：%s。' % (
                act.target.ui_meta.name, act.dropn, self.card_desc(act.cards),
            )


@ui_meta(actions.Damage)
class Damage:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(self, act):
        s, t = act.source, act.target
        if s:
            return '|G【%s】|r对|G【%s】|r造成了%d点伤害。' % (
                s.ui_meta.name, t.ui_meta.name, act.amount
            )
        else:
            return '|G【%s】|r受到了%d点无来源的伤害。' % (
                t.ui_meta.name, act.amount
            )

    def sound_effect(self, act):
        return 'thb-sound-hit'


@ui_meta(actions.LifeLost)
class LifeLost:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(self, act):
        return '|G【%s】|r流失了%d点体力。' % (
            act.target.ui_meta.name, act.amount
        )


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

        s = es or '|G【%s】|r对|G【%s】|r使用了|G%s|r。' % (
            s.ui_meta.name,
            '】|r、|G【'.join(tl.ui_meta.name),
            act.card.ui_meta.name
        )

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
        return '|G【%s】|r被击坠了。' % (
            tgt.ui_meta.name,
        )

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
        return '|G【%s】|r重新回到了场上。' % (
            tgt.ui_meta.name,
        )


@ui_meta(actions.TurnOverCard)
class TurnOverCard:
    def effect_string(self, act):
        tgt = act.target
        return '|G【%s】|r翻开了牌堆顶的一张牌，%s。' % (
            tgt.ui_meta.name,
            self.card_desc(act.card)
        )


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
            name = f'|G{ch.ui_meta.name}|r'
        except Exception:
            name = f'|R*[pid:{p.pid}]|r'

        role = g.ui_meta.roles[role.get().name],
        return f'{name}的身份是：|R{role}|r。'


@ui_meta(actions.Pindian)
class Pindian:
    # choose_card meta
    def choose_card_text(self, act, cards):
        if act.cond(cards):
            return (True, '不服来战！')
        else:
            return (False, '请选择一张牌用于拼点')

    def effect_string_before(self, act):
        return '|G【%s】|r对|G【%s】|r发起了拼点：' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(self, act):
        winner = act.source if act.succeeded else act.target
        return '|G【%s】|r是人生赢家！' % (
            winner.ui_meta.name
        )


@ui_meta(actions.ShowCards)
class ShowCards:
    def is_relevant_to_me(self, act):
        if self.me in act.to:
            return True


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
            prompt = '|G【%s】|r进行了一次判定（|G%s|r），结果为%s。' % (
                act.target.ui_meta.name,
                act_name,
                self.card_desc(act.card)
            )
        else:
            prompt = '|G【%s】|r进行了一次判定，结果为%s。' % (
                act.target.ui_meta.name,
                self.card_desc(act.card)
            )

        return prompt


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
    FATETELL = 7  # Play Fatetell animation, arg: CardSprite, no ret val.
    SHOW     = 8
    UNSHOW   = 9
    DECKAREA = 10
    DROPAREA = 11
    HANDAREA = 12


class MigrateInstructionType(IntEnum):
    OP   = 1
    CARD = 2
    PORTAREA = 3


MigrateInstruction = Tuple[MigrateInstructionType, Union[Tuple[MigrateOp], Tuple[int], Tuple[view.CardMetaView]]]

DUP: MigrateInstruction      = (MigrateInstructionType.OP, (MigrateOp.DUP,))
GET: MigrateInstruction      = (MigrateInstructionType.OP, (MigrateOp.GET,))
MOVE: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.MOVE,))
FADE: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.FADE,))
GRAY: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.GRAY,))
UNGRAY: MigrateInstruction   = (MigrateInstructionType.OP, (MigrateOp.UNGRAY,))
FATETELL: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.FATETELL,))
SHOW: MigrateInstruction     = (MigrateInstructionType.OP, (MigrateOp.SHOW,))
UNSHOW: MigrateInstruction   = (MigrateInstructionType.OP, (MigrateOp.UNSHOW,))
DECKAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.DECKAREA,))
DROPAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.DROPAREA,))
HANDAREA: MigrateInstruction = (MigrateInstructionType.OP, (MigrateOp.HANDAREA,))

CARD: Callable[[Card], MigrateInstruction] = lambda c: (MigrateInstructionType.CARD, (view.card(c),))


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

    return (MigrateInstructionType.PORTAREA, (t,))


@ui_meta(actions.MigrateCardsTransaction)
class MigrateCardsTransaction:

    def animation_instructions(self, trans: actions.MigrateCardsTransaction) -> List[MigrateInstruction]:
        me = self.me
        ops: List[MigrateInstruction] = []

        for m in trans.movements:
            # -- card actions --
            getops = [CARD(m.card), AREA(m.fr), GET]

            showing = (m.fr.type == 'showncards', m.to.type == 'showncards')

            if showing == (True, False):
                ops += getops + [DUP, UNSHOW]
            elif showing == (False, True):
                ops += getops + [DUP, SHOW]

            if m.to in (me.cards, me.showncards):
                ops += getops + [DUP, UNGRAY, AREA('hand'), MOVE]
            elif m.to.type == 'droppedcard':
                ops += getops + [DUP, GRAY, AREA('dropped'), MOVE]
            elif m.to.owner:
                ops += getops + [DUP, UNGRAY, DUP, FADE, AREA(m.to), MOVE]
            else:
                continue  # no animation

        return ops

    def detach_animation_instructions(self, trans: Optional[actions.MigrateCardsTransaction], cards: Sequence[Card]) -> List[MigrateInstruction]:
        ops: List[MigrateInstruction] = []

        for c in VirtualCard.unwrap(cards):
            fr = c.resides_in

            ops += [CARD(c), AREA(fr), GET]

            if fr.type == 'showncards':
                ops += [DUP, UNSHOW]

            if trans and isinstance(trans.action, actions.BaseFatetell):
                ops += [DUP, DUP, UNGRAY if trans.action.succeeded else GRAY, FATETELL, AREA('dropped'), MOVE]
            else:
                ops += [DUP, UNGRAY, AREA('dropped'), MOVE]

        return ops
