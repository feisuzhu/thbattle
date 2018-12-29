# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Optional
import random

# -- third party --
# -- own --
from thb import actions
from thb.meta.common import G, card_desc, ui_meta
from utils.misc import BatchList


# -- code --
@ui_meta(actions.DrawCards)
class DrawCards:
    def effect_string(self, act):
        return '|G【%s】|r摸了%d张牌。' % (
            act.target.ui_meta.name, act.amount,
        )


@ui_meta(actions.ActiveDropCards)
class ActiveDropCards:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, 'OK，就这些了')
        else:
            return (False, '请弃掉%d张牌…' % act.dropn)

    def effect_string(self, act):
        if act.dropn > 0 and act.cards:
            return '|G【%s】|r弃掉了%d张牌：%s' % (
                act.target.ui_meta.name, act.dropn, card_desc(act.cards),
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

        meta = getattr(c, 'ui_meta', None)
        effect_string = getattr(meta, 'effect_string', None)
        if effect_string:
            return effect_string(act)

        return '|G【%s】|r对|G【%s】|r使用了|G%s|r。' % (
            s.ui_meta.name,
            '】|r、|G【'.join(tl.ui_meta.name),
            act.card.ui_meta.name
        )

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
        return '|G【%s】|r翻开了牌堆顶的一张牌，%s' % (
            tgt.ui_meta.name,
            card_desc(act.card)
        )


@ui_meta(actions.RevealRole)
class RevealRole:
    def effect_string(self, act):
        g = G()
        me = g.me
        if not (me in act.to if isinstance(act.to, list) else me is act.to):
            return

        tgt = act.target
        i = tgt.identity
        try:
            name = '|G%s|r' % tgt.ui_meta.name
        except Exception:
            name = '|R%s|r' % tgt.account.username

        return '%s的身份是：|R%s|r' % (
            name,
            G().ui_meta.identity_table[i.type],
        )


@ui_meta(actions.Pindian)
class Pindian:
    # choose_card meta
    def choose_card_text(self, g, act, cards):
        if act.cond(cards):
            return (True, '不服来战！')
        else:
            return (False, '请选择一张牌用于拼点')

    def effect_string_before(self, act):
        return '|G【%s】|r对|G【%s】|r发起了拼点' % (
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
        from thb.meta.common import card_desc

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
                card_desc(act.card)
            )
        else:
            prompt = '|G【%s】|r进行了一次判定，结果为%s。' % (
                act.target.ui_meta.name,
                card_desc(act.card)
            )

        return prompt


@ui_meta(actions.ActionShootdown)
class ActionShootdown:
    target_independent = False
    shootdown_message = '您不能这样出牌'


@ui_meta(actions.BaseActionStage)
class BaseActionStage:
    idle_prompt = '请出牌…'

    def choose_card_text(self, g, act, cards):
        if not act.cond(cards):
            return False, '您选择的牌不符合出牌规则'
        else:
            return True, '不会显示'


@ui_meta(actions.VitalityLimitExceeded)
class VitalityLimitExceeded:
    target_independent = True
    shootdown_message = '你没有干劲了'
