# -*- coding: utf-8 -*-

# -- stdlib --
from functools import wraps
import logging

# -- third party --
# -- own --
from game.autoenv import Game
from gamepack.thb import actions as thbactions, cards as thbcards, inputlets
from gamepack.thb.ui.ui_meta.common import gen_metafunc

# -- code --
log = logging.getLogger('Inputlets UI Meta')

# -----BEGIN INPUTLETS UI META-----
__metaclass__ = gen_metafunc(inputlets)


class ActionDisplayResult(Exception):
    __slots__ = (
        'valid',
        'prompt',
        'pl_selecting',
        'pl_disabled',
        'pl_selected',
    )

    def __init__(self, valid, prompt, pl_selecting, pl_disabled, pl_selected):
        Exception.__init__(self)
        self.valid = valid
        self.prompt = prompt
        self.pl_selecting = pl_selecting
        self.pl_disabled = pl_disabled
        self.pl_selected = pl_selected


def walk_wrapped(cl, check_is_complete):
    g = Game.getgame()

    for c in cl:
        if not isinstance(c, thbcards.Skill):
            continue

        if check_is_complete:
            try:
                is_complete = c.ui_meta.is_complete
            except:
                is_complete = None

            if not is_complete:
                # skills that cannot combined with other skill
                raise ActionDisplayResult(False, u'您不能这样出牌', False, [], [])

            try:
                rst, reason = is_complete(g, [c])
            except:
                log.exception('card.ui_meta.is_complete error')
                raise ActionDisplayResult(False, u'[card.ui_meta.is_complete错误]', False, [], [])

            if not rst:
                raise ActionDisplayResult(False, reason, False, [], [])

        walk_wrapped(c.associated_cards, True)


def pasv_handle_card_selection(g, ilet, cards):
    if not ilet.categories:
        return [], ''

    g = Game.getgame()

    if cards:
        walk_wrapped(cards, True)

        from gamepack.thb.cards import Skill

        if cards[0].is_card(Skill) and not thbactions.skill_check(cards[0]):
            raise ActionDisplayResult(False, u'您不能这样出牌', False, [], [])

    c = ilet.initiator.cond(cards)
    c1, text = ilet.initiator.ui_meta.choose_card_text(g, ilet.initiator, cards)
    assert c == c1, 'cond = %s, meta = %s' % (c, c1)

    if not c:
        raise ActionDisplayResult(False, text, False, [], [])

    return cards, text


def pasv_handle_player_selection(g, ilet, players):
    if not ilet.candidates:
        return False, [], [], ''

    disables = [p for p in g.players if p not in ilet.candidates]
    players = [p for p in players if p not in disables]

    players, valid = ilet.initiator.choose_player_target(players)
    try:
        valid1, reason = ilet.initiator.ui_meta.target(players)
        assert bool(valid) == bool(valid1)
    except:
        log.exception('act.ui_meta.target error')
        raise ActionDisplayResult(False, u'[act.ui_meta.target错误]', bool(ilet.candidates), disables, players)

    if not valid:
        raise ActionDisplayResult(False, reason, True, disables, players)

    return True, disables, players, reason


def actv_handle_card_selection(g, act, cards):
    if len(cards) != 1:
        raise ActionDisplayResult(False, u'请选择一张牌使用', False, [], [])

    walk_wrapped(cards, False)
    card = cards[0]

    c = act.cond(cards)
    c1, text = act.ui_meta.choose_card_text(g, act, cards)
    assert c == c1, 'cond = %s, meta = %s' % (c, c1)

    if not c:
        raise ActionDisplayResult(False, text, False, [], [])

    return card


def actv_handle_target_selection(g, card, players):
    plsel = False
    selected = []
    disables = []

    target_list, tl_valid = card.target(g, g.me, players)
    if target_list is not None:
        selected = target_list[:]
        # if card.target in (thbcards.t_One, thbcards.t_OtherOne):
        if card.target.__name__ in ('t_One', 't_OtherOne'):
            for p in g.players:
                act = thbactions.ActionStageLaunchCard(g.me, [p], card)
                shootdown = act.action_shootdown()
                if shootdown is not None:
                    if shootdown.ui_meta.target_independent:
                        reason = shootdown.ui_meta.shootdown_message
                        raise ActionDisplayResult(False, reason, False, [], [])

                    disables.append(p)

        plsel = True
        for i in disables:
            try:
                target_list.remove(i)
            except ValueError:
                pass

    try:
        rst, reason = card.ui_meta.is_action_valid(g, [card], target_list)
    except Exception as e:
        log.exception(e)
        raise ActionDisplayResult(False, u'[card.ui_meta.is_action_valid错误]', False, [], [])

    if not rst:
        raise ActionDisplayResult(False, reason, plsel, disables, selected)

    if not tl_valid:  # honor result of game logic
        raise ActionDisplayResult(False, u'您选择的目标不符合规则', plsel, disables, selected)

    return target_list, disables, reason


def action_disp_func(f):
    @wraps(f)
    def wrapper(*a, **k):
        try:
            f(*a, **k)
            raise Exception('Not raising ActionDisplayResult!')
        except ActionDisplayResult as e:
            return e

        except Exception as e:
            # Arghhh
            log.exception(e)
            return ActionDisplayResult(False, unicode(e), False, [], [])

    wrapper.__name__ = f.__name__
    return wrapper


class ActionInputlet:
    @action_disp_func
    def passive_action_disp(ilet, skills, rawcards, params, players):
        g = Game.getgame()

        usage = getattr(ilet.initiator, 'card_usage', 'none')

        if skills:
            if any(not g.me.has_skill(s) for s in skills):
                raise ActionDisplayResult(False, u'您不能这样出牌', False, [], [])
            cards = [thbactions.skill_wrap(g.me, skills, rawcards, params)]
            usage = cards[0].usage if usage == 'launch' else usage
        else:
            cards = rawcards

        cards, prompt_card = pasv_handle_card_selection(g, ilet, cards)
        plsel, disables, players, prompt_target = pasv_handle_player_selection(g, ilet, players)

        verify = getattr(ilet.initiator, 'ask_for_action_verify', None)
        rst = not verify or verify(g.me, cards, players)
        if not rst:
            raise ActionDisplayResult(False, rst.ui_meta.shootdown_message, plsel, disables, players)

        raise ActionDisplayResult(True, prompt_target or prompt_card, plsel, disables, players)

    def passive_action_recommend(ilet):
        g = Game.getgame()

        if not ilet.categories: return

        for c in g.me.showncards:
            if not ilet.initiator.cond([c]): continue
            return c

        for c in g.me.cards:
            if not ilet.initiator.cond([c]): continue
            return c

    @action_disp_func
    def active_action_disp(ilet, skills, rawcards, params, players):
        g = Game.getgame()

        stage = ilet.initiator

        if not skills and not rawcards:
            raise ActionDisplayResult(False, stage.ui_meta.idle_prompt, False, [], [])

        usage = getattr(ilet.initiator, 'card_usage', 'none')

        if skills:
            if any(not g.me.has_skill(s) for s in skills):
                raise ActionDisplayResult(False, u'您不能这样出牌', False, [], [])
            cards = [thbactions.skill_wrap(g.me, skills, rawcards, params)]
            usage = cards[0].usage if usage == 'launch' else usage
        else:
            cards = rawcards

        card = actv_handle_card_selection(g, stage, cards)
        players, disables, prompt = actv_handle_target_selection(g, card, players)

        act = thbactions.ActionStageLaunchCard(g.me, players, card)

        shootdown = act.action_shootdown()
        if shootdown is not None:
            raise ActionDisplayResult(False, shootdown.ui_meta.shootdown_message, True, disables, players)

        raise ActionDisplayResult(True, prompt, True, disables, players)
