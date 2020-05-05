# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from thb.actions import ActionStage, AskForCard, Damage, LaunchCard, UserAction
from thb.actions import ask_for_action, skill_check, skill_wrap
from thb.cards import AttackCard, BaseAttack, Card, GrazeCard, LaunchGraze, Skill, TreatAs
from thb.cards import UseGraze, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from utils import classmix, InstanceHookMeta


# -- code --
class InsightfulSwordLegalCard(object):
    __metaclass__ = InstanceHookMeta

    @classmethod
    def instancecheck(cls, c):
        if cls is InsightfulSwordLegalCard:
            if c.is_card(GrazeCard):
                return True

            if isinstance(c, Card) and \
                c.resides_in.type in ('cards', 'showncards') and \
                set(c.category) == {'equipment', 'weapon'}:

                return True

        return False


class InsightfulSwordGrazeCard(TreatAs, VirtualCard):
    treat_as = GrazeCard


class InsightfulSwordGrazeAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        tgt, card = self.target, self.card
        return Game.getgame().process_action(LaunchCard(tgt, [tgt], card))

    def is_valid(self):
        tgt, card = self.target, self.card
        return LaunchCard(tgt, [tgt], card).can_fire()

    def ask_for_action_verify(self, p, cl, tl):
        tgt, card = self.target, cl[0]
        return LaunchCard(tgt, [tgt], card).can_fire()


class InsightfulSwordDamageAction(UserAction):

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        Game.getgame().process_action(Damage(self.source, self.target, 1))
        return True


class InsightfulSwordMixin(AskForCard):
    def process_card(self, card):
        g = Game.getgame()
        if not card.is_card(GrazeCard):
            tgt = self.target
            card.move_to(tgt.cards) # shall not be detached yet, yet detached already, when AskForCard -> UseGraze -> ...
            assert card.usage == 'launch'

            if not g.process_action(InsightfulSwordGrazeAction(tgt, tgt, card)):
                return False
            if not tgt.has_skill(InsightfulSword): # fall when wearing weapon
                return False

            card = InsightfulSwordGrazeCard(tgt)
            self.card = card # for UI UseCard display

        return super(InsightfulSwordMixin, self).process_card(card)


class InsightfulMarkingHandler(EventHandler):
    interested = ('action_before', 'action_after')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, (UseGraze, LaunchGraze)):
            tgt = act.target
            if tgt.has_skill(InsightfulSword):
                act.__class__ = classmix(InsightfulSwordMixin, act.__class__)
                act.card_cls = InsightfulSwordLegalCard

        elif evt_type == 'action_after' and isinstance(act, LaunchGraze):
            tgt = act.target
            if tgt.has_skill(InsightfulSword):
                t = tgt.tags
                t['sword_graze_undone'] = False

                launched = getattr(act, 'card', None)
                if launched and launched.is_card(InsightfulSwordGrazeCard):
                    t['sword_graze_undone'] = True

        return act


class InsightfulSwordHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, BaseAttack):
            src = act.source
            tgt = act.target
            t = tgt.tags

            if t['sword_graze_undone']:
                t['sword_graze_undone'] = False
                if not act.succeeded and not src.dead and tgt.has_skill(InsightfulSword):
                    Game.getgame().process_action(InsightfulSwordDamageAction(tgt, src))

        return act


class InsightfulSword(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class PresentWorldSlashAction(UserAction):
    def __init__(self, source, target, card):
        self.source = source
        self.target = target
        self.card = card

    def apply_action(self):
        src, tgt, c = self.source, self.target, self.card
        g = Game.getgame()
        g.players.reveal([c])

        skill = skill_wrap(src, [PresentWorldSlash], [c], {})
        assert skill_check(skill)  # should not fail
        g.deck.register_vcard(skill)

        if src.has_skill(PresentWorldSlash) and not tgt.dead:
            g.process_action(LaunchCard(src, [tgt], skill, bypass_check=True))

        return True


class PresentWorldSlashHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStage):
            tgt = act.target
            if tgt.tags['vitality']: return act
            if tgt.has_skill(PresentWorldSlash):
                if not (tgt.cards, tgt.showncards, tgt.equips):
                    return act

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

                g.process_action(PresentWorldSlashAction(tgt, p, c))

        return act

    def cond(self, cl):
        return len(cl) == 1 and \
            not cl[0].is_card(VirtualCard)

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)


class PresentWorldSlash(TreatAs, Skill):
    # for skill wrap
    treat_as = AttackCard
    skill_category = ('character', 'passive')

    def check(self):
        return Game.getgame().current_player is self.player


@register_character_to('common')
class SpYoumu(Character):
    skills = [InsightfulSword, PresentWorldSlash]
    eventhandlers_required = [InsightfulMarkingHandler, InsightfulSwordHandler, PresentWorldSlashHandler]
    maxlife = 4
