# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from thb.actions import ActionStage, Damage, DropCards, LaunchCard, UserAction
from thb.actions import ask_for_action
from thb.cards import AttackCard, BaseAttack, DummyCard, GrazeCard, LaunchGraze, PhysicalCard, Skill, TreatAs, VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to


# -- code --
class InsightfulSwordAction(UserAction):
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        Game.getgame().process_action(Damage(self.source, self.target, 1))
        return True


class InsightfulSwordHandler(EventHandler):
    interested = ('attack_aftergraze',)
    execute_after = ('LaevateinHandler',)

    def handle(self, evt_type, arg):
        if evt_type == 'attack_aftergraze':
            act, succeed = arg
            src, tgt = act.source, act.target

            if isinstance(act, BaseAttack):
                if src and tgt.has_skill(InsightfulSword) and tgt.tags['sword_graze']:
                    tgt.tags['sword_graze'] = False
                    src.dead or succeed or Game.getgame().process_action(InsightfulSwordAction(tgt, src))

        return arg


class InsightfulMarkerHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, LaunchGraze):
            src = act.target
            if src.has_skill(InsightfulSword):
                graze = getattr(act, 'card')

                if graze and graze.is_card(InsightfulSword):
                    src.tags['sword_graze'] = True

        return act


class InsightfulSword(TreatAs, Skill):
    skill_category = ('character', 'passive')

    @property
    def treat_as(self):
        cl = self.associated_cards
        if not cl: return DummyCard
        c = cl[0]
        if c.is_card(PhysicalCard):
            return GrazeCard
        return DummyCard

    def check(self):
        cl = self.associated_cards
        if not cl or len(cl) != 1: return False
        c = cl[0]
        if set(getattr(c, 'category')) == {'equipment', 'weapon'}:
            if c.resides_in is not None and c.resides_in.type in ('cards', 'showncards', 'equips'):
                return c.resides_in.owner.has_skill(InsightfulSword)
        return False


class PresentWorldSlashAttackCard(TreatAs, VirtualCard):
    treat_as = AttackCard


class PresentWorldSlashAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(DropCards(src, src, self.cards))
        lc = LaunchCard(src, [tgt], PresentWorldSlashAttackCard(src), bypass_check=True)
        src.has_skill(PresentWorldSlash) and lc.can_fire() and g.process_action(lc)
        return True


class PresentWorldHandler(EventHandler):
    interested = ('action_after', )

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, ActionStage):
            tgt = act.target
            if tgt.tags['vitality'] > 0:
                return act

            if tgt.has_skill(PresentWorldSlash):
                g = Game.getgame()
                pl = [p for p in g.players if not p.dead and p is not tgt]
                _, rst = ask_for_action(self, [tgt], ('cards', 'showncards', 'equips'), pl)
                if not rst:
                    return act

                try:
                    cl, pl = rst
                    p, = pl
                except Exception:
                    return act

                g.process_action(PresentWorldSlashAction(tgt, p, cl))

        return act

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)

    def choose_player_target(self, tl):
        if not tl: return (tl, False)
        return (tl[-1:], True)


class PresentWorldSlash(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


@register_character_to('common')
class SpYoumu(Character):
    skills = [InsightfulSword, PresentWorldSlash]
    eventhandlers_required = [InsightfulMarkerHandler, InsightfulSwordHandler, PresentWorldHandler]
    maxlife = 4
