# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import IntEnum
from typing import List, Optional, Sequence, TYPE_CHECKING, Union
import random

# -- third party --
from typing_extensions import Literal, TypedDict

# -- own --
from thb import actions
from thb.meta.common import ui_meta
from utils.misc import BatchList
from thb.mode import THBAction

# -- typing --
if TYPE_CHECKING:
    from thb.cards.base import Card, CardList  # noqa: F401


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
    def effect_string(self, act):
        g = self.game
        me = self.me
        if not (me in act.to if isinstance(act.to, list) else me is act.to):
            return

        tgt = act.target
        i = tgt.identity
        try:
            name = '|G%s|r' % tgt.ui_meta.name
        except Exception:
            name = '|R%s|r' % tgt.account.username

        return '%s的身份是：|R%s|r。' % (
            name,
            g.ui_meta.identity_table[i.type],
        )


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


class MigrateCardsAnimationOp(IntEnum):
    PUSH       = 0  # Push next as-is
    DUP        = 1  # Duplicate top elem
    GET        = 2  # Get a CardSprite, find in hand/dropped area. Create if not found. args: Card, create_in return value: CardSprite.
    MOVE       = 3  # Move CardSprite to another Area. arg: CardSprite, Area, no return value.
    FADE       = 4  # Fade CardSprite, arg: CardSprite, no ret val.
    GRAY       = 5  # Set CardSprite gray, arg: CardSprite, no ret val.
    UNGRAY     = 6  # Unset CardSprite gray, arg: CardSprite, no ret val.
    FATETELL   = 7  # Play Fatetell animation, arg: CardSprite, no ret val.
    SHOW       = 8
    UNSHOW     = 9
    AREA_HAND  = 10
    AREA_DECK  = 11
    AREA_DROP  = 12
    AREA_PORT0 = 13
    AREA_PORT1 = 14
    AREA_PORT2 = 15
    AREA_PORT3 = 16
    AREA_PORT4 = 17
    AREA_PORT5 = 18
    AREA_PORT6 = 19
    AREA_PORT7 = 20
    AREA_PORT8 = 21
    AREA_PORT9 = 22


class CardView(TypedDict):
    type: Literal['card']
    card: str
    suit: int
    number: int
    sync_id: int


@ui_meta(actions.MigrateCardsTransaction)
class MigrateCardsTransaction:

    # def dbgprint(self, ins):
    #     rst: Any = []
    #     for i in ins:
    #         if isinstance(i, int):
    #             rst.append(Op(i))
    #         else:
    #             rst.append(repr(i))

    #     from UnityEngine import Debug
    #     Debug.Log(repr(rst))

    def cl2index(self, cl: CardList) -> int:
        g = self.game
        assert cl.owner
        for i, p in enumerate(g.players):
            if p.player == cl.owner.player:
                return i
        else:
            raise ValueError

    def view(self, c: Card) -> CardView:
        return {
            'type': 'card',
            'card': c.__class__.__name__,
            'suit': c.suit,
            'number': c.number,
            'sync_id': c.sync_id,
        }

    def animation_instructions(self, trans: actions.MigrateCardsTransaction) -> List[Union[MigrateCardsAnimationOp, CardView]]:
        Op = MigrateCardsAnimationOp

        me = self.me
        ops: List[Union[MigrateCardsAnimationOp, CardView]] = []

        # class CardMovement:
        #     trans: MigrateCardsTransaction
        #     card: Card
        #     fr: CardList
        #     to: CardList
        #     direction: Literal['front', 'back'] = 'front'

        for m in trans.movements:
            # -- card actions --
            c = self.view(m.card)
            tail: List[Union[MigrateCardsAnimationOp, CardView]] = []

            if m.fr.type in ('deckcard', 'droppedcard') or not m.fr.owner:
                tail += [c, Op.AREA_DECK, Op.GET]
            elif m.fr in (me.cards, me.showncards):
                tail += [c, Op.AREA_HAND, Op.GET]
            else:
                tail += [c, Op(Op.AREA_PORT0 + self.cl2index(m.fr)), Op.GET]

            showing = (m.fr.type == 'showncards', m.to.type == 'showncards')

            if showing == (True, False):
                tail += [Op.DUP, Op.UNSHOW]
            elif showing == (False, True):
                tail += [Op.DUP, Op.SHOW]

            if m.to in (me.cards, me.showncards):
                tail += [Op.DUP, Op.UNGRAY, Op.AREA_HAND, Op.MOVE]
            else:
                if m.to.type in ('droppedcard', 'deckcard'):
                    gray = m.to.type == 'droppedcard'
                    tail += [Op.DUP, Op.GRAY if gray else Op.UNGRAY, Op.AREA_DROP, Op.MOVE]

                elif m.to.owner:
                    tail += [Op.DUP, Op.UNGRAY, Op.DUP, Op.FADE, Op(Op.AREA_PORT0 + self.cl2index(m.to)), Op.MOVE]
                else:
                    continue  # no animation

            ops += tail

        return ops

    def detach_animation_instructions(self, trans: MigrateCardsTransaction, cards: Sequence[Card]) -> List[Union[MigrateCardsAnimationOp, CardView]]:
        Op = MigrateCardsAnimationOp

        me = self.me
        ops: List[Union[MigrateCardsAnimationOp, CardView]] = []

        for c in cards:
            cv = self.view(c)
            fr = c.resides_in

            if fr.type in ('deckcard', 'droppedcard') or not fr.owner:
                ops += [cv, Op.AREA_DECK, Op.GET]
            elif fr in (me.cards, me.showncards):
                ops += [cv, Op.AREA_HAND, Op.GET]
            else:
                ops += [cv, Op(Op.AREA_PORT0 + self.cl2index(fr)), Op.GET]

            if fr.type == 'showncards':
                ops += [Op.DUP, Op.UNSHOW]

            act = trans.action
            if isinstance(act, actions.BaseFatetell):
                ops += [Op.DUP, Op.DUP, Op.UNGRAY if act.succeeded else Op.GRAY, Op.FATETELL, Op.AREA_DROP, Op.MOVE]
            else:
                ops += [Op.DUP, Op.UNGRAY, Op.AREA_DROP, Op.MOVE]

        return ops
