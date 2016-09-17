# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from thb.actions import Damage, FinalizeStage, LaunchCard, Reforge, UserAction
from thb.actions import ask_for_action
from thb.cards import Attack, AttackCard, Card, GrazeCard, LaunchGraze, Skill, TreatAs
from thb.cards import UseGraze, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from utils import classmix, InstanceHookMeta


# -- code --
class JiongyanjianLegalCard(object):
    __metaclass__ = InstanceHookMeta

    @classmethod
    def instancecheck(cls, c):
        if cls is JiongyanjianLegalCard:
            if c.is_card(GrazeCard):
                return True

            if isinstance(c, Card) and set(c.category) == {'equipment', 'weapon'}:
                return True

        return False

    @classmethod
    def subclasscheck(cls, C):
        raise NotImplemented


class JiongyanjianGrazeCard(TreatAs, VirtualCard):
    treat_as = GrazeCard


class JiongyanjianGrazeAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        tgt, card = self.target, self.card
        return Game.getgame().process_action(LaunchCard(tgt, [tgt], card))


class JiongyanjianDamageAction(Damage):
    pass


class JiongyanjianMixin(object):
    def process_card(self, card):
        g = Game.getgame()
        if not card.is_card(GrazeCard):
            tgt = self.target
            if not g.process_action(JiongyanjianGrazeAction(tgt, tgt, card)):
                return False

            card = JiongyanjianGrazeCard(tgt)

        return super(JiongyanjianMixin, self).process_card(card)


class JiongyanjianHandler(EventHandler):
    interested = ('action_before', 'action_after')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, (UseGraze, LaunchGraze)):
            tgt = act.target
            if tgt.has_skill(Jiongyanjian):
                act.__class__ = classmix(JiongyanjianMixin, act.__class__)
                act.card_cls = JiongyanjianLegalCard

        elif evt_type == 'action_after' and isinstance(act, Attack):
            src, tgt = act.source, act.target
            if not act.succeeded and tgt.has_skill(Jiongyanjian):
                for c in tgt.equips:
                    if 'weapon' in c.category:
                        g = Game.getgame()
                        g.process_action(JiongyanjianDamageAction(tgt, src, 1))
                        break

        return act


class Jiongyanjian(Skill):
    associated_action = None
    skill_category = ('character', 'active')
    target = t_None


class XianshizhanAttackCard(TreatAs, VirtualCard):
    treat_as = AttackCard


class XianshizhanAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        src, tgt, c = self.source, self.target, self.card
        g = Game.getgame()
        g.process_action(Reforge(src, src, c))
        g.process_action(LaunchCard(src, [tgt], XianshizhanAttackCard(src), bypass_check=True))
        return True


class XianshizhanHandler(EventHandler):
    interested = ('action_apply', )

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            tgt = act.target
            if tgt.has_skill(Xianshizhan):
                g = Game.getgame()
                pl = [p for p in g.players if not p.dead and p is not tgt]
                _, rst = ask_for_action(self, [tgt], ('cards', 'showncards', 'equips'), pl)
                if not rst:
                    return act

                try:
                    cl, pl = rst
                    c, = cl
                    p, = pl
                except Exception:
                    return act

                g.process_action(XianshizhanAction(tgt, p, c))

        return act

    def cond(self, cl):
        return len(cl) == 1 and \
            not cl[0].is_card(VirtualCard) and \
            'basic' not in cl[0].category

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)


class Xianshizhan(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


# @register_character_to('1week')
class Youmu20150620(Character):
    skills = [Jiongyanjian, Xianshizhan]
    eventhandlers_required = [JiongyanjianHandler, XianshizhanHandler]
    maxlife = 4
