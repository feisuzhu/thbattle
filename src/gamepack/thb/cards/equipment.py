# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from . import basic, spellcard
from ..actions import Damage, DrawCards, DropCardStage, DropCards, Fatetell, FatetellAction, ForEach
from ..actions import GenericAction, LaunchCard, MaxLifeChange, MigrateCardsTransaction, PlayerTurn
from ..actions import UserAction, migrate_cards, random_choose_card, register_eh, user_choose_cards
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from .base import Card, Skill, TreatAs, VirtualCard, t_None, t_OtherLessEqThanN, t_OtherOne
from game.autoenv import EventHandler, Game, GameError, user_input
from utils import CheckFailed, check, classmix


# -- code --
class WearEquipmentAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card
        target = self.target
        equips = target.equips
        g = Game.getgame()

        with MigrateCardsTransaction() as trans:
            for oc in equips:
                if oc.equipment_category == card.equipment_category:
                    migrate_cards([oc], g.deck.droppedcards, unwrap=True, trans=trans)
                    break
            migrate_cards([card], target.equips, trans=trans)

        return True


@register_eh
class EquipmentTransferHandler(EventHandler):
    interested = (
        'card_migration',
    )

    def handle(self, evt, args):
        if evt == 'card_migration':
            act, cards, _from, to = args
            if _from is not None and _from.type == 'equips':
                for c in cards:
                    try:
                        _from.owner.skills.remove(c.equipment_skill)
                    except ValueError:
                        pass

            if to is not None and to.type == 'equips':
                for c in cards:
                    to.owner.skills.append(c.equipment_skill)

        return args


class ShieldSkill(Skill):
    associated_action = None
    target = t_None


class OpticalCloakSkill(TreatAs, ShieldSkill):  # just a tag
    treat_as = Card.card_classes['GrazeCard']
    skill_category = ('equip', 'passive')

    def check(self):
        return False


class OpticalCloak(FatetellAction):
    # 光学迷彩
    def apply_action(self):
        g = Game.getgame()
        target = self.target
        ft = Fatetell(target, lambda card: card.suit in (Card.HEART, Card.DIAMOND))
        g.process_action(ft)
        self.fatetell_card = ft.card
        return bool(ft.succeeded)


@register_eh
class OpticalCloakHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        from .basic import BaseUseGraze
        if evt_type == 'action_apply' and isinstance(act, BaseUseGraze):
            tgt = act.target
            if not tgt.has_skill(OpticalCloakSkill): return act
            if act.card: return act

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g = Game.getgame()
            if g.process_action(OpticalCloak(tgt, tgt)):
                act.card = OpticalCloakSkill(tgt)

        return act


class MomijiShieldSkill(ShieldSkill):
    skill_category = ('equip', 'passive')


class MomijiShield(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source = self.target = act.target

    def apply_action(self):
        self.action.cancelled = True
        return True


@register_eh
class MomijiShieldHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('HouraiJewelHandler', )

    def handle(self, evt_type, act):
        from .basic import BaseAttack
        if not (evt_type == 'action_before' and isinstance(act, BaseAttack)): return act
        tgt = act.target
        if not tgt.has_skill(MomijiShieldSkill): return act
        if not act.associated_card.color == Card.BLACK: return act
        g = Game.getgame()
        g.process_action(MomijiShield(act))

        return act


class UFOSkill(Skill):
    associated_action = None
    skill_category = ('equip', 'passive')
    target = t_None


class GreenUFOSkill(UFOSkill):
    increment = 1


class RedUFOSkill(UFOSkill):
    increment = 1


@register_eh
class UFODistanceHandler(EventHandler):
    interested = ('calcdistance',)

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
    skill_category = ('equip', 'passive')
    target = t_None
    range = 3


class Roukanken(GenericAction):
    def __init__(self, act):
        assert isinstance(act, basic.BaseAttack)
        self.action = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        act = self.action
        target = act.target
        skills = target.skills
        for e in target.equips:
            s = e.equipment_skill
            if issubclass(s, ShieldSkill):
                skills.remove(s)

        try:
            rst = Game.getgame().process_action(act)
        finally:
            for card in target.equips:
                s = card.equipment_skill
                if issubclass(s, ShieldSkill):
                    target.has_skill(s) or skills.append(s)

        return rst


@register_eh
class RoukankenEffectHandler(EventHandler):
    interested = ('action_before',)
    execute_before = (
        'MomijiShieldHandler',
        'OpticalCloakHandler',
        'SaigyouBranchHandler',
        'HouraiJewelHandler',
        'SpearTheGungnirHandler',
        'HakuroukenHandler',
    )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            if act.cancelled:
                return act

            if hasattr(act, 'roukanken_tag'):
                return act

            act.roukanken_tag = True
            source = act.source
            if source.has_skill(RoukankenSkill):
                act = Roukanken(act)
                return act
        return act


class NenshaPhoneSkill(WeaponSkill):
    associated_action = None
    skill_category = ('equip', 'passive')
    target = t_None
    range = 4


class NenshaPhone(GenericAction):
    def apply_action(self):
        tgt = self.target

        cards = list(tgt.cards)[:2]
        g = Game.getgame()
        g.players.exclude(tgt).reveal(cards)
        migrate_cards(cards, tgt.showncards)

        return True


@register_eh
class NenshaPhoneHandler(EventHandler):
    interested = ('action_after',)

    def handle(self, evt_type, act):
        from .basic import BaseAttack
        if not evt_type == 'action_after': return act
        if not isinstance(act, BaseAttack): return act
        if not act.succeeded: return act
        src = act.source
        tgt = act.target
        if tgt.dead: return act
        if not tgt.cards: return act
        if not src.has_skill(NenshaPhoneSkill): return act
        if not user_input([src], ChooseOptionInputlet(self, (False, True))): return act
        g = Game.getgame()
        g.process_action(NenshaPhone(src, tgt))
        return act


class ElementalReactorSkill(WeaponSkill):
    associated_action = None
    skill_category = ('equip', 'passive')
    target = t_None
    range = 1


@register_eh
class ElementalReactorHandler(EventHandler):
    interested = ('action_stage_action', 'card_migration')
    execute_after = ('EquipmentTransferHandler', )

    def handle(self, evt_type, arg):
        if evt_type == 'action_stage_action':
            tgt = arg
            if not tgt.has_skill(ElementalReactorSkill): return arg
            basic.AttackCardHandler.set_freeattack(tgt)

        elif evt_type == 'card_migration':
            act, cards, _from, to = arg

            from .definition import ElementalReactorCard

            if _from is not None and _from.type == 'equips':
                src = _from.owner
                for c in cards:
                    if c.is_card(ElementalReactorCard):
                        basic.AttackCardHandler.cancel_freeattack(src)

        return arg


class GungnirSkill(TreatAs, WeaponSkill):
    target = t_OtherOne
    skill_category = ('equip', 'active')
    range = 3
    treat_as = Card.card_classes['AttackCard']  # arghhhhh, nasty circular references!

    def check(self):
        cl = self.associated_cards
        cat = ('cards', 'showncards')
        if not all(c.resides_in.type in cat for c in cl): return False
        return len(cl) == 2


class ScarletRhapsody(ForEach):
    action_cls = basic.Attack


class ScarletRhapsodySkill(WeaponSkill):
    range = 4
    associated_action = ScarletRhapsody
    category = ('skill', 'treat_as', 'basic')
    skill_category = ('equip', 'active')
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

            raw = VirtualCard.unwrap([card])
            check(all(r.resides_in in (tgt.cards, tgt.showncards) for r in raw))
            cards = set(tgt.cards) | set(tgt.showncards)
            check(cards <= set(raw))

            return True
        except CheckFailed:
            return False

    def is_card(self, cls):
        from ..cards import AttackCard
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

    @property
    def distance(self):
        try:
            return max(1, self.associated_cards[0].distance)
        except:
            return 1


class RepentanceStickSkill(WeaponSkill):
    range = 2
    skill_category = ('equip', 'passive')
    associated_action = None
    target = t_None


class RepentanceStick(GenericAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        catnames = ('cards', 'showncards', 'equips', 'fatetell')
        cats = [getattr(tgt, i) for i in catnames]

        l = []
        for i in xrange(2):
            if not (tgt.cards or tgt.showncards or tgt.equips or tgt.fatetell):
                break

            card = user_input(
                [src], ChoosePeerCardInputlet(self, tgt, catnames)
            )

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
    interested = ('action_before',)
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

                if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                    return act

                g.process_action(RepentanceStick(src, tgt))
                act.cancelled = True

        return act


class MaidenCostumeSkill(ShieldSkill):
    skill_category = ('equip', 'passive')


class MaidenCostumeEffect(spellcard.NonResponsiveInstantSpellCardAction):
    def apply_action(self):
        g = Game.getgame()
        g.process_action(Damage(source=self.source, target=self.target))
        return True


@register_eh
class MaidenCostumeHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('RejectHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SinsackCarnivalEffect):
            target = act.target
            if not act.cancelled and target.has_skill(MaidenCostumeSkill):
                act.cancelled = True
                nact = MaidenCostumeEffect(source=act.source, target=target)
                nact.associated_card = act.associated_card
                return nact
                # Game.getgame().process_action(nact)
        return act


class IbukiGourdSkill(RedUFOSkill):
    skill_category = ('equip', 'passive')
    increment = 0


@register_eh
class IbukiGourdHandler(EventHandler):
    interested = ('action_after', 'card_migration')
    execute_after = ('WineHandler', 'CiguateraHandler', )

    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, PlayerTurn):
            target = arg.target
            if target.has_skill(IbukiGourdSkill):
                g = Game.getgame()
                g.process_action(basic.Wine(target, target))

        elif evt_type == 'card_migration':
            from .definition import IbukiGourdCard
            act, cl, _from, to = arg

            if any(c.is_card(IbukiGourdCard) for c in cl):
                g = Game.getgame()

                for cl in (_from, to):
                    if cl.type == 'equips':
                        tgt = cl.owner
                        g.process_action(basic.Wine(tgt, tgt))

        return arg


class HouraiJewelAttack(basic.BaseAttack, spellcard.InstantSpellCardAction):
    def apply_action(self):
        g = Game.getgame()
        g.process_action(Damage(self.source, self.target))
        return True


class HouraiJewelSkill(WeaponSkill):
    associated_action = None
    skill_category = ('equip', 'passive')
    target = t_None
    range = 1


@register_eh
class HouraiJewelHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('RejectHandler', 'WineHandler')  # wine does not affect this.

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.Attack):
            src = act.source
            if not src.has_skill(HouraiJewelSkill): return act
            if isinstance(act, HouraiJewelAttack): return act
            if user_input([src], ChooseOptionInputlet(self, (False, True))):
                act.__class__ = classmix(HouraiJewelAttack, act.__class__)

        return act


class UmbrellaSkill(ShieldSkill):
    skill_category = ('equip', 'passive')


class UmbrellaEffect(GenericAction):
    def __init__(self, act, damage_act):
        self.source = self.target = damage_act.target
        self.action = act
        self.damage_act = damage_act

    def apply_action(self):
        self.damage_act.cancelled = True
        return True


@register_eh
class UmbrellaHandler(EventHandler):
    # 紫的阳伞
    interested = ('action_before',)
    execute_before = ('RejectHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            if not act.target.has_skill(UmbrellaSkill): return act
            g = Game.getgame()
            pact = g.action_stack[-1]

            if isinstance(pact, spellcard.SpellCardAction):
                Game.getgame().process_action(UmbrellaEffect(pact, act))

        return act


class SaigyouBranchSkill(TreatAs, ShieldSkill):
    treat_as = Card.card_classes['RejectCard']
    skill_category = ('equip', 'passive')

    def check(self):
        return False


class SaigyouBranch(FatetellAction):
    def __init__(self, source, act):
        self.source = source
        self.target = source
        self.act = act

    def apply_action(self):
        act = self.act
        src = self.source

        g = Game.getgame()
        ft = Fatetell(src, lambda card: 9 <= card.number <= 13)
        g.process_action(ft)
        if ft.succeeded:
            # rej = spellcard.LaunchReject(src, act, SaigyouBranchSkill(src))
            g.process_action(LaunchCard(
                src, [act.target], SaigyouBranchSkill(src), spellcard.Reject(src, act)
            ))
            return True
        else:
            return False


@register_eh
class SaigyouBranchHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('RejectHandler', )
    execute_after = ('HouraiJewelHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.SpellCardAction):
            tgt = act.target
            if not tgt.has_skill(SaigyouBranchSkill): return act
            if act.cancelled: return act
            if isinstance(act, spellcard.Reject): return act  # can't respond to reject

            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(SaigyouBranch(tgt, act))

        return act


class HakuroukenSkill(WeaponSkill):
    range = 2
    skill_category = ('equip', 'passive')
    associated_action = None
    target = t_None


class Hakurouken(GenericAction):
    card_usage = 'drop'

    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = user_choose_cards(self, tgt, ('cards', 'showncards'))
        g = Game.getgame()
        if cards:
            self.peer_action = 'drop'
            g.process_action(DropCards(tgt, cards))
        else:
            self.peer_action = 'draw'
            g.process_action(DrawCards(src, 1))

        return True

    def cond(self, cards):
        tgt = self.target
        return len(cards) == 1 and cards[0].resides_in in (tgt.cards, tgt.showncards)


@register_eh
class HakuroukenHandler(EventHandler):
    interested = ('action_before',)

    # BUG WITH OUT THIS LINE:
    # src equips [Gourd, Hakurouken], tgt drops Exinwan
    # then src drops Gourd,
    # but Attack.damage == 1, Wine tag preserved.
    execute_before = ('WineHandler', 'MomijiShieldHandler')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, basic.BaseAttack):
            if act.cancelled: return act
            src = act.source
            if not src.has_skill(HakuroukenSkill): return act
            card = act.associated_card
            if not card.color == Card.BLACK: return act

            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return act

            Game.getgame().process_action(Hakurouken(src, act.target))

        return act


class AyaRoundfan(GenericAction):
    def apply_action(self):
        src = self.source
        tgt = self.target

        g = Game.getgame()

        equip = user_input([src], ChoosePeerCardInputlet(self, tgt, ['equips']))
        if not equip:
            equip = random_choose_card([tgt.equips])
        g.process_action(DropCards(tgt, [equip]))
        self.card = equip

        return True


class AyaRoundfanSkill(WeaponSkill):
    range = 5
    skill_category = ('equip', 'passive')
    associated_action = None
    target = t_None


@register_eh
class AyaRoundfanHandler(EventHandler):
    interested = ('action_after',)
    card_usage = 'drop'

    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, Damage):
            if not act.succeeded: return act
            src, tgt = act.source, act.target
            if not (src and src.has_skill(AyaRoundfanSkill) and tgt.equips): return act

            g = Game.getgame()
            pa = g.action_stack[-1]
            if not isinstance(pa, basic.BaseAttack): return act

            cards = user_choose_cards(self, src, ('cards', 'showncards'))
            if not cards: return act
            g = Game.getgame()
            g.process_action(DropCards(src, cards))
            g.process_action(AyaRoundfan(src, tgt))

        return act

    def cond(self, cards):
        if not len(cards) == 1: return False
        return cards[0].resides_in.type in ('cards', 'showncards')


class Laevatein(UserAction):
    def apply_action(self):
        return True  # logic handled in LaevateinHandler


class LaevateinSkill(WeaponSkill):
    range = 3
    skill_category = ('equip', 'passive')
    associated_action = None
    target = t_None


@register_eh
class LaevateinHandler(EventHandler):
    interested = ('attack_aftergraze',)
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

            g = Game.getgame()
            cards = user_choose_cards(self, src, ('cards', 'showncards', 'equips'))
            if not cards:
                return arg

            g.process_action(DropCards(src, cards))
            g.process_action(Laevatein(src, tgt))
            return act, True

        return arg

    def cond(self, cards):
        if not len(cards) == 2: return False

        if any(c.resides_in.type not in (
            'cards', 'showncards', 'equips'
        ) for c in cards): return False

        from ..cards import LaevateinCard
        if any(
            c.resides_in.type == 'equips' and c.is_card(LaevateinCard)
            for c in cards
        ): return False

        return True


class DeathSickleSkill(WeaponSkill):
    range = 2
    skill_category = ('equip', 'passive')
    associated_action = None
    target = t_None


class DeathSickle(GenericAction):
    def __init__(self, act):
        self.action = act
        self.source, self.target = act.source, act.target

    def apply_action(self):
        self.action.amount += 1
        return True


@register_eh
class DeathSickleHandler(EventHandler):
    interested = ('action_before',)
    execute_before = ('WineHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            from .basic import Attack
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            src = act.source
            if not src or not src.has_skill(DeathSickleSkill): return act
            tgt = act.target
            if len(tgt.cards) + len(tgt.showncards) == 0:
                g.process_action(DeathSickle(act))

        return act


class KeystoneSkill(GreenUFOSkill):
    skill_category = ('equip', 'passive')
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
    interested = ('action_before',)
    execute_before = ('SaigyouBranchHandler', 'RejectHandler')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, spellcard.Sinsack):
            tgt = act.target
            if tgt.has_skill(KeystoneSkill):
                Game.getgame().process_action(Keystone(act))

        return act


class WitchBroomSkill(RedUFOSkill):
    skill_category = ('equip', 'passive')
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
                self.card = e
                ft.set_card(e)
                break
        else:
            raise GameError('Player has YinYangOrb skill but no equip!')

        return True


class YinYangOrbSkill(AccessoriesSkill):
    skill_category = ('equip', 'passive')


@register_eh
class YinYangOrbHandler(EventHandler):
    interested = ('fatetell',)
    execute_after = ('FatetellMalleateHandler', )

    def handle(self, evt_type, act):
        if evt_type == 'fatetell':
            tgt = act.target
            if not tgt.has_skill(YinYangOrbSkill): return act
            if not user_input([tgt], ChooseOptionInputlet(self, (False, True))):
                return act

            g = Game.getgame()
            g.process_action(YinYangOrb(act))

        return act


class SuwakoHatSkill(AccessoriesSkill):
    skill_category = ('equip', 'passive')


class SuwakoHatEffect(UserAction):
    def __init__(self, target, dcs):
        self.source = self.target = target
        self.dcs = dcs

    def apply_action(self):
        self.dcs.dropn = max(self.dcs.dropn - 2, 0)
        return True


@register_eh
class SuwakoHatHandler(EventHandler):
    interested = ('action_before',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(SuwakoHatSkill):
                Game.getgame().process_action(SuwakoHatEffect(tgt, act))

        return act


class YoumuPhantomSkill(AccessoriesSkill):
    skill_category = ('equip', 'passive')


class YoumuPhantomHeal(basic.Heal):
    pass


@register_eh
class YoumuPhantomHandler(EventHandler):
    interested = ('card_migration',)

    def handle(self, evt_type, arg):
        if not evt_type == 'card_migration': return arg

        act, cards, _from, to = arg

        from .definition import YoumuPhantomCard

        g = Game.getgame()

        if _from is not None and _from.type == 'equips':
            for c in cards:
                if c.is_card(YoumuPhantomCard):
                    owner = _from.owner

                    g.process_action(MaxLifeChange(owner, owner, -1))
                    if not owner.dead:
                        g.process_action(YoumuPhantomHeal(owner, owner))

        if to is not None and to.type == 'equips':
            for c in cards:
                if c.is_card(YoumuPhantomCard):
                    g.process_action(MaxLifeChange(to.owner, to.owner, 1))

        return arg


class IceWingSkill(AccessoriesSkill):
    skill_category = ('equip', 'passive')


class IceWing(GenericAction):
    def __init__(self, act):
        assert isinstance(act, (spellcard.SealingArray, spellcard.FrozenFrog))
        self.source = self.target = act.target
        self.action = act

    def apply_action(self):
        self.action.cancelled = True
        return True


@register_eh
class IceWingHandler(EventHandler):
    interested = ('action_before',)
    _effect_cls = spellcard.SealingArray, spellcard.FrozenFrog
    interested = (
        ('action_before', _effect_cls),
    )

    execute_before = ('RejectHandler', 'SaigyouBranchHandler')

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, self._effect_cls):
            if act.target.has_skill(IceWingSkill):
                Game.getgame().process_action(IceWing(act))

        return act


class GrimoireSkill(TreatAs, WeaponSkill):
    skill_category = ('equip', 'active')
    range = 1
    from .base import Card
    lookup_tbl = {
        Card.SPADE: Card.card_classes['SinsackCarnivalCard'],  # again...
        Card.HEART: Card.card_classes['FeastCard'],
        Card.CLUB: Card.card_classes['MapCannonCard'],
        Card.DIAMOND: Card.card_classes['HarvestCard'],
    }
    del Card

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
class GrimoireHandler(EventHandler):
    interested = ('action_after', 'action_can_fire')

    def handle(self, evt_type, arg):
        if evt_type == 'action_can_fire':
            act, v = arg
            if not isinstance(act, LaunchCard): return arg
            c = act.card
            if c.is_card(GrimoireSkill):
                src = act.source
                t = src.tags

                if t['turn_count'] <= t['grimoire_tag']:
                    return (act, False)

                if basic.AttackCardHandler.is_freeattack(act.source):
                    return arg

                if t['attack_num'] <= 0:
                    return (act, False)

        elif evt_type == 'action_after' and isinstance(arg, LaunchCard):
            c = arg.card
            if c.is_card(GrimoireSkill):
                t = arg.source.tags
                t['attack_num'] -= 1
                t['grimoire_tag'] = t['turn_count']

        return arg
