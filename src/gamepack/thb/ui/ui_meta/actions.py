# -*- coding: utf-8 -*-

import random

from gamepack.thb import actions
from utils import BatchList

from .common import gen_metafunc, card_desc, G

# -----BEGIN ACTIONS UI META-----
__metaclass__ = gen_metafunc(actions)


class DrawCards:
    def effect_string(act):
        return u'|G【%s】|r摸了%d张牌。' % (
            act.target.ui_meta.char_name, act.amount,
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
            s = u'、'.join(card_desc(c) for c in act.cards)
            return u'|G【%s】|r弃掉了%d张牌：%s' % (
                act.target.ui_meta.char_name, act.dropn, s,
            )


class Damage:
    update_portrait = True

    def effect_string(act):
        s, t = act.source, act.target
        if s:
            return u'|G【%s】|r对|G【%s】|r造成了%d点伤害。' % (
                s.ui_meta.char_name, t.ui_meta.char_name, act.amount
            )
        else:
            return u'|G【%s】|r受到了%d点无来源的伤害。' % (
                t.ui_meta.char_name, act.amount
            )


class LifeLost:
    update_portrait = True

    def effect_string(act):
        return u'|G【%s】|r流失了%d点体力。' % (
            act.target.ui_meta.char_name, act.amount
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
            s.ui_meta.char_name,
            u'】|r、|G【'.join(tl.ui_meta.char_name),
            act.card.ui_meta.name
        )

    def sound_effect(act):
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


class UseCard:
    def sound_effect_after(act):
        c = act.card
        if not c:
            return

        if act.card_usage not in ('use', 'launch'):
            return

        meta = getattr(c, 'ui_meta', None)
        se = getattr(meta, 'sound_effect', None)
        return se and se(act)


class PlayerDeath:
    barrier = True
    update_portrait = True

    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|rMISS了。' % (
            tgt.ui_meta.char_name,
        )

    def sound_effect(act):
        meta = act.target.ui_meta
        se = getattr(meta, 'miss_sound_effect', None)
        if isinstance(se, (list, tuple)):
            return random.choice(se)
        else:
            return se


class PlayerRevive:
    barrier = True
    update_portrait = True

    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r重新回到了场上。' % (
            tgt.ui_meta.char_name,
        )


class TurnOverCard:
    def effect_string(act):
        tgt = act.target
        return u'|G【%s】|r翻开了牌堆顶的一张牌，%s' % (
            tgt.ui_meta.char_name,
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
            name = u'|G%s|r' % tgt.ui_meta.char_name
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
            act.source.ui_meta.char_name,
            act.target.ui_meta.char_name,
        )

    def effect_string(act):
        winner = act.source if act.succeeded else act.target
        return u'|G【%s】|r是人生赢家！' % (
            winner.ui_meta.char_name
        )

# -----END ACTIONS UI META-----
