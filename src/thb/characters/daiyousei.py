# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from thb.actions import ActionStage, DrawCardStage, GenericAction, MigrateCardsTransaction
from thb.actions import PlayerDeath, UserAction, migrate_cards
from thb.cards.base import CardList, Skill, t_None, t_OtherOne
from thb.cards.classes import Heal
from thb.characters.base import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet
from thb.mode import THBEventHandler


# -- code --
class SupportAction(UserAction):
    def apply_action(self):
        cl = self.associated_card.associated_cards
        src = self.source
        tgt = self.target
        lst = src.tags.get('daiyousei_spnum', 0)
        n = len(cl)
        if lst < 3 <= lst + n:
            g = self.game
            g.process_action(Heal(src, src))
        src.tags['daiyousei_spnum'] = lst + n
        tgt.reveal(cl)
        migrate_cards([self.associated_card], tgt.cards, unwrap=True)
        self.cards = cl
        return True


class Support(Skill):
    associated_action = SupportAction
    skill_category = ['character', 'active']
    target = t_OtherOne
    usage = 'handover'
    no_drop = True
    no_reveal = True

    def check(self):
        cl = self.associated_cards
        return cl and all(
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards', 'equips')
            for c in cl
        )


class SupportKOFAction(UserAction):
    def apply_action(self):
        tgt = self.target
        cl = tgt.support_cl = CardList(tgt, 'support')

        with MigrateCardsTransaction(self) as trans:
            migrate_cards(tgt.cards, cl, unwrap=True, trans=trans)
            migrate_cards(tgt.showncards, cl, unwrap=True, trans=trans)
            migrate_cards(tgt.equips, cl, unwrap=True, trans=trans)

        return True


class SupportKOFReturningAction(GenericAction):
    def apply_action(self):
        migrate_cards(self.source.support_cl, self.target.cards, unwrap=True)
        return True


class SupportKOFHandler(THBEventHandler):
    interested = ['character_debut', 'action_apply']
    execute_after = ['DeathHandler']

    def handle(self, evt_type, arg):
        if evt_type == 'character_debut':
            old, new = arg
            if not old: return arg
            if not getattr(old, 'support_cl', None): return arg

            g = self.game
            g.process_action(SupportKOFReturningAction(old, new))

        elif evt_type == 'action_apply' and isinstance(arg, PlayerDeath):
            tgt = arg.target
            if not tgt.has_skill(SupportKOF): return arg

            if not (tgt.cards or tgt.showncards or tgt.equips):
                return arg

            g = self.game
            if g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                g.process_action(SupportKOFAction(tgt, tgt))

        return arg


class SupportKOF(Skill):
    associated_action = None
    skill_category = ['character', 'passive']
    target = t_None


class Moe(Skill):
    associated_action = None
    skill_category = ['character', 'passive', 'compulsory']
    target = t_None


class MoeDrawCard(DrawCardStage):
    pass


class DaiyouseiHandler(THBEventHandler):
    interested = ['action_before']

    # Well, well, things are getting messy
    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, DrawCardStage):
                tgt = act.target
                if tgt.has_skill(Moe):
                    act.amount += tgt.maxlife - tgt.life
                    act.__class__ = MoeDrawCard
            elif isinstance(act, ActionStage):
                tgt = act.target
                if tgt.has_skill(Support):
                    tgt.tags['daiyousei_spnum'] = 0
        return act


@register_character_to('common', '-kof')
class Daiyousei(Character):
    skills = [Support, Moe]
    eventhandlers = [DaiyouseiHandler]
    maxlife = 3


@register_character_to('kof')
class DaiyouseiKOF(Character):
    skills = [SupportKOF, Moe]
    eventhandlers = [DaiyouseiHandler, SupportKOFHandler]
    maxlife = 3
