# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
import logging
from itertools import chain, combinations, permutations
from typing import Any, cast
import random

# -- third party --
# -- own --
from game.base import EventHandler
from thb.actions import ActionStageLaunchCard, CardChooser, skill_wrap
from thb.cards.base import t_None, t_All, t_AllInclusive, t_One, t_OtherOne, t_Self, t_OneOrNone
from thb.inputlets import ActionInputlet, ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
log = logging.getLogger('UserInputFuzzingHandler')
C = combinations


class UserInputFuzzingHandler(EventHandler):

    def handle(self, evt: str, arg: Any) -> Any:
        if evt == 'user_input':
            trans, ilet = arg
            self.react(trans, ilet)

        return arg

    def react(self, trans, ilet):
        p = ilet.actor
        g = self.game

        if trans.name == 'ActionStageAction':
            if random.random() < 0.05:
                return False

            cards = list(p.showncards) + list(p.cards) + list(p.equips)

            while random.random() < 0.5:
                # Skill
                skl = [sk for sk in p.skills if sk.target.__name__ != 't_None']
                if skl:
                    sk = random.choice(skl)
                else:
                    break

                # Card
                cc = list(chain(*[combinations(cards, i) for i in range(5)]))
                random.shuffle(cc)
                for cl in cc:
                    c = skill_wrap(p, [sk], cl, {})
                    if c.check():
                        break
                else:
                    break

                # Targets
                for t in self.possible_targets(g, p, c):
                    if self.try_launch(ilet, cl, t, skills=[sk]):
                        return

                break

            for c in cards:
                if not c.associated_action:
                    continue

                for t in self.possible_targets(g, p, c):
                    if self.try_launch(ilet, [c], t):
                        return True

        elif trans.name == 'Action' and isinstance(ilet, ActionInputlet):
            if not (ilet.categories and not ilet.candidates):
                return True

            cond = cast(CardChooser, ilet.initiator).cond
            cl = list(p.showncards) + list(p.cards)
            for c in chain(C(cl, 1), C(cl, 2)):
                if cond(c):
                    ilet.set_result(skills=[], cards=c, characters=[])
                    return True

        elif trans.name == 'ChooseOption' and isinstance(ilet, ChooseOptionInputlet):
            ilet.set_option(random.choice(list(ilet.options) * 2 + [None]))

        elif trans.name == 'ChoosePeerCard' and isinstance(ilet, ChoosePeerCardInputlet):
            tgt = ilet.target
            if random.random() < 0.9:
                cats = [getattr(tgt, i) for i in ilet.categories]
                c = random.choice(list(chain(*cats)))
                ilet.set_card(c)
        else:
            log.warning('Not processing %s transaction', trans.name)

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
                rl.extend(list(permutations(pl, i)))
            random.shuffle(rl)

        elif tn == 't_OneOrNone':
            rl = [[i] for i in pl]
            rl.append([])
            random.shuffle(rl)

        elif tn == '_t_OtherN':
            n = target._for_test_OtherN
            rl = list(permutations(pl, n))
            random.shuffle(rl)
            rl = [list(i) for i in rl]
        else:
            rl = []
            for i in range(3):  # HACK: should be enough
                rl.extend(list(permutations(pl, i)))
            random.shuffle(rl)

        for i in rl:
            log.debug("tgt %s", target)
            log.debug("rl %s", i)
            rst, ok = c.target(g, me, i)
            if ok:
                yield rst
