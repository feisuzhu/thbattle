# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from functools import wraps
from typing import List, Sequence
import logging

# -- third party --
# -- own --
from thb import actions, inputlets
from thb.actions import BaseActionStage
from thb.cards.base import Card, Skill
from thb.characters.base import Character
from thb.meta.common import ui_meta


# -- code --
log = logging.getLogger('Inputlets UI Meta')


@ui_meta(inputlets.ChooseOptionInputlet)
class ChooseOptionInputlet:

    def get_buttons(self, ilet: inputlets.ChooseOptionInputlet) -> dict:
        try:
            ui_meta = ilet.initiator.ui_meta
            buttons = ui_meta.choose_option_buttons
            prompt = ui_meta.choose_option_prompt
            if callable(prompt):
                prompt = prompt(ilet.initiator)
            if callable(buttons):
                buttons = buttons(ilet.initiator)

            buttons = list(reversed(buttons))

            return {'prompt': prompt, 'buttons': buttons}
        except AttributeError:
            name = ilet.initiator.__class__.__name__
            return {
                'prompt': f"UIChooseOption: {name} missing ui_meta",
                'buttons': (('确定', True), ('结束', False))
            }


@ui_meta(inputlets.ChoosePeerCardInputlet)
class ChoosePeerCardInputlet:

    def get_lists(self, ilet: inputlets.ChoosePeerCardInputlet) -> list:
        from thb.cards.base import CardList
        from thb.meta import view

        lists = [getattr(ilet.target, cat) for cat in ilet.categories]
        return [{
            'name': CardList.ui_meta.lookup[i.type],
            'cards': [view.card(c) for c in i]
        } for i in lists if i]


class ActionDisplayResult(Exception):
    __slots__ = (
        'result',
    )

    def __init__(self, valid, prompt, pl_selecting, pl_disabled, pl_selected):
        Exception.__init__(self)
        self.result = {
            'valid': valid,
            'prompt': prompt,
            'pl_selecting': pl_selecting,
            'pl_disabled': [p.get_player().pid for p in pl_disabled],
            'pl_selected': [p.get_player().pid for p in pl_selected],
        }


def walk_wrapped(g, cl, check_is_complete):
    for c in cl:
        if not isinstance(c, Skill):
            continue

        if check_is_complete:
            try:
                is_complete = c.ui_meta.is_complete
            except Exception:
                # skills that cannot combined with other skill
                raise ActionDisplayResult(False, '您不能这样出牌', False, [], [])

            try:
                rst, reason = is_complete(c)
            except Exception:
                log.exception('card.ui_meta.is_complete error')
                raise ActionDisplayResult(False, '[card.ui_meta.is_complete 错误]', False, [], [])

            if not rst:
                raise ActionDisplayResult(False, reason, False, [], [])

        walk_wrapped(g, c.associated_cards, True)


def action_disp_func(f):
    @wraps(f)
    def wrapper(self, ilet, skills, rawcards, params, players):
        try:
            skills, rawcards, players = ilet.lookup_stuffs(skills, rawcards, players)
            f(self, ilet, skills, rawcards, params, players)
            raise Exception("Didn't raise ActionDisplayResult!")
        except ActionDisplayResult as e:
            return e.result

        except Exception as e:
            log.exception("ActionInputlet meta failure")
            return ActionDisplayResult(False, str(e), False, [], []).result

    wrapper.__name__ = f.__name__
    return wrapper


@ui_meta(inputlets.ActionInputlet)
class ActionInputlet:
    @action_disp_func
    def passive_action_disp(self, ilet, skills, rawcards, params, players):
        me = self.me

        usage = getattr(ilet.initiator, 'card_usage', 'none')

        if skills:
            if any(not me.has_skill(s) for s in skills):
                raise ActionDisplayResult(False, '您不能这样出牌', False, [], [])
            cards = [actions.skill_wrap(me, skills, rawcards, params)]
            usage = cards[0].usage if usage == 'launch' else usage
        else:
            cards = rawcards

        cards, prompt_card = self.pasv_handle_card_selection(ilet, cards)
        plsel, disables, players, prompt_target = self.pasv_handle_player_selection(ilet, players)

        verify = getattr(ilet.initiator, 'ask_for_action_verify', None)
        rst = not verify or verify(me, cards, players)
        if not rst:
            raise ActionDisplayResult(False, rst.ui_meta.shootdown_message, plsel, disables, players)

        raise ActionDisplayResult(True, prompt_target or prompt_card, plsel, disables, players)

    def pasv_handle_card_selection(self, ilet, cards):
        g = self.game

        if not ilet.categories:
            return [], ''

        if cards:
            walk_wrapped(g, cards, True)

            from thb.cards.base import Skill

            if cards[0].is_card(Skill) and not actions.skill_check(cards[0]):
                raise ActionDisplayResult(False, '您不能这样出牌', False, [], [])

        c = ilet.initiator.cond(cards)
        c1, text = ilet.initiator.ui_meta.choose_card_text(g, ilet.initiator, cards)
        assert c == c1, 'cond = %s, meta = %s' % (c, c1)

        if not c:
            raise ActionDisplayResult(False, text, False, [], [])

        return cards, text

    def pasv_handle_player_selection(self, ilet, players):
        g = self.game

        if not ilet.candidates:
            return False, [], [], ''

        disables = [p for p in g.players if p not in ilet.candidates]
        players = [p for p in players if p not in disables]

        players, logic_valid = ilet.initiator.choose_player_target(players)
        try:
            ui_meta_valid, reason = ilet.initiator.ui_meta.target(players)
            assert bool(logic_valid) == bool(ui_meta_valid), 'logic: %s, ui: %s' % (logic_valid, ui_meta_valid)
        except Exception:
            log.exception('act.ui_meta.target error')
            raise ActionDisplayResult(False, '[act.ui_meta.target 错误]', bool(ilet.candidates), disables, players)

        if not logic_valid:
            raise ActionDisplayResult(False, reason, True, disables, players)

        return True, disables, players, reason

    def passive_action_recommend(self, ilet):
        if not ilet.categories: return

        me = self.me
        from thb.meta import view

        for c in me.showncards:
            if not ilet.initiator.cond([c]): continue
            return view.card(c)

        for c in me.cards:
            if not ilet.initiator.cond([c]): continue
            return view.card(c)

    def get_selectable_cards(self, ilet, for_skill):
        cards = []
        actor = ilet.actor
        if for_skill:
            cards += actor.cards
            cards += actor.showncards
            cards += actor.equips
        else:
            for cat in ilet.categories:
                cards += getattr(actor, cat)

        from thb.meta import view
        return [view.card(c) for c in cards]

    @action_disp_func
    def active_action_disp(self, ilet, skills, rawcards, params, players):
        me = self.me

        stage = ilet.initiator

        if not skills and not rawcards:
            raise ActionDisplayResult(False, stage.ui_meta.idle_prompt, False, [], [])

        usage = getattr(ilet.initiator, 'card_usage', 'none')

        if skills:
            if any(not me.has_skill(s) for s in skills):
                raise ActionDisplayResult(False, '您不能这样出牌', False, [], [])
            cards = [actions.skill_wrap(me, skills, rawcards, params)]
            usage = cards[0].usage if usage == 'launch' else usage
        else:
            cards = rawcards

        card = self.actv_handle_card_selection(stage, cards)
        players, disables, prompt = self.actv_handle_target_selection(stage, card, players)

        act = stage.launch_card_cls(me, players, card)

        shootdown = act.action_shootdown()
        if shootdown is not None:
            raise ActionDisplayResult(False, shootdown.ui_meta.shootdown_message, True, disables, players)

        raise ActionDisplayResult(True, prompt, True, disables, players)

    def actv_handle_card_selection(self, act, cards):
        g = self.game
        if len(cards) != 1:
            raise ActionDisplayResult(False, '请选择一张牌使用', False, [], [])

        walk_wrapped(g, cards, False)
        card = cards[0]

        c = act.cond(cards)
        c1, text = act.ui_meta.choose_card_text(g, act, cards)
        assert c == c1, 'cond = %s, meta = %s' % (c, c1)

        if not c:
            raise ActionDisplayResult(False, text, False, [], [])

        return card

    def actv_handle_target_selection(self, stage: BaseActionStage, card: Card, players: Sequence[Character]):
        plsel = False
        selected: List[Character] = []
        disables: List[Character] = []
        g = self.game
        me = self.me

        tl, tl_valid = card.target(me, players)
        if tl is not None:
            selected = list(tl)
            if card.target.__name__ in ('t_One', 't_OtherOne'):
                for p in g.players:
                    act = stage.launch_card_cls(me, [p], card)
                    shootdown = act.action_shootdown()
                    if shootdown is not None:
                        if shootdown.ui_meta.target_independent:
                            reason = shootdown.ui_meta.shootdown_message
                            raise ActionDisplayResult(False, reason, False, [], [])

                        disables.append(p)

            plsel = True
            for i in disables:
                try:
                    tl.remove(i)
                except ValueError:
                    pass

        try:
            rst, reason = card.ui_meta.is_action_valid(card, tl)
        except Exception:
            log.exception('card.ui_meta.is_action_valid error')
            raise ActionDisplayResult(False, '[card.ui_meta.is_action_valid错误]', False, [], [])

        if not rst:
            raise ActionDisplayResult(False, reason, plsel, disables, selected)

        if not tl_valid:  # honor result of game logic
            raise ActionDisplayResult(False, '您选择的目标不符合规则', plsel, disables, selected)

        return tl, disables, reason
