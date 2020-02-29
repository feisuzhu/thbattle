# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from copy import deepcopy

# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, InputTransaction, user_input
from thb.actions import Damage, Reforge, RevealIdentity, UserAction, migrate_cards, random_choose_card
from thb.cards import Skill, t_None, t_One, t_OtherOne
from thb.characters.baseclasses import Character, register_character_to
from thb.common import build_choices
from thb.inputlets import ChooseGirlInputlet, ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class ThirdEye(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class ThirdEyeAction(UserAction):

    def apply_action(self):
        g = Game.getgame()
        src = self.source

        if g.process_action(ThirdEyeChooseGirl(self.source, self.target)):
             tgt = src.tags['recollected_char']
        else:
            return False

        if not tgt or not issubclass(tgt, Character):
            return False

        self.target = tgt
        skills = tgt.skills
        skills = [s for s in skills if 'character' in s.skill_category]
        skills = [s for s in skills if 'once' not in s.skill_category]
        skills = [s for s in skills if 'awake' not in s.skill_category]
        skills = [s for s in skills if 'boss' not in s.skill_category]

        if not skills: return False

        mapping = self.mapping = {s.__name__: s for s in skills}
        names = list(sorted(mapping.keys()))

        name_chosen = user_input([src], ChooseOptionInputlet(self, names)) or names[0]

        for skill in src.skills:
            if src.has_skill(skill) and skill.__name__ == 'Recollection':
                src.skills.remove(skill) # shall not fail

        for s in tgt.skills:
            if s.__name__ == name_chosen:
                s.__name__ = 'Recollection'
                self.sk_choice = deepcopy(s)
                break
        else:
            assert None, 'please kill a coffeeyin if this occurs'

        # g.players.reveal(self.sk_choice) # never do this! GAME DATA MISS

        src.skills.append(self.sk_choice)

        p = self.target
        ehs = g.ehclasses
        ehs.extend(p.eventhandlers_required)

        g.update_event_handlers()

        return True


class ThirdEyeChooseGirl(UserAction):
    # CharChoice

    def apply_action(self):
        g = Game.getgame()
        src = self.source
        if not src.has_skill(ThirdEye): return False

        # if nec., for different modes:
        # mode_name = g.__class__.__name__
        # assert mode_name
        # if mode_name == 'THBattleKOF':
        #     chars = get_characters('common')
        # if mode_name == '...':
        #     chars = get_characters('common', 'kof')
        # ...
        # ...
        from thb.characters import get_characters
        chars = get_characters('common')
        charset = set(chars)
        chars = list(charset - set(p.__class__ for p in g.players))
        if getattr(self, 'char_choice', None):
            try:
                chars.remove(self.char_choice)
            except:
                pass

        choices, _ = build_choices(
            g, {},
            candidates=chars, players=[src],
            num=[3] * 1,# for testing: num=[4] * 1,
            akaris=[0] * 1,
            shared=False,
        )

        with InputTransaction('ChooseGirl', [src], mapping=choices) as trans:
            c = user_input([src], ChooseGirlInputlet(g, choices), timeout=30, trans=trans)
            c = c or choices[src][0]

        g.players.reveal(c) # nec., for sync, no showing image

        # for ui display:
        self.char_choice = c.char_cls
        src.tags['recollected_char'] = c.char_cls

        if self.char_choice in set(p.__class__ for p in g.players):
            return False

        return True


class ThirdEyeHandler(EventHandler):
    interested = ('action_after',)
    execute_after = (
        'DyingHandler',
        'AyaRoundfanHandler',
        'NenshaPhoneHandler',
    )

    def handle(self, evt_type, act):
        if not evt_type == 'action_after': return act
        if not isinstance(act, Damage): return act

        tgt = act.target

        if not tgt.has_skill(ThirdEye): return act

        if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            return act

        Game.getgame().process_action(ThirdEyeAction(tgt, tgt))

        return act


class RosaReforgeAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target
        src.tags['rosa_reforge'] = src.tags['turn_count']

        assert tgt.showncards
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, ('showncards',)))
        card = card or random_choose_card([tgt.showncards])
        if not card:
            return False

        g.process_action(Reforge(src, tgt, card))
        self.card = card # for ui show showncard

        return True

    def is_valid(self):
        src, tgt = self.source, self.target

        if not any(getattr(tgt, 'showncards')):
            return False

        return src.tags['rosa_reforge'] < src.tags['turn_count']


class Rosa(Skill):
    associated_action = RosaReforgeAction
    skill_category = ('character', 'active')
    target = t_One

    def check(self):
        return not self.associated_cards


class RosaRevealAction(UserAction):

    def apply_action(self):
        src = self.source
        tgt = self.target

        assert tgt.cards
        assert src.has_skill(Rosa)

        card = user_input([src], ChoosePeerCardInputlet(self, tgt, ('cards',)))
        card = card or random_choose_card([tgt.showncards])
        if not card:
            return False

        g = Game.getgame()
        g.players.reveal(card)
        migrate_cards([card], tgt.showncards)

        self.card = card # for ui

        return True


class RosaHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):

            src, tgt = act.source, act.target
            if src is tgt: return act

            self.process(src, tgt)

        return act

    def process(self, src, tgt):
        if src is None or tgt is None:
            return

        if not src.has_skill(Rosa) or tgt.dead:
            return

        if not tgt.cards:
            return

        if user_input([src], ChooseOptionInputlet(self, (False, True))):
            g = Game.getgame()
            g.process_action(RosaRevealAction(src, tgt))


class MindReadAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src, tl = self.source, self.target_list

        assert src.has_skill(MindRead) and len(tl) == 1

        if src.tags['mind_read_used']:
            return False

        src.tags['mind_read_used'] = True
        g = Game.getgame()
        tgt = tl[0]
        g.process_action(RevealIdentity(tgt, src))

        return True


class MindRead(Skill):
    associated_action = MindReadAction
    skill_category = ('character', 'active', 'once', 'boss')
    target = t_OtherOne

    def check(self):
        return not len(self.associated_cards)


@register_character_to('common', 'boss')
class SpSatori(Character):
    skills = [ThirdEye, Rosa]
    boss_skills = [MindRead]
    eventhandlers_required = [ThirdEyeHandler, RosaHandler]
    maxlife = 3
