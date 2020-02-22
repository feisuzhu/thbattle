# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Any, List, Sequence, Tuple, Type

# -- third party --
# -- own --
from thb.cards.base import Card, PhysicalCard, Skill, t_All, t_AllInclusive, t_None, t_One
from thb.cards.base import t_OtherLessEqThanN, t_OtherOne, t_Self
from thb.characters.base import Character


# -- code --
def physical_card(cls: Type[PhysicalCard]):
    assert issubclass(cls, PhysicalCard)
    for a in ('associated_action', 'target', 'category'):
        assert hasattr(cls, a), (cls, a)
    PhysicalCard.classes[cls.__name__] = cls
    return cls


# ==================================================
from thb.cards import basic


class BasicCard(PhysicalCard):
    pass


@physical_card
class AttackCard(BasicCard):
    associated_action = basic.Attack
    target = t_OtherOne
    category = ['basic']
    distance = 1


@physical_card
class GrazeCard(BasicCard):
    associated_action = None
    target = t_None
    category = ['basic']


@physical_card
class HealCard(BasicCard):
    associated_action = basic.Heal
    target = t_Self
    category = ['basic']


@physical_card
class WineCard(BasicCard):
    associated_action = basic.Wine
    target = t_Self
    category = ['basic']


@physical_card
class ExinwanCard(BasicCard):
    associated_action = basic.Exinwan
    target = t_Self
    category = ['basic']


# --------------------------------------------------
from thb.cards import spellcard


class SpellcardCard(PhysicalCard):
    pass


@physical_card
class DemolitionCard(SpellcardCard):
    associated_action = spellcard.Demolition
    target = t_OtherOne
    category = ['spellcard', 'instant_spellcard']


@physical_card
class RejectCard(SpellcardCard):
    associated_action = None
    target = t_None
    category = ['spellcard', 'instant_spellcard']


@physical_card
class SealingArrayCard(SpellcardCard):
    associated_action = spellcard.DelayedLaunchCard
    target = t_OtherOne
    category = ['spellcard', 'delayed_spellcard']
    delayed_action = spellcard.SealingArray
    no_drop = True


@physical_card
class FrozenFrogCard(SpellcardCard):
    associated_action = spellcard.DelayedLaunchCard
    target = t_OtherOne
    category = ['spellcard', 'delayed_spellcard']
    distance = 1
    delayed_action = spellcard.FrozenFrog
    no_drop = True


@physical_card
class NazrinRodCard(SpellcardCard):
    associated_action = spellcard.NazrinRod
    target = t_Self
    category = ['spellcard', 'instant_spellcard']


@physical_card
class SinsackCard(SpellcardCard):
    associated_action = spellcard.DelayedLaunchCard
    target = t_Self
    category = ['spellcard', 'delayed_spellcard']
    delayed_action = spellcard.Sinsack
    no_drop = True


@physical_card
class YukariDimensionCard(SpellcardCard):
    associated_action = spellcard.YukariDimension
    target = t_OtherOne
    category = ['spellcard', 'instant_spellcard']
    distance = 1


@physical_card
class DuelCard(SpellcardCard):
    associated_action = spellcard.Duel
    target = t_OtherOne
    category = ['spellcard', 'instant_spellcard']


@physical_card
class MapCannonCard(SpellcardCard):
    associated_action = spellcard.MapCannon
    target = t_All
    category = ['group_effect', 'spellcard', 'instant_spellcard']


@physical_card
class DemonParadeCard(SpellcardCard):
    associated_action = spellcard.DemonParade
    target = t_All
    category = ['group_effect', 'spellcard', 'instant_spellcard']


@physical_card
class FeastCard(SpellcardCard):
    associated_action = spellcard.Feast
    target = t_AllInclusive
    category = ['group_effect', 'spellcard', 'instant_spellcard']


@physical_card
class HarvestCard(SpellcardCard):
    associated_action = spellcard.Harvest
    target = t_AllInclusive
    category = ['group_effect', 'spellcard', 'instant_spellcard']


@physical_card
class DollControlCard(SpellcardCard):
    associated_action = spellcard.DollControl

    def t_DollControl(self: Any, g: Any, src: Character, tl: Sequence[Character]) -> Tuple[List[Character], bool]:
        if not tl: return ([], False)
        tl = [ch for ch in tl if not ch.dead]
        while tl and src is tl[0]:
            del tl[0]
        return (tl[:2], len(tl) >= 2)

    target = t_DollControl
    category = ['spellcard', 'instant_spellcard']
    del t_DollControl


@physical_card
class DonationBoxCard(SpellcardCard):
    associated_action = spellcard.DonationBox
    target = t_OtherLessEqThanN(2)
    category = ['spellcard', 'instant_spellcard']


# --------------------------------------------------
from thb.cards import equipment


class EquipmentCard(PhysicalCard):
    equipment_skill: Type[Skill]
    equipment_category: str


@physical_card
class MomijiShieldCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'shield']
    equipment_skill = equipment.MomijiShieldSkill
    equipment_category = 'shield'


@physical_card
class OpticalCloakCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'shield']
    equipment_skill = equipment.OpticalCloakSkill
    equipment_category = 'shield'


@physical_card
class GreenUFOCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'greenufo']
    equipment_skill = equipment.GreenUFOSkill
    equipment_category = 'greenufo'


@physical_card
class RedUFOCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'redufo']
    equipment_skill = equipment.RedUFOSkill
    equipment_category = 'redufo'


@physical_card
class HakuroukenCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.HakuroukenSkill
    equipment_category = 'weapon'


@physical_card
class ElementalReactorCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.ElementalReactorSkill
    equipment_category = 'weapon'


@physical_card
class UmbrellaCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'shield']
    equipment_skill = equipment.UmbrellaSkill
    equipment_category = 'shield'


@physical_card
class RoukankenCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.RoukankenSkill
    equipment_category = 'weapon'


@physical_card
class GungnirCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.GungnirSkill
    equipment_category = 'weapon'


@physical_card
class LaevateinCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.LaevateinSkill
    equipment_category = 'weapon'


@physical_card
class NenshaPhoneCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.NenshaPhoneSkill
    equipment_category = 'weapon'


@physical_card
class RepentanceStickCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.RepentanceStickSkill
    equipment_category = 'weapon'


@physical_card
class SinsackHatCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_One
    category = ['equipment', 'shield']
    equipment_skill = equipment.SinsackHat
    equipment_category = 'shield'
    distance = 2


@physical_card
class IbukiGourdCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'redufo']
    equipment_skill = equipment.IbukiGourdSkill
    equipment_category = 'redufo'


@physical_card
class HouraiJewelCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.HouraiJewelSkill
    equipment_category = 'weapon'


@physical_card
class MaidenCostumeCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'shield']
    equipment_skill = equipment.MaidenCostume
    equipment_category = 'shield'


@physical_card
class AyaRoundfanCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.AyaRoundfanSkill
    equipment_category = 'weapon'


@physical_card
class ScarletRhapsodyCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.ScarletRhapsodySkill
    equipment_category = 'weapon'


@physical_card
class DeathSickleCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.DeathSickleSkill
    equipment_category = 'weapon'


@physical_card
class KeystoneCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'greenufo']
    equipment_skill = equipment.KeystoneSkill
    equipment_category = 'greenufo'


@physical_card
class WitchBroomCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'redufo']
    equipment_skill = equipment.WitchBroomSkill
    equipment_category = 'redufo'


@physical_card
class YinYangOrbCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'accessories']
    equipment_skill = equipment.YinYangOrbSkill
    equipment_category = 'accessories'


@physical_card
class SuwakoHatCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'accessories']
    equipment_skill = equipment.SuwakoHatSkill
    equipment_category = 'accessories'


@physical_card
class YoumuPhantomCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'accessories']
    equipment_skill = equipment.YoumuPhantomSkill
    equipment_category = 'accessories'


@physical_card
class IceWingCard(PhysicalCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'redufo']
    equipment_skill = equipment.IceWingSkill
    equipment_category = 'redufo'


@physical_card
class GrimoireCard(EquipmentCard):
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ['equipment', 'weapon']
    equipment_skill = equipment.GrimoireSkill
    equipment_category = 'weapon'


# --------------------------------------------------
from thb.cards import debug


@physical_card
class MassiveDamageCard(PhysicalCard):
    associated_action = debug.MassiveDamage

    @staticmethod
    def target(g, source, tl):
        return tl, True

    category = ['debug']


# ==================================================
SPADE, HEART, CLUB, DIAMOND = Card.SPADE, Card.HEART, Card.CLUB, Card.DIAMOND
A, J, Q, K = 1, 11, 12, 13

card_definition = [
    # ======= Spade =======
    (SinsackCard, SPADE, A),
    (DeathSickleCard, SPADE, 2),
    (RepentanceStickCard, SPADE, 3),
    (RoukankenCard, SPADE, 4),
    (HakuroukenCard, SPADE, 5),
    (GungnirCard, SPADE, 6),
    (DemonParadeCard, SPADE, 7),
    (DemonParadeCard, SPADE, 8),
    (SealingArrayCard, SPADE, 9),
    (SealingArrayCard, SPADE, 10),
    (AttackCard, SPADE, J),
    (AttackCard, SPADE, Q),
    (KeystoneCard, SPADE, K),

    (DuelCard, SPADE, A),
    (RejectCard, SPADE, 2),
    (AttackCard, SPADE, 3),
    (AttackCard, SPADE, 4),
    (YukariDimensionCard, SPADE, 5),
    (YukariDimensionCard, SPADE, 6),
    (AttackCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (WineCard, SPADE, 9),
    (AttackCard, SPADE, 10),
    (AttackCard, SPADE, J),
    (RejectCard, SPADE, Q),
    (WitchBroomCard, SPADE, K),

    (DonationBoxCard, SPADE, A),
    (OpticalCloakCard, SPADE, 2),
    (DemolitionCard, SPADE, 3),
    (DemolitionCard, SPADE, 4),
    (AttackCard, SPADE, 8),
    (IceWingCard, SPADE, 9),
    (AttackCard, SPADE, 10),
    (DonationBoxCard, SPADE, J),
    (AttackCard, SPADE, Q),
    (YinYangOrbCard, SPADE, K),

    # ======= Heart =======
    (FeastCard, HEART, A),
    (SinsackHatCard, HEART, 2),
    (HarvestCard, HEART, 3),
    (HarvestCard, HEART, 4),
    (AyaRoundfanCard, HEART, 5),
    (AttackCard, HEART, 6),
    (NazrinRodCard, HEART, 7),
    (NazrinRodCard, HEART, 8),
    (NazrinRodCard, HEART, 9),
    (SealingArrayCard, HEART, 10),
    (AttackCard, HEART, J),
    (DemolitionCard, HEART, Q),
    (GreenUFOCard, HEART, K),

    (MapCannonCard, HEART, A),
    (RejectCard, HEART, 2),
    (HealCard, HEART, 3),
    (HealCard, HEART, 4),
    (HealCard, HEART, 5),
    (HealCard, HEART, 6),
    (HealCard, HEART, 7),
    (HealCard, HEART, 8),
    (HealCard, HEART, 9),
    (AttackCard, HEART, 10),
    (AttackCard, HEART, J),
    (AttackCard, HEART, Q),
    (RejectCard, HEART, K),

    (SinsackCard, HEART, A),
    (GrazeCard, HEART, 2),
    (GrazeCard, HEART, 3),
    (GrazeCard, HEART, 4),
    (HealCard, HEART, 8),
    (GrazeCard, HEART, 9),
    (GrazeCard, HEART, 10),
    (GrazeCard, HEART, J),
    (GrazeCard, HEART, Q),
    (YinYangOrbCard, HEART, K),

    # ======= Club =======
    (SuwakoHatCard, CLUB, A),
    (MomijiShieldCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (DemolitionCard, CLUB, 4),
    (AttackCard, CLUB, 5),
    (AttackCard, CLUB, 6),
    (DemonParadeCard, CLUB, 7),
    (AttackCard, CLUB, 8),
    (WineCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (ExinwanCard, CLUB, Q),
    (GreenUFOCard, CLUB, K),

    (DuelCard, CLUB, A),
    (AttackCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (AttackCard, CLUB, 4),
    (FrozenFrogCard, CLUB, 5),
    (FrozenFrogCard, CLUB, 6),
    (AttackCard, CLUB, 7),
    (DemolitionCard, CLUB, 8),
    (WineCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (RejectCard, CLUB, Q),
    (RedUFOCard, CLUB, K),

    (YoumuPhantomCard, CLUB, A),
    (UmbrellaCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (AttackCard, CLUB, 4),
    (AttackCard, CLUB, 8),
    (IbukiGourdCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (MaidenCostumeCard, CLUB, Q),
    (DollControlCard, CLUB, K),

    # ======= Diamond =======
    (ElementalReactorCard, DIAMOND, A),
    (GrazeCard, DIAMOND, 2),
    (GrazeCard, DIAMOND, 3),
    (GrazeCard, DIAMOND, 4),
    (ScarletRhapsodyCard, DIAMOND, 5),
    (GrazeCard, DIAMOND, 6),
    (GrazeCard, DIAMOND, 7),
    (GrazeCard, DIAMOND, 8),
    (GrazeCard, DIAMOND, 9),
    (NenshaPhoneCard, DIAMOND, 10),
    (LaevateinCard, DIAMOND, J),
    (GrimoireCard, DIAMOND, Q),
    (GreenUFOCard, DIAMOND, K),

    (DuelCard, DIAMOND, A),
    (GrazeCard, DIAMOND, 2),
    (HealCard, DIAMOND, 3),
    (HealCard, DIAMOND, 4),
    (YukariDimensionCard, DIAMOND, 5),
    (YukariDimensionCard, DIAMOND, 6),
    (AttackCard, DIAMOND, 7),
    (AttackCard, DIAMOND, 8),
    (WineCard, DIAMOND, 9),
    (AttackCard, DIAMOND, 10),
    (ExinwanCard, DIAMOND, J),
    (RejectCard, DIAMOND, Q),
    (RedUFOCard, DIAMOND, K),

    (HouraiJewelCard, DIAMOND, A),
    (GrazeCard, DIAMOND, 2),
    (AttackCard, DIAMOND, 3),
    (AttackCard, DIAMOND, 4),
    (GrazeCard, DIAMOND, 8),
    (WineCard, DIAMOND, 9),
    (GrazeCard, DIAMOND, 10),
    (GrazeCard, DIAMOND, J),
    (HealCard, DIAMOND, Q),
    (DollControlCard, DIAMOND, K),
]

# ANCHOR(card)
card_definition = [
] * 1000 or card_definition


kof_card_definition = [
    # ======= Spade =======
    (SinsackCard, SPADE, A),
    (DeathSickleCard, SPADE, 2),
    (RepentanceStickCard, SPADE, 3),
    (AttackCard, SPADE, 4),
    (HakuroukenCard, SPADE, 5),
    (GungnirCard, SPADE, 6),
    (DemonParadeCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (WineCard, SPADE, 9),
    (SealingArrayCard, SPADE, 10),
    (AttackCard, SPADE, J),
    (AttackCard, SPADE, Q),
    (RejectCard, SPADE, K),

    (DuelCard, SPADE, A),
    (OpticalCloakCard, SPADE, 2),
    (DemolitionCard, SPADE, 3),
    (DemolitionCard, SPADE, 4),
    (YukariDimensionCard, SPADE, 5),
    (YukariDimensionCard, SPADE, 6),
    (AttackCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (AttackCard, SPADE, 9),
    (AttackCard, SPADE, 10),
    (AttackCard, SPADE, J),
    (AttackCard, SPADE, Q),
    (RejectCard, SPADE, K),

    # ======= Heart =======
    (FeastCard, HEART, A),
    (GrazeCard, HEART, 2),
    (HealCard, HEART, 3),
    (HarvestCard, HEART, 4),
    (AyaRoundfanCard, HEART, 5),
    (AttackCard, HEART, 6),
    (NazrinRodCard, HEART, 7),
    (NazrinRodCard, HEART, 8),
    (NazrinRodCard, HEART, 9),
    (SealingArrayCard, HEART, 10),
    (AttackCard, HEART, J),
    (DemolitionCard, HEART, Q),
    (RejectCard, HEART, K),

    (MapCannonCard, HEART, A),
    (AttackCard, HEART, 2),
    (GrazeCard, HEART, 3),
    (GrazeCard, HEART, 4),
    (HealCard, HEART, 5),
    (HealCard, HEART, 6),
    (HealCard, HEART, 7),
    (HealCard, HEART, 8),
    (GrazeCard, HEART, 9),
    (AttackCard, HEART, 10),
    (AttackCard, HEART, J),
    (GrazeCard, HEART, Q),
    (DuelCard, HEART, K),

    # ======= Club =======
    (YoumuPhantomCard, CLUB, A),
    (MomijiShieldCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (DemolitionCard, CLUB, 4),
    (FrozenFrogCard, CLUB, 5),
    (AttackCard, CLUB, 6),
    (AttackCard, CLUB, 7),
    (DemolitionCard, CLUB, 8),
    (WineCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (ExinwanCard, CLUB, Q),
    (DollControlCard, CLUB, K),

    (SuwakoHatCard, CLUB, A),
    (UmbrellaCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (AttackCard, CLUB, 4),
    (FrozenFrogCard, CLUB, 5),
    (AttackCard, CLUB, 6),
    (AttackCard, CLUB, 7),
    (AttackCard, CLUB, 8),
    (IbukiGourdCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (RejectCard, CLUB, Q),
    (DuelCard, CLUB, K),

    # ======= Diamond =======
    (DuelCard, DIAMOND, A),
    (GrazeCard, DIAMOND, 2),
    (HealCard, DIAMOND, 3),
    (AttackCard, DIAMOND, 4),
    (LaevateinCard, DIAMOND, 5),
    (YukariDimensionCard, DIAMOND, 6),
    (AttackCard, DIAMOND, 7),
    (GrazeCard, DIAMOND, 8),
    (AttackCard, DIAMOND, 9),
    (NenshaPhoneCard, DIAMOND, 10),
    (GrazeCard, DIAMOND, J),
    (HealCard, DIAMOND, Q),
    (GrazeCard, DIAMOND, K),

    (ElementalReactorCard, DIAMOND, A),
    (GrazeCard, DIAMOND, 2),
    (GrazeCard, DIAMOND, 3),
    (HealCard, DIAMOND, 4),
    (YukariDimensionCard, DIAMOND, 5),
    (GrazeCard, DIAMOND, 6),
    (GrazeCard, DIAMOND, 7),
    (GrazeCard, DIAMOND, 8),
    (GrazeCard, DIAMOND, 9),
    (AttackCard, DIAMOND, 10),
    (ExinwanCard, DIAMOND, J),
    (AttackCard, DIAMOND, Q),
    (GrazeCard, DIAMOND, K),
]

del A, J, Q, K
