# -*- coding: utf-8 -*-
# Cards and Deck definition

# -- stdlib --
# -- third party --
# -- own --
from .base import Card, PhysicalCard, t_All, t_AllInclusive, t_None, t_One, t_OtherLessEqThanN
from .base import t_OtherOne, t_Self
from game import GameObjectMeta


# -- code --
def card_meta(clsname, bases, _dict):
    for a in ('associated_action', 'target', 'category'):
        assert a in _dict

    cls = GameObjectMeta(clsname, (PhysicalCard,), _dict)
    Card.card_classes[clsname] = cls
    return cls

__metaclass__ = card_meta

# ==================================================


from . import basic


class AttackCard:
    associated_action = basic.Attack
    target = t_OtherOne
    category = ('basic', )
    distance = 1


class GrazeCard:
    associated_action = None
    target = t_None
    category = ('basic', )


class HealCard:
    associated_action = basic.Heal
    target = t_Self
    category = ('basic', )


class WineCard:
    associated_action = basic.Wine
    target = t_Self
    category = ('basic', )


class ExinwanCard:
    associated_action = basic.Exinwan
    target = t_Self
    category = ('basic', )

# --------------------------------------------------

from . import spellcard


class DemolitionCard:
    associated_action = spellcard.Demolition
    target = t_OtherOne
    category = ('spellcard', 'instant_spellcard')


class RejectCard:
    associated_action = None
    target = t_None
    category = ('spellcard', 'instant_spellcard')


class SealingArrayCard:
    associated_action = spellcard.DelayedLaunchCard
    target = t_OtherOne
    category = ('spellcard', 'delayed_spellcard')
    delayed_action = spellcard.SealingArray
    no_drop = True


class FrozenFrogCard:
    associated_action = spellcard.DelayedLaunchCard
    target = t_OtherOne
    category = ('spellcard', 'delayed_spellcard')
    distance = 1
    delayed_action = spellcard.FrozenFrog
    no_drop = True


class NazrinRodCard:
    associated_action = spellcard.NazrinRod
    target = t_Self
    category = ('spellcard', 'instant_spellcard')


class SinsackCard:
    associated_action = spellcard.DelayedLaunchCard
    target = t_Self
    category = ('spellcard', 'delayed_spellcard')
    delayed_action = spellcard.Sinsack
    no_drop = True


class YukariDimensionCard:
    associated_action = spellcard.YukariDimension
    target = t_OtherOne
    category = ('spellcard', 'instant_spellcard')
    distance = 1


class DuelCard:
    associated_action = spellcard.Duel
    target = t_OtherOne
    category = ('spellcard', 'instant_spellcard')


class MapCannonCard:
    associated_action = spellcard.MapCannon
    target = t_All
    category = ('spellcard', 'instant_spellcard')


class SinsackCarnivalCard:
    associated_action = spellcard.SinsackCarnival
    target = t_All
    category = ('spellcard', 'instant_spellcard')


class FeastCard:
    associated_action = spellcard.Feast
    target = t_AllInclusive
    category = ('spellcard', 'instant_spellcard')


class HarvestCard:
    associated_action = spellcard.Harvest
    target = t_AllInclusive
    category = ('spellcard', 'instant_spellcard')


class DollControlCard:
    associated_action = spellcard.DollControl

    def t_DollControl(g, source, tl):
        if not tl: return ([], False)
        tl = tl[:]
        while tl and source is tl[0]:
            del tl[0]
        return (tl[:2], len(tl) >= 2)

    target = staticmethod(t_DollControl)
    category = ('spellcard', 'instant_spellcard')
    del t_DollControl


class DonationBoxCard:
    associated_action = spellcard.DonationBox
    target = t_OtherLessEqThanN(2)
    category = ('spellcard', 'instant_spellcard')


# --------------------------------------------------

from . import equipment


class MomijiShieldCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'shield')
    equipment_skill = equipment.MomijiShieldSkill
    equipment_category = 'shield'


class OpticalCloakCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'shield')
    equipment_skill = equipment.OpticalCloakSkill
    equipment_category = 'shield'


class GreenUFOCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'greenufo')
    equipment_skill = equipment.GreenUFOSkill
    equipment_category = 'greenufo'


class RedUFOCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'redufo')
    equipment_skill = equipment.RedUFOSkill
    equipment_category = 'redufo'


class HakuroukenCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.HakuroukenSkill
    equipment_category = 'weapon'


class ElementalReactorCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.ElementalReactorSkill
    equipment_category = 'weapon'


class UmbrellaCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'shield')
    equipment_skill = equipment.UmbrellaSkill
    equipment_category = 'shield'


class RoukankenCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.RoukankenSkill
    equipment_category = 'weapon'


class GungnirCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.GungnirSkill
    equipment_category = 'weapon'


class LaevateinCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.LaevateinSkill
    equipment_category = 'weapon'


class NenshaPhoneCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.NenshaPhoneSkill
    equipment_category = 'weapon'


class RepentanceStickCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.RepentanceStickSkill
    equipment_category = 'weapon'


class MaidenCostumeCard:
    associated_action = equipment.WearEquipmentAction
    target = t_One
    category = ('equipment', 'shield')
    equipment_skill = equipment.MaidenCostumeSkill
    equipment_category = 'shield'
    distance = 2


class IbukiGourdCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'redufo')
    equipment_skill = equipment.IbukiGourdSkill
    equipment_category = 'redufo'


class HouraiJewelCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.HouraiJewelSkill
    equipment_category = 'weapon'


class SaigyouBranchCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'shield')
    equipment_skill = equipment.SaigyouBranchSkill
    equipment_category = 'shield'


class AyaRoundfanCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.AyaRoundfanSkill
    equipment_category = 'weapon'


class ScarletRhapsodyCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.ScarletRhapsodySkill
    equipment_category = 'weapon'


class DeathSickleCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.DeathSickleSkill
    equipment_category = 'weapon'


class KeystoneCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'greenufo')
    equipment_skill = equipment.KeystoneSkill
    equipment_category = 'greenufo'


class WitchBroomCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'redufo')
    equipment_skill = equipment.WitchBroomSkill
    equipment_category = 'redufo'


class YinYangOrbCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'accessories')
    equipment_skill = equipment.YinYangOrbSkill
    equipment_category = 'accessories'


class SuwakoHatCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'accessories')
    equipment_skill = equipment.SuwakoHatSkill
    equipment_category = 'accessories'


class YoumuPhantomCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'accessories')
    equipment_skill = equipment.YoumuPhantomSkill
    equipment_category = 'accessories'


class IceWingCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'accessories')
    equipment_skill = equipment.IceWingSkill
    equipment_category = 'accessories'


class GrimoireCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.GrimoireSkill
    equipment_category = 'weapon'

# ==================================================

del __metaclass__

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
    (SinsackCarnivalCard, SPADE, 7),
    (SinsackCarnivalCard, SPADE, 8),
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
    (MaidenCostumeCard, HEART, 2),
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
    (SinsackCarnivalCard, CLUB, 7),
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
    (SaigyouBranchCard, CLUB, Q),
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
    (SinsackCarnivalCard, SPADE, 7),
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
