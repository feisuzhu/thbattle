# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, Callable, Dict, List, Type, cast
import logging

# -- third party --
# -- own --
from client.core import Core
from game.base import Player
from thb.actions import THBAction, ActionStage, Damage, Fatetell, LaunchCard, MigrateCardsTransaction, Pindian
from thb.actions import PlayerDeath, PlayerTurn, UserAction
from thb.cards.base import Card, VirtualCard
from thb.characters.base import Character
from thb.mode import THBattle
from utils.misc import BatchList, group_by


# -- code --
log = logging.getLogger('THBattleUI_Effects')


def damage_effect(g: THBattle, core: Core, evt: str, act: Damage):
    core.gate.post('thb.ui.damage', {
        'target': to_actor(act.target),
        'amount': act.amount,
    })


def player_turn_effect(g: THBattle, core: Core, evt: str, act: PlayerTurn):
    core.gate.post('thb.ui.player_turn', {
        'actor': to_actor(act.target)
    })
    sync_game_state(g, core, evt, act)


def player_turn_effect_after(g: THBattle, core: Core, evt: str, act: PlayerTurn):
    core.gate.post('thb.ui.player_turn', {
        'actor': None
    })
    sync_game_state(g, core, evt, act)


EFFECT_STRING_FUNCTION_MAPPING = {
    'action_before': 'effect_string_before',
    'action_apply': 'effect_string_apply',
    'action_after': 'effect_string',
}

SOUND_EFFECT_FUNCTION_MAPPING = {
    'action_before': 'sound_effect_before',
    'action_apply': 'sound_effect',
    'action_after': 'sound_effect_after',
}


def general_action_effect(g: THBattle, core: Core, evt: str, act: THBAction):
    meta = getattr(act, 'ui_meta', None)
    if not meta: return

    if evt == 'action_before':
        rays = getattr(meta, 'ray', None)
        rays = rays(act) if rays else []
        for f, t in rays:
            core.gate.post('thb.ui.ray', {
                'from': to_actor(f), 'to': to_actor(t)
            })

    text = lambda t: core.gate.post('thb.ui.text', {'text': t})

    if prompt := getattr(meta, EFFECT_STRING_FUNCTION_MAPPING[evt], None):
        s = prompt(act)
        if isinstance(s, (tuple, list)):
            for t in s:
                text(t)
        elif isinstance(s, str):
            text(s)

    if snd := getattr(meta, SOUND_EFFECT_FUNCTION_MAPPING[evt], None):
        if clip := snd(act):
            play_at_target = getattr(meta, 'play_sound_at_target', False)
            play_at = to_actor(act.target if play_at_target else act.source)
            core.gate.post('thb.ui.sound', {
                'clip': clip,
                'play_at': play_at,
            })


def ui_show_disputed_effect(g: THBattle, core: Core, evt: str, cards: List[Card]):
    rawcards = VirtualCard.unwrap(cards)
    instructions = MigrateCardsTransaction.ui_meta.detach_animation_instructions(None, rawcards)
    core.gate.post('thb.ui.card_migration', instructions)


def pindian_effect_start(g: THBattle, core: Core, evt: str, act: Any):
    core.gate.post('thb.ui.pindian:start', {
        'source': to_actor(act.source),
        'target': to_actor(act.target),
    })


def pindian_effect_chosen(g: THBattle, core: Core, evt: str, arg: Any):
    p, card = arg
    core.gate.post('thb.ui.pindian:chosen', {
        'who': to_actor(p),
        'card': Card.dump(card),
    })


def pindian_effect_card_reveal(g: THBattle, core: Core, evt: str, act: Any):
    view = Card.dump
    cards = act.pindian_card
    core.gate.post('thb.ui.pindian:reveal', {
        'source_card': view(cards[act.source]),
        'target_card': view(cards[act.target]),
    })


def pindian_effect_finish(g: THBattle, core: Core, evt: str, act: Any):
    core.gate.post('thb.ui.pindian:finish', {
        'succeeded': act.succeeded,
    })


def sync_game_state(g: THBattle, core: Core, evt: str, act: Any):
    from .state import state_of
    core.gate.post('thb.ui.game_state', state_of(g))


actions_mapping: Dict[str, Dict[Type[THBAction], Callable]] = {
    'action_before': {
        Pindian:     pindian_effect_start,
        ActionStage: sync_game_state,
        PlayerTurn:  player_turn_effect,
        THBAction:   general_action_effect,
    },
    'action_apply': {
        Damage: damage_effect,
        THBAction: general_action_effect,
    },
    'action_after': {
        Pindian:     pindian_effect_finish,
        PlayerDeath: sync_game_state,
        LaunchCard:  sync_game_state,
        ActionStage: sync_game_state,
        PlayerTurn:  player_turn_effect_after,
        THBAction:   general_action_effect,
    }
}


def action_effects(g: THBattle, core: Core, evt: str, act: THBAction):
    cls = act.__class__

    if isinstance(act, UserAction):
        sync_game_state(g, core, evt, act)

    while cls is not object:
        if f := actions_mapping[evt].get(cls):
            f(g, core, evt, act)
        cls = cls.__base__


def to_actor(o: Any) -> dict:
    if isinstance(o, Character):
        return {'pid': o.player.pid}
    elif isinstance(o, Player):
        return {'pid': o.pid}
    else:
        raise Exception(f'WTF: {o}')


def user_input_start_effects(g: THBattle, core: Core, evt: str, arg: Any):
    trans, ilet = arg
    core.gate.post('thb.ui.input_start', {
        'trans_name': trans.name,
        'actor': to_actor(ilet.actor),
    })


def user_input_finish_effects(g: THBattle, core: Core, evt: str, arg: Any):
    trans, ilet, rst = arg
    core.gate.post('thb.ui.input_finish', {
        'trans_name': trans.name,
        'actor': to_actor(ilet.actor),
    })


def card_migration_effects(g: THBattle, core: Core, evt: str, arg: Any):
    instructions = MigrateCardsTransaction.ui_meta.animation_instructions(arg)
    core.gate.post('thb.ui.card_migration', instructions)


def card_detach_effects(g: THBattle, core: Core, evt: str, arg: Any):
    trans, cards = arg
    instructions = MigrateCardsTransaction.ui_meta.detach_animation_instructions(trans, cards)
    core.gate.post('thb.ui.card_migration', instructions)


def game_roll_prompt(g: THBattle, core: Core, evt: str, arg: Any):
    pl = cast(BatchList[Player], arg)
    t = ' -> '.join(f'*[user:{p.pid}]' for p in pl)
    core.gate.post('thb.ui.text', {'text': f'Roll点顺序：{t}'})


def showcards_effect(g: THBattle, core: Core, evt: str, act: Any):
    if act.ui_meta.is_relevant_to_me(act):
        core.gate.post('thb.ui.showcards', {
            'who': to_actor(act.target),
            'cards': [Card.dump(c) for c in act.cards],
            'to': [to_actor(ch) for ch in act.to],
        })


def fatetell_effect(g: THBattle, core: Core, evt: str, act: Any):
    text = Fatetell.ui_meta.fatetell_prompt_string(act)
    core.gate.post('thb.ui.text', {'text': text})


def reseat_effects(g: THBattle, core: Core, evt: str, arg: Any):
    b4, after = arg
    core.gate.post('thb.ui.reseat', {
        'before': [to_actor(p) for p in b4],
        'after': [to_actor(p) for p in after],
    })


# ----- MAPPING -----


events_mapping: Dict[str, Callable] = {
    'action_before':       action_effects,
    'action_apply':        action_effects,
    'action_after':        action_effects,
    'fatetell':            fatetell_effect,
    'user_input_start':    user_input_start_effects,
    'user_input_finish':   user_input_finish_effects,
    'post_card_migration': card_migration_effects,
    'detach_cards':        card_detach_effects,
    'game_roll':           game_roll_prompt,
    'reseat':              reseat_effects,
    'showcards':           showcards_effect,
    'ui_show_disputed':    ui_show_disputed_effect,
}


def handle_event(g: THBattle, core: Core, evt: str, arg: Any):
    if f := events_mapping.get(evt):
        f(g, core, evt, arg)
        return True
    else:
        return False
