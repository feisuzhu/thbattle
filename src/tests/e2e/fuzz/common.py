# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from itertools import chain, combinations as C, permutations as P
from typing import Any, cast, Tuple, Sequence
import logging
import random

# -- third party --
import gevent

# -- own --
from game.base import EventHandler
from thb.cards.base import Card
from thb.actions import ActionStageLaunchCard, CardChooser, CharacterChooser
from thb.actions import MigrateCardsTransaction, skill_wrap
from thb.inputlets import ActionInputlet, ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
log = logging.getLogger('UserInputFuzzingHandler')


def let_it_go(*cores):
    while True:
        gevent.idle(-100)

        for i in range(10):
            if any(c.server._ep.active for c in cores):
                break

            gevent.sleep(0.05)
        else:
            raise Exception('STUCK!')

        for c in cores:
            c.server._ep.active = False


class UserInputFuzzingHandler(EventHandler):

    def handle(self, evt: str, arg: Any) -> Any:
        if evt == 'user_input':
            trans, ilet = arg
            self.react(trans, ilet)
        elif evt in ('action_before', 'action_apply', 'action_after'):
            self.effect_meta(evt, arg)
        elif evt == 'post_card_migration':
            self.card_mig_ui_meta(arg)
        elif evt == 'detach_cards':
            self.detach_ui_meta(arg)
        elif evt == 'action_stage_action':
            self.get_game_state()

        return arg

    def get_game_state(self):
        from thb.meta.state import state_of
        state_of(self.game)

    def card_mig_ui_meta(self, arg: MigrateCardsTransaction):
        arg.ui_meta.animation_instructions(arg)

    def detach_ui_meta(self, arg: Tuple[MigrateCardsTransaction, Sequence[Card]]):
        trans, cards = arg
        rst = trans.ui_meta.detach_animation_instructions(trans, cards)
        assert rst

    def effect_meta(self, evt: str, act: Any):
        while hasattr(act, 'ui_meta'):
            _type = {
                'action_before': 'effect_string_before',
                'action_apply':  'effect_string_apply',
                'action_after':  'effect_string',
            }[evt]
            prompt = getattr(act.ui_meta, _type, None)
            if not prompt: break
            prompt(act)
            break

        if hasattr(act, 'ui_meta'):
            if evt == 'action_before':
                rays = getattr(act.ui_meta, 'ray', None)
                rays = rays(act) if rays else []

            _type = {
                'action_before': 'sound_effect_before',
                'action_apply':  'sound_effect_apply',
                'action_after':  'sound_effect',
            }[evt]
            se = getattr(act.ui_meta, _type, None)
            se = se and se(act)

    def react(self, trans, ilet):
        p = ilet.actor
        g = self.game

        if trans.name == 'ActionStageAction':
            if random.random() < 0.05:
                return False

            cards = list(p.showncards) + list(p.cards) + list(p.equips)

            while random.random() < 0.5:
                # Skill
                skl = [sk for sk in p.skills if 't_None' not in sk.target.__name__]
                [sk.ui_meta.clickable() for sk in skl]
                if skl:
                    sk = random.choice(skl)
                else:
                    break

                # Card
                cc = list(chain(*[C(cards, i) for i in range(4)]))
                random.shuffle(cc)

                for tl in self.possible_targets(g, p, sk):
                    tl_seen = set()
                    for cl in cc:
                        c = skill_wrap(p, [sk], cl, {})

                        try:
                            tl, ok = c.target(p, tl)
                        except Exception as e:
                            raise Exception(f"{c}.target: {c.target} failed") from e

                        tl1 = tuple(tl)
                        if tl1 in tl_seen:
                            continue

                        tl_seen.add(tl1)

                        ok, reason = self.ui_meta_walk_wrapped([c])
                        if not ok:
                            assert not c.check(), (c, c.associated_cards, c.check(), ok, reason)
                            continue

                        try:
                            ok2, reason = c.ui_meta.is_action_valid(c, tl)
                        except Exception as e:
                            raise Exception(f"{c}.ui_meta.is_action_valid failed") from e

                        # This can happen
                        # assert (ok and bool(c.check())) == ok2, {
                        #     'ok': ok,
                        #     'c.check()': c.check(),
                        #     'ok2': ok2,
                        #     'c': c,
                        #     'tl': tl,
                        #     'reason': reason,
                        # }

                        if not ok:
                            continue

                        # This can happen too
                        # assert c.ui_meta.clickable(), c

                        if self.try_launch(ilet, cl, tl, skills=[sk]):
                            return
                break

            for c in cards:
                if not c.associated_action:
                    continue

                for t in self.possible_targets(g, p, c):
                    if self.try_launch(ilet, [c], t):
                        return True

        elif trans.name in ('Action', 'AskForRejectAction') and isinstance(ilet, ActionInputlet):
            rst = {
                'skills': [],
                'cards': [],
                'characters': [],
            }

            if ilet.categories:
                initiator = cast(CardChooser, ilet.initiator)
                cond = initiator.cond
                cl = list(p.showncards) + list(p.cards)

                found = False
                for skcls in ilet.actor.skills:
                    sk = skcls(ilet.actor)
                    if not sk.ui_meta.clickable():
                        continue

                    uiok, uireason = self.ui_meta_walk_wrapped([sk])
                    cct_ok, cct_reason = initiator.ui_meta.choose_card_text(initiator, [sk])
                    if cond([sk]) and random.random() < 0.5:
                        for c in chain([], C(cl, 1), C(cl, 2), [cl]):
                            sk = skill_wrap(p, [skcls], c, {})
                            uiok, uireason = self.ui_meta_walk_wrapped([sk])
                            assert uiok
                            assert cond([sk])
                            rst['skills'] = [skcls]
                            rst['cards'] = c
                            found = True
                            break

                    if found:
                        break
                else:
                    for c in chain(C(cl, 1), C(cl, 2), [cl]):
                        cct_ok, cct_reason = initiator.ui_meta.choose_card_text(initiator, c)
                        if cond(c):
                            assert cct_ok, (c, cct_reason)
                            rst['cards'] = c
                            break

            if ilet.candidates:
                initiator = cast(CharacterChooser, ilet.initiator)
                target = initiator.choose_player_target
                # (self, pl: Sequence[Character]) -> Tuple[List[Character], bool]: ...
                pl = ilet.candidates
                for p in chain(C(pl, 1), C(pl, 2), [pl]):
                    p, ok = target(p)
                    ccp_ok, ccp_reason = initiator.ui_meta.target(p)
                    if ok:
                        assert ccp_ok, (p, ccp_reason)
                        rst['characters'] = p
                        break

            if rst:
                ilet.set_result(**rst)

            return True

        elif trans.name == 'ChooseOption' and isinstance(ilet, ChooseOptionInputlet):
            ilet.set_option(random.choice(list(ilet.options) * 2 + [None]))

        elif trans.name == 'ChoosePeerCard' and isinstance(ilet, ChoosePeerCardInputlet):
            tgt = ilet.target
            if random.random() < 0.9:
                cats = [getattr(tgt, i) for i in ilet.categories]
                cl = list(chain(*cats))
                if cl:
                    ilet.set_card(random.choice(cl))
        elif trans.name == 'SortCharacter':
            pass
        elif trans.name == 'ChooseGirl':
            from settings import TESTING_CHARACTERS as TESTS
            choices = [c for c in ilet.mapping[ilet.actor] if c.char_cls and c.char_cls.__name__ in TESTS]
            if choices:
                c = random.choice(choices)
                log.info('Got %s', c.char_cls)
                ilet.set_choice(c)
        elif trans.name == 'HarvestChoose':
            pass
        elif trans.name == 'Pindian':
            pass
        elif trans.name == 'HopeMask':
            pass
        elif trans.name == 'Prophet':
            pass
        elif trans.name == 'ChooseIndividualCard':
            pass
        elif trans.name == 'BanGirl':
            pass
        elif trans.name == 'GalgameDialog':
            pass
        else:
            log.warning('Not processing %s transaction', trans.name)
            1/0

    def ui_meta_walk_wrapped(self, cl, check_is_complete=False):
        from thb.cards.base import Skill
        for c in cl:
            if not isinstance(c, Skill):
                continue

            if check_is_complete:
                rst, reason = c.ui_meta.is_complete(c)
                if not rst:
                    return rst, reason

            rst, reason = self.ui_meta_walk_wrapped(c.associated_cards, True)
            if not rst:
                return rst, reason

        return True, 'OK'

    def try_launch(self, ilet, cl, tl, skills=[]):
        p = ilet.actor
        if skills:
            c = skill_wrap(p, skills, cl, {})
        else:
            assert len(cl) == 1, cl
            c, = cl

        act = ActionStageLaunchCard(p, tl, c)
        if act.can_fire():
            ilet.set_result(skills=skills, cards=cl, characters=tl)
            return True

        return False

    def possible_targets(self, g, me, c):
        target = c.target
        tn = target.__name__
        pl = g.players

        if tn == 't_None':
            raise Exception('Fuck')

        elif tn == 't_Self':
            rl = [[me]]

        elif tn == 't_OtherOne':
            rl = list(pl)
            random.shuffle(rl)
            rl = [[i] for i in rl if i is not me]

        elif tn == 't_One':
            rl = list(pl)
            random.shuffle(rl)
            rl = [[i] for i in rl]

        elif tn == 't_All':
            rl = list(pl)
            rl.remove(me)
            rl = [rl]

        elif tn == 't_AllInclusive':
            rl = [pl]

        elif tn == '_t_OtherLessEqThanN':
            n = target._for_test_OtherLessEqThanN
            rl = []
            for i in range(n+1):
                rl.extend(list(P(pl, i)))
            random.shuffle(rl)

        elif tn == 't_OneOrNone':
            rl = [[i] for i in pl]
            rl.append([])
            random.shuffle(rl)

        elif tn == '_t_OtherN':
            n = target._for_test_OtherN
            rl = list(P(pl, n))
            random.shuffle(rl)
            rl = [list(i) for i in rl]
        else:
            rl = []
            for i in range(3):  # HACK: should be enough
                rl.extend(list(P(pl, i)))
            random.shuffle(rl)

        return rl
