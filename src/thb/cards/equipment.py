# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import List, cast

# -- third party --
# -- own --
from game.base import GameError
from thb.actions import ActionLimitExceeded, Damage, DrawCards, DropCardStage
from thb.actions import DropCards, FatetellAction, FatetellStage, FinalizeStage, ForEach
from thb.actions import GenericAction, LaunchCard, MaxLifeChange, MigrateCardsTransaction, Reforge
from thb.actions import UserAction, VitalityLimitExceeded, detach_cards, migrate_cards
from thb.actions import random_choose_card, register_eh, ttags, user_choose_cards
from thb.cards import basic, spellcard
from thb.cards.base import Card, PhysicalCard, Skill, TreatAs, t_None
from thb.cards.base import t_OtherLessEqThanN, t_OtherOne
from thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from thb.mode import THBEventHandler
from utils.check import CheckFailed, check
from utils.misc import classmix


# -- code --
class WearEquipmentAction(UserAction):
    def apply_action(self):
        g = self.game
        card = self.associated_card

        from thb.cards.definition import EquipmentCard
        assert isinstance(card, EquipmentCard)

        tgt = self.target
        equips = tgt.equips

        self.action = 'wear'
        if card.equipment_category == 'weapon' and ttags(tgt)['vitality'] > 0:
            if g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                ttags(tgt)['vitality'] -= 1
                g.process_action(ReforgeWeapon(tgt, tgt, card))
                self.action = 'reforge'
                return True

        _s, _t, _c, rst = g.emit_event('wear_equipment', (self, tgt, card, 'default'))
        assert _s is self
        assert _t is tgt
        assert _c is card
        assert rst in ('default', 'handled')

        if rst == 'handled':
            return True

        for oc in list(equips):
            if oc.equipment_category == card.equipment_category:
                g.process_action(DropCards(tgt, tgt, [oc]))

        migrate_cards([card], tgt.equips)

        return True


class ReforgeWeapon(Reforge):
    pass


@register_eh
class EquipmentTransferHandler(THBEventHandler):
    interested = ['post_card_migration']

    def handle(self, evt, trans):
        if evt == 'post_card_migration':
            from thb.cards.definition import EquipmentCard
            assert isinstance(trans, MigrateCardsTransaction)
            for m in trans.movements:
                c = m.card
                if not isinstance(c, EquipmentCard):
                    continue

                if m.fr.type == 'equips':
                    owner = m.fr.owner
                    assert owner

                    try:
                        owner.skills.remove(c.equipment_skill)
                    except ValueError:
                        pass

                if m.to.type == 'equips':
                    owner = m.to.owner
                    assert owner
                    if c.equipment_skill:
                        owner.skills.append(c.equipment_skill)

        return trans


class ShieldSkill(Skill):
    associated_action = None
    target = t_None()


class OpticalCloakSkill(TreatAs, ShieldSkill):  # just a tag
    treat_as = PhysicalCard.classes['GrazeCard']
    skill_category = ['equip', 'passive']

    def check(self):
        return False


class OpticalCloak(FatetellAction):
    # 光学迷彩
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

    def fatetell_action(self, ft):
        self.fatetell_card = ft.card
        return bool(ft.succeeded)

    def fatetell_cond(self, card: Card):
        return card.color == Card.RED


@register_eh
class OpticalCloakHandler(THBEventHandler):
    interested = ['action_apply']
    execute_after = ['AssistedGrazeHandler']

    def handle(self, evt_type, act):
        from .basic import BaseUseGraze
        if evt_type == 'action_apply' and isinstance(act, BaseUseGraze):
            tgt = act.target
            if not tgt.has_skill(OpticalCloakSkill): return act
            if act.card: return act

            g = self.game

            if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            if g.process_action(OpticalCloak(tgt, tgt)):
                act.card = OpticalCloakSkill(tgt)

        return act


class MomijiShieldSkill(ShieldSkill):
    skill_category = ['equip', 'passive']


class MomijiShield(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source = self.target = act.target

    def apply_action(self):
        self.action.cancelled = True
        return True


@register_eh
class MomijiShieldHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['HouraiJewelHandler']

    def handle(self, evt_type, act):
        from .basic import BaseAttack
        if not (evt_type == 'action_before' and isinstance(act, BaseAttack)): return act
        tgt = act.target
        if not tgt.has_skill(MomijiShieldSkill): return act
        if not act.associated_card.color == Card.BLACK: return act
        g = self.game
        g.process_action(MomijiShield(act))

        return act


class UFOSkill(Skill):
    associated_action = None
    skill_category = ['equip', 'passive']
    target = t_None()


class GreenUFOSkill(UFOSkill):
    increment = 1


class RedUFOSkill(UFOSkill):
    increment = 1


@register_eh
class UFODistanceHandler(THBEventHandler):
    interested = ['calcdistance']

    def handle(self, evt_type, arg):
        if not evt_type == 'calcdistance': return arg

        src, card, dist = arg
        for s in src.skills:
            if not issubclass(s, RedUFOSkill): continue
            if not src.has_skill(s): continue
            incr = s.increment
            incr = incr(src) if callable(incr) else incr
            for p in dist:
                dist[p] -= incr

        for p in dist:
            for s in p.skills:
                if not issubclass(s, GreenUFOSkill): continue
                if not p.has_skill(s): continue
                incr = s.increment
                dist[p] += incr(p) if callable(incr) else incr

        return arg


class WeaponSkill(Skill):
    range = 1


class RoukankenSkill(WeaponSkill):
    associated_action = None
    skill_category = ['equip', 'passive']
    target = t_None()
    range = 3


class Roukanken(GenericAction):

    def apply_action(self):
        tgt = self.target

        skills = [s for s in tgt.skills if issubclass(s, ShieldSkill)]
        for s in skills:
            tgt.disable_skill(s, 'roukanken')

        return True


@register_eh
class RoukankenEffectHandler(THBEventHandler):
    interested = ['action_before', 'action_done']
    execute_before = [
        'MomijiShieldHandler',
        'OpticalCloakHandler',
        'SaigyouBranchHandler',
        'HouraiJewelHandler',
        'SpearTheGungnirHandler',
        'HakuroukenHandler',
        'FreakingPowerHandler',
        'ResonanceHandler'
    ]

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            cls = self.__class__
            g = self.game

            if act.cancelled:
                return act

            if act._[cls] == 'roukanken-processed':
                return act

            act._[cls] = 'roukanken-processed'

            src, tgt = act.source, act.target
            if src.has_skill(RoukankenSkill):
                g.process_action(Roukanken(src, tgt))

        if evt_type == 'action_done' and isinstance(act, basic.BaseAttack):
            act.target.reenable_skill('roukanken')

        return act


class NenshaPhoneSkill(WeaponSkill):
    associated_action = None
    skill_category = ['equip', 'passive']
    target = t_None()
    range = 4


class NenshaPhone(GenericAction):
    def apply_action(self):
        tgt = self.target

        cards = list(tgt.cards)[:2]
        g = self.game
        g.players.exclude(tgt).reveal(cards)
        migrate_cards(cards, tgt.showncards)

        return True


@register_eh
class NenshaPhoneHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            if not act.succeeded: return act
            g = self.game
            pa = g.action_stack[-1]
            if not isinstance(pa, basic.BaseAttack): return act

            src = act.source
            tgt = act.target
            if tgt.dead: return act
            if not tgt.cards: return act
            if not src.has_skill(NenshaPhoneSkill): return act
            if not g.user_input([src], ChooseOptionInputlet(self, (False, True))): return act
            g.process_action(NenshaPhone(src, tgt))

        return act


class ElementalReactorSkill(WeaponSkill):
    associated_action = None
    skill_category = ['equip', 'passive']
    target = t_None()
    range = 1


@register_eh
class ElementalReactorHandler(THBEventHandler):
    interested = ['action_stage_action', 'post_card_migration']
    execute_after = ['EquipmentTransferHandler']

    def handle(self, evt_type, arg):
        if evt_type == 'action_stage_action':
            tgt = arg
            if not tgt.has_skill(ElementalReactorSkill): return arg
            basic.AttackCardVitalityHandler.disable(tgt)

        elif evt_type == 'post_card_migration':
            trans = cast(MigrateCardsTransaction, arg)
            from .definition import ElementalReactorCard

            for m in trans.movements:
                if m.fr.type == 'equips' and m.card.is_card(ElementalReactorCard):
                    basic.AttackCardVitalityHandler.enable(m.fr.owner)

        return arg


class GungnirSkill(TreatAs, WeaponSkill):
    target = t_OtherOne()
    skill_category = ['equip', 'active']
    range = 3
    treat_as = PhysicalCard.classes['AttackCard']  # arghhhhh, nasty circular references!

    def check(self):
        cl = self.associated_cards
        cat = ('cards', 'showncards')
        if not all(c.resides_in.type in cat for c in cl): return False
        if not all(c.is_card(PhysicalCard) for c in cl): return False
        return len(cl) == 2


class ScarletRhapsody(ForEach):
    action_cls = basic.Attack


class ScarletRhapsodySkill(WeaponSkill):
    range = 4
    associated_action = ScarletRhapsody
    category = ['skill', 'treat_as', 'basic']
    skill_category = ['equip', 'active']
    target = t_OtherLessEqThanN(3)
    usage = 'launch'

    def check(self):
        try:
            cl = self.associated_cards
            check(len(cl) == 1)
            card = cl[0]
            from .definition import AttackCard
            check(card.is_card(AttackCard))
            tgt = card.resides_in.owner
            check(card.is_card(PhysicalCard))

            check(card.resides_in in (tgt.cards, tgt.showncards))
            check(card in set(tgt.cards) or card in set(tgt.showncards))

            check(set(tgt.cards) | set(tgt.showncards) == set([card]))

            return True
        except CheckFailed:
            return False

    def is_card(self, cls):
        from thb.cards.definition import AttackCard
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

    @property
    def distance(self):
        cl = self.associated_cards
        if not cl:
            return 1
        c = cl[0]
        return max(1, getattr(c, 'distance', 1))


class RepentanceStickSkill(WeaponSkill):
    range = 2
    skill_category = ['equip', 'passive']
    associated_action = None
    target = t_None()


class RepentanceStick(GenericAction):
    def apply_action(self) -> bool:
        src, tgt = self.source, self.target
        g = self.game

        catnames = ('cards', 'showncards', 'equips', 'fatetell')
        cats = [getattr(tgt, i) for i in catnames]

        l: List[PhysicalCard] = []
        for i in range(2):
            if not (tgt.cards or tgt.showncards or tgt.equips or tgt.fatetell):
                break

            card = g.user_input(
                [src], ChoosePeerCardInputlet(self, tgt, catnames)
            )

            if not card:
                card = random_choose_card(g, cats)
            if card:
                l.append(card)
                g.players.exclude(tgt).player.reveal(card)
                g.process_action(DropCards(src, tgt, [card]))

        self.cards = l
        return True


@register_eh
class RepentanceStickHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['WineHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if act.cancelled: return act
            src, tgt = act.source, act.target
            if src and src.has_skill(RepentanceStickSkill):
                g = self.game
                pa = g.action_stack[-1]
                if not isinstance(pa, basic.BaseAttack): return act
                if not (tgt.cards or tgt.showncards or tgt.equips or tgt.fatetell):
                    return act

                if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                    return act

                g.process_action(RepentanceStick(src, tgt))
                act.cancelled = True

        return act


class IbukiGourdSkill(RedUFOSkill):
    skill_category = ['equip', 'passive']
    increment = 0


@register_eh
class IbukiGourdHandler(THBEventHandler):
    interested = ['action_apply', 'action_after', 'post_card_migration']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            src = act.source
            if not src: return act
            if not src.has_skill(IbukiGourdSkill): return act

            g = self.game
            ttags(src)['ibukigourd_did_damage'] = True

        elif evt_type == 'action_apply' and isinstance(act, FinalizeStage):
            tgt = act.target
            if not tgt.has_skill(IbukiGourdSkill): return act

            g = self.game
            if ttags(tgt)['ibukigourd_did_damage']: return act

            g.process_action(basic.Wine(tgt, tgt))

        elif evt_type == 'post_card_migration':
            from .definition import IbukiGourdCard
            trans = cast(MigrateCardsTransaction, act)

            for m in trans.movements:
                if m.card.is_card(IbukiGourdCard) and m.to.type == 'equips':
                    assert m.to.owner
                    tgt = m.to.owner
                    g = self.game
                    g.process_action(basic.Wine(tgt, tgt))

        return act


class HouraiJewelAttack(basic.BaseAttack, spellcard.InstantSpellCardAction):
    def apply_action(self):
        g = self.game
        g.process_action(Damage(self.source, self.target))
        return True


class HouraiJewelSkill(WeaponSkill):
    associated_action = None
    skill_category = ['equip', 'passive']
    target = t_None()
    range = 1


@register_eh
class HouraiJewelHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['RejectHandler', 'WineHandler']  # wine does not affect this.

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.Attack):
            src = act.source
            if not src.has_skill(HouraiJewelSkill): return act
            if isinstance(act, HouraiJewelAttack): return act
            g = self.game
            if g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                act.__class__ = classmix(HouraiJewelAttack, act.__class__)

        return act


class UmbrellaSkill(ShieldSkill):
    skill_category = ['equip', 'passive']


class UmbrellaEffect(GenericAction):
    def __init__(self, act, damage_act):
        self.source = self.target = damage_act.target
        self.action = act
        self.damage_act = damage_act

    def apply_action(self):
        self.damage_act.cancelled = True
        return True


@register_eh
class UmbrellaHandler(THBEventHandler):
    # 紫的阳伞
    interested = ['action_before']
    execute_before = ['RejectHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if not act.target.has_skill(UmbrellaSkill): return act
            g = self.game
            pact = g.action_stack[-1]

            if isinstance(pact, spellcard.SpellCardAction):
                self.game.process_action(UmbrellaEffect(pact, act))

        return act


class MaidenCostume(TreatAs, ShieldSkill):
    treat_as = PhysicalCard.classes['RejectCard']
    skill_category = ['equip', 'passive']

    def check(self):
        return False


class MaidenCostumeAction(FatetellAction):
    def __init__(self, source, act):
        self.source = source
        self.target = source
        self.fatetell_target = source
        self.act = act

    def fatetell_action(self, ft):
        act = self.act
        src = self.source

        g = self.game
        if ft.succeeded:
            # rej = spellcard.LaunchReject(src, act, SaigyouBranchSkill(src))
            g.process_action(LaunchCard(
                src, [act.target], MaidenCostume(src), spellcard.Reject(src, act)
            ))
            return True
        else:
            return False

    def fatetell_cond(self, c: Card):
        return 9 <= c.number <= 13


@register_eh
class MaidenCostumeHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['RejectHandler']
    execute_after = ['HouraiJewelHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SpellCardAction):
            tgt = act.target
            if not tgt.has_skill(MaidenCostume): return act
            if act.cancelled: return act
            if isinstance(act, spellcard.Reject): return act  # can't respond to reject
            g = self.game
            if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            self.game.process_action(MaidenCostumeAction(tgt, act))

        return act


class HakuroukenSkill(WeaponSkill):
    range = 2
    skill_category = ['equip', 'passive']
    associated_action = None
    target = t_None()


class Hakurouken(GenericAction):
    card_usage = 'drop'

    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        g = self.game
        if cards:
            self.peer_action = 'drop'
            g.process_action(DropCards(src, tgt, cards))
        else:
            self.peer_action = 'draw'
            g.process_action(DrawCards(src, 1))

        return True

    def cond(self, cards):
        return len(cards) == 1 and not cards[0].is_card(Skill)


@register_eh
class HakuroukenHandler(THBEventHandler):
    interested = ['action_before']

    # BUG WITH OUT THIS LINE:
    # src equips [Gourd, Hakurouken], tgt drops Exinwan
    # then src drops Gourd,
    # but Attack.damage == 1, Wine tag preserved.
    execute_before = ['WineHandler', 'MomijiShieldHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            if act.cancelled: return act
            src = act.source
            if not src.has_skill(HakuroukenSkill): return act
            card = act.associated_card
            if not card.suit == Card.CLUB: return act

            g = self.game
            if not g.user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(Hakurouken(src, act.target))

        return act


class AyaRoundfan(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = self.game

        equip = g.user_input([src], ChoosePeerCardInputlet(self, tgt, ['equips']))
        equip = equip or random_choose_card(g, [tgt.equips])
        g.process_action(DropCards(src, tgt, [equip]))
        self.card = equip

        return True

    def is_valid(self):
        # Proton 2015/4/2 0:26:51
        # 小爱打幽香，打中以后，弃丸子发动团扇
        # Proton 2015/4/2 0:26:59
        # 然后弃了自己的装备
        # Proton 2015/4/2 0:27:25
        # 发动了于是又弃了幽香的装备
        # Proton 2015/4/2 0:27:41
        # 发动了小小军势
        # Proton 2015/4/2 0:28:02
        # 这时候针妙丸又来了一发，幽香卒
        # 0:28:19
        # 八咫乌鸦 2015/4/2 0:28:19
        # 喜闻乐见的插入结算
        # Proton 2015/4/2 0:28:49
        # 嗯 然后就回到了团扇的效果
        # Proton 2015/4/2 0:29:08
        # 团扇弃置cost把对面弃死了啊！
        # Proton 2015/4/2 0:29:38
        # 然后后半段效果都假设是对面还活着
        # Proton 2015/4/2 0:29:44
        # 崩

        # 所以加上这个
        return self.target.equips


class AyaRoundfanSkill(WeaponSkill):
    range = 5
    skill_category = ['equip', 'passive']
    associated_action = None
    target = t_None()


@register_eh
class AyaRoundfanHandler(THBEventHandler):
    interested = ['action_after']
    execute_after = ['DyingHandler']
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            if not act.succeeded: return act
            src, tgt = act.source, act.target
            if not (src and src.has_skill(AyaRoundfanSkill) and tgt.equips): return act

            g = self.game
            pa = g.action_stack[-1]
            if not isinstance(pa, basic.BaseAttack): return act

            cards = user_choose_cards(self, src, ('cards', 'showncards'))
            if not cards: return act
            g.process_action(DropCards(src, src, cards))
            g.process_action(AyaRoundfan(src, tgt))

        return act

    def cond(self, cards):
        if not len(cards) == 1 or cards[0].is_card(Skill):
            return False

        return cards[0].resides_in.type in ('cards', 'showncards')


class Laevatein(UserAction):
    def apply_action(self):
        return True  # logic handled in LaevateinHandler


class LaevateinSkill(WeaponSkill):
    range = 3
    skill_category = ['equip', 'passive']
    associated_action = None
    target = t_None()


@register_eh
class LaevateinHandler(THBEventHandler):
    interested = ['attack_aftergraze']
    card_usage = 'drop'

    def handle(self, evt_type, arg):
        if evt_type == 'attack_aftergraze':
            act, succeed = arg
            assert isinstance(act, basic.BaseAttack)
            if succeed:
                return arg

            src = act.source
            tgt = act.target
            if not src or not src.has_skill(LaevateinSkill):
                return arg

            g = self.game
            cards = user_choose_cards(self, src, ('cards', 'showncards', 'equips'))
            if not cards:
                return arg

            g.process_action(DropCards(src, src, cards))
            g.process_action(Laevatein(src, tgt))
            return act, True

        return arg

    def cond(self, cards):
        if not len(cards) == 2: return False

        from thb.cards.definition import LaevateinCard
        for c in cards:
            t = c.resides_in.type
            if t not in ('cards', 'showncards', 'equips'):
                return False
            elif t == 'equips' and c.is_card(LaevateinCard):
                return False
            elif c.is_card(Skill):
                return False

        return True


class DeathSickleSkill(WeaponSkill):
    range = 2
    skill_category = ['equip', 'passive']
    associated_action = None
    target = t_None()


class DeathSickle(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source, self.target = act.source, act.target

    def apply_action(self):
        self.action.amount += 1
        return True


@register_eh
class DeathSickleHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['WineHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            from .basic import Attack
            g = self.game
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            src = act.source
            if not src or not src.has_skill(DeathSickleSkill): return act
            tgt = act.target
            if len(tgt.cards) + len(tgt.showncards) == 0:
                g.process_action(DeathSickle(act))

        return act


class KeystoneSkill(GreenUFOSkill):
    skill_category = ['equip', 'passive']
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
class KeystoneHandler(THBEventHandler):
    interested = ['action_before']
    execute_before = ['SaigyouBranchHandler', 'RejectHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.Sinsack):
            tgt = act.target
            if tgt.has_skill(KeystoneSkill):
                self.game.process_action(Keystone(act))

        return act


class WitchBroomSkill(RedUFOSkill):
    skill_category = ['equip', 'passive']
    increment = 2


class AccessoriesSkill(Skill):
    associated_action = None
    target = t_None()


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
                with MigrateCardsTransaction(self) as trans:
                    migrate_cards([ft.card], tgt.cards, unwrap=True, trans=trans)
                    migrate_cards([e], tgt.special, trans=trans)

                detach_cards([e], trans=trans)
                self.card = e
                ft.set_card(e, self)

                break
        else:
            raise GameError('Player has YinYangOrb skill but no equip!')

        return True


class YinYangOrbSkill(AccessoriesSkill):
    skill_category = ['equip', 'passive']


@register_eh
class YinYangOrbHandler(THBEventHandler):
    interested = ['fatetell']
    execute_after = ['FatetellMalleateHandler']

    def handle(self, evt_type, act):
        if evt_type == 'fatetell':
            g = self.game
            tgt = act.target
            if not tgt.has_skill(YinYangOrbSkill): return act
            if not g.user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g.process_action(YinYangOrb(act))

        return act


class SuwakoHatSkill(AccessoriesSkill):
    skill_category = ['equip', 'passive']


class SuwakoHatEffect(UserAction):
    def __init__(self, target, dcs):
        self.source = self.target = target
        self.dcs = dcs

    def apply_action(self):
        self.dcs.dropn = max(self.dcs.dropn - 2, 0)
        return True


@register_eh
class SuwakoHatHandler(THBEventHandler):
    interested = ['action_before']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(SuwakoHatSkill):
                self.game.process_action(SuwakoHatEffect(tgt, act))

        return act


class YoumuPhantomSkill(AccessoriesSkill):
    skill_category = ['equip', 'passive']


class YoumuPhantomHeal(basic.Heal):
    pass


@register_eh
class YoumuPhantomHandler(THBEventHandler):
    interested = ['post_card_migration']

    def handle(self, evt_type, arg):
        if not evt_type == 'post_card_migration': return arg

        from .definition import YoumuPhantomCard
        trans = cast(MigrateCardsTransaction, arg)
        g = self.game

        for m in trans.movements:
            if not m.card.is_card(YoumuPhantomCard):
                continue

            if m.fr.type == 'equips':
                tgt = m.fr.owner
                assert tgt
                g.process_action(MaxLifeChange(tgt, tgt, -1))
                if not tgt.dead:
                    g.process_action(YoumuPhantomHeal(tgt, tgt))

            if m.to.type == 'equips':
                tgt = m.to.owner
                assert tgt
                g.process_action(MaxLifeChange(tgt, tgt, 1))

        return arg


class IceWingSkill(RedUFOSkill):
    skill_category = ['equip', 'passive']
    increment = 1


class IceWing(GenericAction):
    def __init__(self, act):
        assert isinstance(act, (spellcard.SealingArray, spellcard.FrozenFrog))
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True


@register_eh
class IceWingHandler(THBEventHandler):
    interested = ['action_before']
    _effect_cls = spellcard.SealingArray, spellcard.FrozenFrog

    execute_before = ['RejectHandler', 'SaigyouBranchHandler']

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, self._effect_cls):
            if act.target.has_skill(IceWingSkill):
                self.game.process_action(IceWing(act))

        return act


class GrimoireSkill(TreatAs, WeaponSkill):
    skill_category = ['equip', 'active']
    range = 1
    lookup_tbl = {
        Card.SPADE: PhysicalCard.classes['DemonParadeCard'],  # again...
        Card.HEART: PhysicalCard.classes['FeastCard'],
        Card.CLUB: PhysicalCard.classes['MapCannonCard'],
        Card.DIAMOND: PhysicalCard.classes['HarvestCard'],
    }

    @property
    def treat_as(self):
        cl = self.associated_cards
        if not (cl and cl[0].suit):
            from .base import DummyCard
            return DummyCard
        return self.lookup_tbl[cl[0].suit]

    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        if not cl[0].resides_in.type in ('cards', 'showncards', 'equips'):
            return False
        if not cl[0].suit: return False
        return True


@register_eh
class GrimoireHandler(THBEventHandler):
    interested = ['action_after', 'action_shootdown']

    def handle(self, evt_type, act):
        if evt_type == 'action_shootdown':
            if not isinstance(act, LaunchCard): return act
            c = act.card
            if c.is_card(GrimoireSkill):
                src = act.source
                t = ttags(src)

                if t['grimoire_tag']:
                    raise ActionLimitExceeded

                if t['vitality'] <= 0:
                    raise VitalityLimitExceeded

        elif evt_type == 'action_after' and isinstance(act, LaunchCard):
            c = act.card
            if c.is_card(GrimoireSkill):
                src = act.source
                t = ttags(src)
                t['vitality'] -= 1
                t['grimoire_tag'] = True

        return act


class SinsackHatAction(FatetellAction):
    def __init__(self, source, target, hat_card):
        self.source = source
        self.target = target
        self.hat_card = hat_card
        self.fatetell_target = target

    def fatetell_action(self, ft):
        if not ft.succeeded:
            return False

        g = self.game
        tgt, c = self.target, self.hat_card
        g.process_action(spellcard.SinsackDamage(None, tgt, amount=2))
        migrate_cards([c], tgt.cards, unwrap=True)
        return True

    def fatetell_cond(self, c: Card):
        return c.suit == Card.SPADE and 1 <= c.number <= 8


class SinsackHat(ShieldSkill):
    skill_category = ['equip', 'passive']


@register_eh
class SinsackHatHandler(THBEventHandler):
    interested = ['action_after']

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, FatetellStage):
            tgt = act.target
            g = self.game
            from .definition import SinsackHatCard
            for c in list(tgt.equips):
                if not c.is_card(SinsackHatCard):
                    continue

                g.process_action(SinsackHatAction(tgt, tgt, c))
                return act

        return act
