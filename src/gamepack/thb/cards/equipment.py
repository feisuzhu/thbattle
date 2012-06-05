# -*- coding: utf-8 -*-

from .base import *
from ..actions import *

from . import basic, spellcard, base

from utils import check, CheckFailed

class WearEquipmentAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card
        target = self.target
        equips = target.equips
        g = Game.getgame()
        for oc in equips:
            if oc.equipment_category == card.equipment_category:
                g.process_action(DropCards(target, [oc]))
                break
        migrate_cards([card], target.equips)
        return True

@register_eh
class EquipmentTransferHandler(EventHandler):
    def handle(self, evt, args):
        if evt == 'card_migration':
            act, cards, _from, to = args
            if _from is not None and _from.type == CardList.EQUIPS:
                for c in cards:
                    try:
                        _from.owner.skills.remove(c.equipment_skill)
                    except ValueError:
                        pass

            if to is not None and to.type == CardList.EQUIPS:
                for c in cards:
                    to.owner.skills.append(c.equipment_skill)

        return args

class ShieldSkill(Skill):
    associated_action = None
    target = t_None

class OpticalCloakSkill(ShieldSkill): # just a tag
    pass

class OpticalCloak(FatetellAction, GenericAction):
    # 光学迷彩
    def apply_action(self):
        g = Game.getgame()
        target = self.target
        ft = Fatetell(target, lambda card: card.suit in (Card.HEART, Card.DIAMOND))
        g.process_action(ft)
        if ft.succeeded:
            return True
        else:
            return False

@register_eh
class OpticalCloakHandler(EventHandler):
    def handle(self, evt_type, act):
        from .basic import UseGraze
        if evt_type == 'action_before' and isinstance(act, UseGraze):
            target = act.target
            if not target.has_skill(OpticalCloakSkill): return act
            if not target.user_input('choose_option', self): return act
            g = Game.getgame()
            if g.process_action(OpticalCloak(target, target)):
                return DummyAction(target, target, True)
            return act
        return act

class UFOSkill(Skill):
    associated_action = None
    target = t_None

class GreenUFOSkill(UFOSkill):
    increment = 1

class RedUFOSkill(UFOSkill):
    increment = 1

@register_eh
class UFODistanceHandler(EventHandler):
    execute_before = ('DistanceValidator',)
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, CalcDistance):
            source = act.source
            for s in source.skills:
                if issubclass(s, RedUFOSkill):
                    act.correction += s.increment

            dist = act.distance
            for p in dist.keys():
                for s in p.skills:
                    if issubclass(s, GreenUFOSkill):
                        dist[p] += s.increment
        return act

class WeaponSkill(Skill):
    range = 1

class HakuroukenSkill(WeaponSkill):
    associated_action = None
    target = t_None
    range = 2

class Hakurouken(InternalAction):
    # 白楼剑
    def __init__(self, act):
        assert isinstance(act, basic.BaseAttack)
        self.action = act

    def apply_action(self):
        act = self.action
        target = act.target
        skills = target.skills
        for e in target.equips:
            s = e.equipment_skill
            if issubclass(s, ShieldSkill):
                skills.remove(s)
        rst = Game.getgame().process_action(act)
        for card in target.equips:
            s = card.equipment_skill
            if issubclass(s, ShieldSkill):
                skills.append(s)
        return rst

@register_eh
class HakuroukenEffectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            if hasattr(act, 'hakurouken_tag'):
                return act
            act.hakurouken_tag = True
            source = act.source
            if source.has_skill(HakuroukenSkill):
                act = Hakurouken(act)
                return act
        return act

class ElementalReactorSkill(WeaponSkill):
    associated_action = None
    target = t_None
    range = 1

@register_eh
class ElementalReactorHandler(EventHandler):
    # 八卦炉
    def handle(self, evt_type, act):
        if evt_type == 'action_stage_action':
            actor = act.actor
            if actor.has_skill(ElementalReactorSkill):
                if not actor.tags.get('reactor_tag', False):
                    actor.tags['reactor_tag'] = True
                    actor.tags['attack_num'] += 1000
            else:
                if actor.tags.get('reactor_tag', False):
                    actor.tags['reactor_tag'] = False
                    actor.tags['attack_num'] -= 1000
        elif evt_type == 'action_after' and isinstance(act, ActionStage):
            act.actor.tags['reactor_tag'] = False

        return act

class UmbrellaSkill(ShieldSkill):
    pass

@register_eh
class UmbrellaHandler(EventHandler):
    # 紫的阳伞
    execute_before = ('RejectHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before':
            if isinstance(act, (spellcard.MapCannonEffect, spellcard.SinsackCarnivalEffect)):
                if act.target.has_skill(UmbrellaSkill):
                    act.cancelled = True
        return act

class RoukankenSkill(WeaponSkill):
    range = 3
    associated_action = None
    target = t_None

class Roukanken(basic.Attack):
    pass

@register_eh
class RoukankenHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, basic.BaseAttack):
            src, tgt = act.source, act.target
            if src.has_skill(RoukankenSkill) and not act.succeeded:
                if src.user_input('choose_option', self):
                    g = Game.getgame()
                    a = basic.UseAttack(target=src)
                    if g.process_action(a):
                        card = a.cards[0]
                        a = Roukanken(source=src, target=tgt)
                        a.associated_card = card
                        g.process_action(a)
        return act

class GungnirSkill(TreatAsSkill, WeaponSkill):
    treat_as = Card.card_classes['AttackCard'] # arghhhhh, nasty circular references!
    range = 3
    target = t_OtherOne
    def check(self):
        cl = self.associated_cards
        cat = (base.CardList.HANDCARD, base.CardList.SHOWNCARD)
        if not all(c.resides_in.type in cat for c in cl): return False
        return len(cl) == 2

class Laevatein(ForEach):
    action_cls = basic.Attack

class LaevateinSkill(WeaponSkill):
    range = 4
    distance = 1
    associated_action = Laevatein
    target = t_OtherLessEqThanN(3)
    def check(self):
        try:
            cl = self.associated_cards
            check(len(cl) == 1)
            card = cl[0]
            from .definition import AttackCard
            check(card.is_card(AttackCard))
            actor = card.resides_in.owner
            check(len(actor.cards) + len(actor.showncards) == 1)
            return True
        except CheckFailed:
            return False

    def is_card(self, cls):
        from ..cards import AttackCard
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

class TridentSkill(WeaponSkill):
    range = 5
    associate_action = None
    target = t_None

@register_eh
class TridentHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, basic.BaseAttack):
            if act.succeeded and act.source.has_skill(TridentSkill):
                target = act.target
                ufos = [
                    c for c in target.equips
                    if c.equipment_category in ('greenufo', 'redufo')
                ]
                if ufos:
                    card = choose_individual_card(act.source, ufos)
                    if card:
                        g = Game.getgame()
                        g.process_action(DropCards(target=target, cards=[card]))
        return act

class RepentanceStickSkill(WeaponSkill):
    range = 2
    associate_action = None
    target = t_None

class RepentanceStick(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        cats = [
            tgt.cards, tgt.showncards,
            tgt.equips, tgt.fatetell,
        ]
        l = []
        for i in xrange(2):
            card = choose_peer_card(src, tgt, cats)
            if not card:
                card = random_choose_card(cats)
            if card:
                l.append(card)
                g.players.exclude(tgt).reveal(card)
                g.process_action(DropCards(target=tgt, cards=[card]))
        self.cards = l
        return True

@register_eh
class RepentanceStickHandler(EventHandler):
    execute_before = ('WineHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled: return act
            src, tgt = act.source, act.target
            if src and src.has_skill(RepentanceStickSkill):
                g = Game.getgame()
                pa = g.action_stack[-1]
                if not isinstance(pa, basic.BaseAttack): return act
                if not (tgt.cards or tgt.showncards or tgt.equips or tgt.fatetell):
                    return act
                if not src.user_input('choose_option', self): return act
                g.process_action(RepentanceStick(src, tgt))
                act.cancelled = True

        return act

class MaidenCostumeSkill(ShieldSkill):
    pass

@register_eh
class MaidenCostumeHandler(EventHandler):
    execute_before = ('RejectHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SinsackCarnivalEffect):
            target = act.target
            if target.has_skill(MaidenCostumeSkill):
                act.cancelled = True
                g = Game.getgame()
                dmg = Damage(source=act.source, target=target)
                dmg.associated_action = act
                g.process_action(dmg)
        return act

class IbukiGourdSkill(RedUFOSkill):
    increment = 0

@register_eh
class IbukiGourdHandler(EventHandler):
    execute_after = ('WineHandler', )
    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, ActionStage):
            actor = arg.actor
            if actor.has_skill(IbukiGourdSkill):
                g = Game.getgame()
                g.process_action(basic.Wine(actor, actor))
        elif evt_type == 'card_migration':
            from .definition import IbukiGourdCard
            act, cl, _from, to = arg
            if any(c.is_card(IbukiGourdCard) for c in cl):
                target = None
                if _from.type == _from.EQUIPS:
                    target = _from.owner
                elif to.type == to.EQUIPS:
                    target = to.owner

                if target:
                    g = Game.getgame()
                    g.process_action(basic.Wine(target, target))

        return arg

class HouraiJewelAttack(spellcard.InstantSpellCardAction):
    def apply_action(self):
        g = Game.getgame()
        dmg = Damage(self.source, self.target)
        dmg.associated_action = self
        g.process_action(dmg)
        return True

class HouraiJewelSkill(WeaponSkill):
    associated_action =  None
    target = t_None
    range = 1

@register_eh
class HouraiJewelHandler(EventHandler):
    execute_before = ('RejectHandler', 'WineHandler') # wine does not affect this.
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            src = act.source
            if src.has_skill(HouraiJewelSkill):
                if src.user_input('choose_option', self):
                    act.__class__ = HouraiJewelAttack
        return act

class SaigyouBranch(FatetellAction):
    def __init__(self, source, act):
        self.source = source
        self.target = source
        self.act = act

    def apply_action(self):
        act = self.act
        src = self.source

        g = Game.getgame()
        ft = Fatetell(src, lambda card: card.suit in (Card.SPADE, Card.CLUB))
        g.process_action(ft)
        if ft.succeeded:
            g.process_action(spellcard.Reject(src, act))
            return True
        else:
            return False

class SaigyouBranchSkill(ShieldSkill):
    pass

@register_eh
class SaigyouBranchHandler(EventHandler):
    execute_before = ('RejectHandler', )
    execute_after = ('HouraiJewelHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SpellCardAction):
            src, tgt = act.source, act.target
            if not tgt.has_skill(SaigyouBranchSkill): return act
            if act.cancelled: return act
            if isinstance(act, spellcard.Reject) and src == tgt:
                # target's own Reject
                return act

            if not tgt.user_input('choose_option', self): return act
            Game.getgame().process_action(SaigyouBranch(tgt, act))
        return act

class FlirtingSwordSkill(WeaponSkill):
    range = 2
    associated_action = None
    target = t_None

class FlirtingSword(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = user_choose_cards(self, tgt)
        g = Game.getgame()
        if cards:
            self.peer_action = 'drop'
            g.process_action(DropCards(tgt, cards))
        else:
            self.peer_action = 'draw'
            g.process_action(DrawCards(src, 1))

        return True

    def cond(self, cards):
        return len(cards) == 1

@register_eh
class FlirtingSwordHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, basic.BaseAttack):
            if act.cancelled: return act
            src = act.source
            if not src.has_skill(FlirtingSwordSkill): return act
            if not src.user_input('choose_option', self): return act

            Game.getgame().process_action(FlirtingSword(src, act.target))

        return act

class AyaRoundfan(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        g = Game.getgame()

        equip = choose_peer_card(src, tgt, [tgt.equips])
        if not equip:
            equip = random_choose_card([tgt.equips])
        g.process_action(DropCards(tgt, [equip]))
        self.card = equip

        return True


class AyaRoundfanSkill(WeaponSkill):
    range = 3
    associated_action = None
    target = t_None

@register_eh
class AyaRoundfanHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, basic.BaseAttack):
            if not act.succeeded: return act
            src = act.source
            tgt = act.target
            if src.has_skill(AyaRoundfanSkill) and tgt.equips:
                cards = user_choose_cards(self, src)
                if not cards: return act
                g = Game.getgame()
                g.process_action(DropCards(src, cards))
                g.process_action(AyaRoundfan(src, tgt))
        return act

    def cond(self, cards):
        if not len(cards) == 1: return False
        return cards[0].resides_in.type in (CardList.HANDCARD, CardList.SHOWNCARD)


class ScarletRhapsodySword(Damage):
    pass

class ScarletRhapsodySwordSkill(WeaponSkill):
    range = 3
    associated_action = None
    target = t_None

@register_eh
class ScarletRhapsodySwordHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, basic.BaseAttack):
            if act.succeeded: return act
            src = act.source
            tgt = act.target
            if not src.has_skill(ScarletRhapsodySwordSkill): return act

            g = Game.getgame()
            cats = [
                src.cards,
                src.showncards,
                src.equips,
            ]
            cards = user_choose_cards(self, src, cats)
            if cards:
                g.process_action(DropCards(src, cards))
                dmg = ScarletRhapsodySword(src, tgt, amount=act.damage)
                dmg.associated_action = act
                g.process_action(dmg)

        return act

    def cond(self, cards):
        if not len(cards) == 2: return False
        return cards[0].resides_in.type in (CardList.HANDCARD, CardList.SHOWNCARD, CardList.EQUIPS)

class DeathSickleSkill(WeaponSkill):
    range = 2
    associated_action = None
    target = t_None

class DeathSickle(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source, self.target = act.source, act.target

    def apply_action(self):
        self.action.damage += 1
        return True

@register_eh
class DeathSickleHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            src, tgt = act.source, act.target
            if tgt.cards or tgt.showncards: return act
            if not src.has_skill(DeathSickleSkill): return act
            Game.getgame().process_action(DeathSickle(act))

        return act

class KeystoneSkill(GreenUFOSkill):
    increment = 1

class Keystone(GenericAction):
    def __init__(self, act):
        assert isinstance(act, spellcard.Sinsack)
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True

@register_eh
class KeystoneHandler(EventHandler):
    execute_before = ('SaigyouBranchHandler', 'RejectHandler')
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.Sinsack):
            tgt = act.target
            if tgt.has_skill(KeystoneSkill):
                Game.getgame().process_action(Keystone(act))

        return act

class WitchBroomSkill(RedUFOSkill):
    increment = 2

class AccessoriesSkill(Skill):
    associated_action = None
    target = t_None

class YinYangOrb(GenericAction):
    def __init__(self, ft):
        self.ftact = ft
        self.source = self.target = ft.target

    def apply_action(self):
        ft = self.ftact
        tgt = ft.target

        from .definition import YinYangOrbCard
        for e in tgt.equips:
            if e.is_card(YinYangOrbCard):
                g = Game.getgame()
                g.process_action(DropCards(tgt, [e]))
                ft.card = e
                break
        else:
            raise GameError('Player has YinYangOrb skill but no equip!')

        return True

class YinYangOrbSkill(AccessoriesSkill):
    pass

@register_eh
class YinYangOrbHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Fatetell):
            tgt = act.target
            if not tgt.has_skill(YinYangOrbSkill): return act
            if not tgt.user_input('choose_option', self): return act

            g = Game.getgame()
            g.process_action(YinYangOrb(act))

        return act

class SuwakoHatSkill(AccessoriesSkill):
    pass

@register_eh
class SuwakoHatHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(SuwakoHatSkill):
                act.dropn = max(act.dropn - 2, 0)
        return act

class YoumuPhantomSkill(AccessoriesSkill):
    pass

@register_eh
class YoumuPhantomHandler(EventHandler):
    def handle(self, evt_type, arg):
        if not evt_type == 'card_migration': return arg

        act, cards, _from, to = arg

        from .definition import YoumuPhantomCard

        if _from is not None and _from.type == CardList.EQUIPS:
            src = _from.owner
            for c in cards:
                if c.is_card(YoumuPhantomCard):
                    src.maxlife -= 1
                    src.life = min(src.life+1, src.maxlife)

        if to is not None and to.type == CardList.EQUIPS:
            src = to.owner
            for c in cards:
                if c.is_card(YoumuPhantomCard):
                    src.maxlife += 1

        return arg

class IceWingSkill(ShieldSkill):
    pass

class IceWing(GenericAction):
    def __init__(self, act):
        assert isinstance(act, spellcard.SealingArray)
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True

@register_eh
class IceWingHandler(EventHandler):
    execute_before = ('RejectHandler', 'SaigyouBranchHandler')
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SealingArray):
            if act.target.has_skill(IceWingSkill):
                Game.getgame().process_action(IceWing(act))

        return act

class GrimoireSkill(TreatAsSkill, WeaponSkill):
    range = 1
    from .base import Card
    lookup_tbl = {
        Card.SPADE: Card.card_classes['SinsackCarnivalCard'], # again...
        Card.HEART: Card.card_classes['FeastCard'],
        Card.CLUB: Card.card_classes['MapCannonCard'],
        Card.DIAMOND: Card.card_classes['HarvestCard'],
    }
    del Card

    @property
    def treat_as(self):
        cl = self.associated_cards
        if not cl:
            from .definition import DummyCard
            return DummyCard
        return self.lookup_tbl[cl[0].suit]

    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        if not cl[0].resides_in.type in (CardList.HANDCARD, CardList.SHOWNCARD, CardList.EQUIPS):
            return False
        return True

@register_eh
class GrimoireHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire':
            act, v = arg
            if not isinstance(act, LaunchCard): return arg
            c = act.card
            if c.is_card(GrimoireSkill):
                src = act.source
                t = src.tags
                if not t['attack_num'] or t['turn_count'] <= t['grimoire_tag']:
                    return (act, False)
        elif evt_type == 'action_after' and isinstance(arg, LaunchCard):
            c = arg.card
            if c.is_card(GrimoireSkill):
                t = arg.source.tags
                t['attack_num'] -= 1
                t['grimoire_tag'] = t['turn_count']
        return arg
