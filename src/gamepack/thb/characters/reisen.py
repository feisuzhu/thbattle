# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import Damage, DropCards, LaunchCard, PlayerTurn
from gamepack.thb.actions import UserAction, user_choose_cards
from gamepack.thb.cards import AttackCard, Card, DuelCard, Heal, HealCard, PhysicalCard, Skill
from gamepack.thb.cards import t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet


# -- code --
class Lunatic(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class Discarder(Skill):
    associated_action = None
    distance = 1
    skill_category = ('character', 'passive')
    target = t_None


class MahjongDrug(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class LunaticAction(UserAction):
    def apply_action(self):
        self.target.skills.append(Discarder)
        self.target.tags['reisen_discarder'] = True  # for tag
        return True


class LunaticHandler(EventHandler):
    interested = (
        ('action_after', Damage),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not src: return act
            if not src.has_skill(Lunatic): return act

            tgt = act.target
            if tgt.has_skill(Discarder): return act

            g = Game.getgame()
            for lc in reversed(g.action_stack):
                if isinstance(lc, LaunchCard):
                    break
            else:
                return act

            c = lc.card
            if not (c.is_card(AttackCard) or c.is_card(DuelCard)):
                return act

            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                g.process_action(LunaticAction(src, tgt))

        return act


class DiscarderHandler(EventHandler):
    interested = (
        ('action_after', PlayerTurn),
        'action_can_fire',
    )

    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire' and isinstance(arg[0], LaunchCard):
            lc, valid = arg
            src = lc.source
            if not src.has_skill(Discarder): return arg
            g = Game.getgame()
            if src is not g.current_turn: return arg

            c = lc.card
            if not c.is_card(PhysicalCard): return arg
            if not c.is_card(AttackCard): return lc, False

            dist = LaunchCard.calc_distance(src, Discarder(src))
            dist.pop(src, '')
            nearest = max(min(dist.values()), 0)
            avail = {p for p in dist if dist[p] <= nearest}

            if not set(lc.target_list) <= avail:
                return lc, False

        elif evt_type == 'action_after' and isinstance(arg, PlayerTurn):
            tgt = arg.target
            if tgt.has_skill(Discarder):
                tgt.skills.remove(Discarder)
                tgt.tags['reisen_discarder'] = False  # for tag

        return arg


class MahjongDrugAction(UserAction):
    def apply_action(self):
        self.target.tags['wine'] = True
        return True

    def is_valid(self):
        return not self.target.dead


class MahjongDrugHandler(EventHandler):
    interested = (
        ('action_after', Heal),
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Heal):
            tgt = act.target
            if not tgt.has_skill(MahjongDrug): return act
            card = getattr(act, 'associated_card', None)
            if not card or not card.is_card(HealCard): return act

            if user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                Game.getgame().process_action(MahjongDrugAction(tgt, tgt))

        return act


@register_character
class Reisen(Character):
    skills = [Lunatic, MahjongDrug]
    eventhandlers_required = [DiscarderHandler, LunaticHandler, MahjongDrugHandler]
    maxlife = 4
