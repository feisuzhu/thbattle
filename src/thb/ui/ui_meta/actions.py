# -*- coding: utf-8 -*-

import random

from thb import actions
from utils import BatchList

from .common import gen_metafunc, card_desc, G

# -----BEGIN ACTIONS UI META-----
__metaclass__ = gen_metafunc(actions)


class DrawCards:
    def effect_string(act):
        return u'|G【%s】|r摸了%d张牌。' % (
            act.target.ui_meta.name, act.amount,
        )


class DropCardStage:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'OK，就这些了')
        else:
            return (False, u'请弃掉%d张牌…' % act.dropn)

    def effect_string(act):
        if act.dropn > 0 and act.cards:
            return u'|G【%s】|r弃掉了%d张牌：%s' % (
                act.target.ui_meta.name, act.dropn, card_desc(act.cards),
            )


class Damage:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(act):
        s, t = act.source, act.target
        if s:
            return u'|G【%s】|r对|G【%s】|r造成了%d点伤害。' % (
                s.ui_meta.name, t.ui_meta.name, act.amount
            )
        else:
            return u'|G【%s】|r受到了%d点无来源的伤害。' % (
                t.ui_meta.name, act.amount
            )

    def sound_effect(act):
        return 'thb-sound-hit'


class LifeLost:
    update_portrait = True
    play_sound_at_target = True

    def effect_string(act):
        return u'|G【%s】|r流失了%d点体力。' % (
            act.target.ui_meta.name, act.amount
        )


class LaunchCard:
    def effect_string_before(act):
        s, tl = act.source, BatchList(act.target_list)
        c = act.card
        if not c:
            return

        meta = getattr(c, 'ui_meta', None)
        effect_string = getattr(meta, 'effect_string', None)
        if effect_string:
            return effect_string(act)

        return u'|G【%s】|r对|G【%s】|r使用了|G%s|r。' % (
            s.ui_meta.name,
            u'】|r、|G【'.join(tl.ui_meta.name),
            act.card.ui_meta.name
        )

    def sound_effect_before(act):
        c = act.card
        if not c:
            return

        meta = getattr(c, 'ui_meta', None)
        se = getattr(meta, 'sound_effect', None)
        return se and se(act)

    def ray(act):
        if getattr(act.card.ui_meta, 'custom_ray', False):
            return []

        s = act.source
        return [(s, t) for t in act.target_list]


class AskForCard:
    def sound_effect_after(act):
        c = act.card
        if not c:
            return

        if act.card_usage != 'use':
            return

        meta = getattr(c, 'ui_meta', None)
        se = getattr(meta, 'sound_effect', None)
        return se and se(act)


class PlayerDeath:
    update_portrait = True

    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|rMISS了。' % (
            tgt.ui_meta.name,
        )

    def sound_effect(act):
        meta = act.target.ui_meta
        se = getattr(meta, 'miss_sound_effect', None)
        if isinstance(se, (list, tuple)):
            return random.choice(se)
        else:
            return se


class PlayerRevive:
    update_portrait = True

    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r重新回到了场上。' % (
            tgt.ui_meta.name,
        )


class TurnOverCard:
    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r翻开了牌堆顶的一张牌，%s' % (
            tgt.ui_meta.name,
            card_desc(act.card)
        )


class RevealIdentity:
    def effect_string(act):
        g = G()
        me = g.me
        if not (me in act.to if isinstance(act.to, list) else me is act.to):
            return

        tgt = act.target
        i = tgt.identity
        try:
            name = u'|G%s|r' % tgt.ui_meta.name
        except:
            name = u'|R%s|r' % tgt.account.username

        return u'%s的身份是：|R%s|r' % (
            name,
            G().ui_meta.identity_table[i.type],
        )


class Pindian:
    # choose_card meta
    def choose_card_text(g, act, cards):
        if act.cond(cards):
            return (True, u'不服来战！')
        else:
            return (False, u'请选择一张牌用于拼点')

    def effect_string_before(act):
        return u'|G【%s】|r对|G【%s】|r发起了拼点' % (
            act.source.ui_meta.name,
            act.target.ui_meta.name,
        )

    def effect_string(act):
        winner = act.source if act.succeeded else act.target
        return u'|G【%s】|r是人生赢家！' % (
            winner.ui_meta.name
        )


class Fatetell:

    def fatetell_prompt_string(act):
        from thb.ui.ui_meta.common import card_desc

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
            prompt = u'|G【%s】|r进行了一次判定（|G%s|r），结果为%s。' % (
                act.target.ui_meta.name,
                act_name,
                card_desc(act.card)
            )
        else:
            prompt = u'|G【%s】|r进行了一次判定，结果为%s。' % (
                act.target.ui_meta.name,
                card_desc(act.card)
            )

        return prompt


class ActionShootdown:
    target_independent = False
    shootdown_message = u'您不能这样出牌'


class ActionStage:
    idle_prompt = u'请出牌…'

    def choose_card_text(g, act, cards):
        if not act.cond(cards):
            return False, u'您选择的牌不符合出牌规则'
        else:
            return True, u'不会显示'


class VitalityLimitExceeded:
    target_independent = True
    shootdown_message = u'你没有干劲了'

# -----END ACTIONS UI META-----
