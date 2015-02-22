# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import ForEach, GenericAction, LaunchCard, UserAction
from ..cards import AttackCard, AttackCardHandler, Skill
from ..inputlets import ChooseOptionInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class HeterodoxySkipAction(GenericAction):
    def apply_action(self):
        return True


class HeterodoxyHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('MaidenCostumeHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and ForEach.is_group(act):
            tgt = act.target
            if not tgt.has_skill(Heterodoxy): return act

            g = Game.getgame()
            for a in reversed(g.action_stack):
                if isinstance(a, HeterodoxyAction):
                    break
            else:
                return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            act.cancelled = True
            g.process_action(HeterodoxySkipAction(tgt, tgt))

        return act


class HeterodoxyAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card.associated_cards[0]
        src = self.source
        victim = self.target
        tgts = self.target_list[1:]

        g.players.reveal(card)
        card.move_to(victim.cards)  # HACK: Silently, no events
        # migrate_cards([self.associated_card], victim.cards, unwrap=migrate_cards.SINGLE_LAYER)

        if card.is_card(AttackCard):
            src.tags['attack_num'] -= 1

        lc = LaunchCard(victim, tgts, card)

        g = Game.getgame()
        g.process_action(lc)

        return True

    def is_valid(self):
        src = self.source
        card = self.associated_card.associated_cards[0]
        if card.is_card(AttackCard) and src.tags['attack_num'] < 1:
            if not AttackCardHandler.is_freeattack(src):
                return False

        victim = self.target
        tgts = self.target_list[1:]
        lc = LaunchCard(victim, tgts, card)
        return lc.can_fire()


class Heterodoxy(Skill):
    no_drop = True
    associated_action = HeterodoxyAction
    skill_category = ('character', 'active')
    usage = 'handover'

    def check(self):
        cl = self.associated_cards
        return (
            cl and len(cl) == 1 and
            cl[0].resides_in.type in ('cards', 'showncards') and
            not cl[0].is_card(Skill) and
            getattr(cl[0], 'associated_action', None)
        )

    def target(self, g, src, tl):
        cl = self.associated_cards
        if not cl: return ([], False)
        c = cl[0]
        tname = c.target.__name__

        tl = [t for t in tl if not t.dead]

        if not tl: return [], False
        if tl[0] is self.player: return [], False

        if tname in ('t_Self', 't_All', 't_AllInclusive'):
            return tl[-1:], True
        else:
            _tl, valid = c.target(g, tl[0], tl[1:])
            return [tl[0]] + _tl, valid


@register_character
class Seiga(Character):
    skills = [Heterodoxy]
    eventhandlers_required = [HeterodoxyHandler]
    maxlife = 4
