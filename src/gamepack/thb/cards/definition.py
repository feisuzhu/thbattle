# -*- coding: utf-8 -*-
# Cards and Deck definition

#from .base import *
from .base import Card, t_None, t_One, t_Self, t_OtherOne, t_All, t_AllInclusive, t_OtherLessEqThanN

from game import GameObjectMeta


def card_meta(clsname, bases, _dict):
    for a in ('associated_action', 'target', 'category'):
        assert a in _dict

    cls = GameObjectMeta(clsname, (Card,), _dict)
    Card.card_classes[clsname] = cls
    return cls

__metaclass__ = card_meta

# ==================================================


class DummyCard:
    associated_action = None
    target = t_None
    category = ('dummy', )

    def __init__(self, suit=Card.NOTSET, number=0, resides_in=None, **kwargs):
        Card.__init__(self, suit, number, resides_in)
        self.__dict__.update(kwargs)


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


class CameraCard:
    associated_action = spellcard.Camera
    target = t_OtherOne
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


class TridentCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.TridentSkill
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


class FlirtingSwordCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.FlirtingSwordSkill
    equipment_category = 'weapon'


class AyaRoundfanCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.AyaRoundfanSkill
    equipment_category = 'weapon'


class ScarletRhapsodySwordCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    category = ('equipment', 'weapon')
    equipment_skill = equipment.ScarletRhapsodySwordSkill
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

__metaclass__ = type

SPADE, HEART, CLUB, DIAMOND = Card.SPADE, Card.HEART, Card.CLUB, Card.DIAMOND
J, Q, K = 11, 12, 13

card_definition = [
    # ======= Spade =======
    (SinsackCard, SPADE, 1),
    (FlirtingSwordCard, SPADE, 2),
    (YukariDimensionCard, SPADE, 3),
    (YukariDimensionCard, SPADE, 4),
    (RoukankenCard, SPADE, 5),
    (HakuroukenCard, SPADE, 6),
    (AttackCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (AttackCard, SPADE, 9),
    (AttackCard, SPADE, 10),
    (YukariDimensionCard, SPADE, J),
    (GungnirCard, SPADE, Q),
    (RedUFOCard, SPADE, K),

    (DuelCard, SPADE, 1),
    (OpticalCloakCard, SPADE, 2),
    (DemolitionCard, SPADE, 3),
    (DemolitionCard, SPADE, 4),
    (GreenUFOCard, SPADE, 5),
    (SealingArrayCard, SPADE, 6),
    (SinsackCarnivalCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (AttackCard, SPADE, 9),
    (AttackCard, SPADE, 10),
    (RejectCard, SPADE, J),
    (DemolitionCard, SPADE, Q),
    (SinsackCarnivalCard, SPADE, K),

    (RepentanceStickCard, SPADE, 2),
    # (LotteryCard, SPADE, J),
    (YinYangOrbCard, SPADE, K),

    (DeathSickleCard, SPADE, 1),
    (UmbrellaCard, SPADE, 2),
    (WineCard, SPADE, 3),
    (AttackCard, SPADE, 4),
    (AttackCard, SPADE, 5),
    (AttackCard, SPADE, 6),
    (AttackCard, SPADE, 7),
    (AttackCard, SPADE, 8),
    (WineCard, SPADE, 9),
    (FrozenFrogCard, SPADE, 10),
    (KeystoneCard, SPADE, J),
    (IceWingCard, SPADE, Q),
    (RejectCard, SPADE, K),

    # =======  Heart =======
    (MapCannonCard, HEART, 1),
    (GrazeCard, HEART, 2),
    (HealCard, HEART, 3),
    (HealCard, HEART, 4),
    (TridentCard, HEART, 5),
    (HealCard, HEART, 6),
    (HealCard, HEART, 7),
    (HealCard, HEART, 8),
    (HealCard, HEART, 9),
    (AttackCard, HEART, 10),
    (AttackCard, HEART, J),
    (HealCard, HEART, Q),
    (GrazeCard, HEART, K),

    (FeastCard, HEART, 1),
    (GrazeCard, HEART, 2),
    (HarvestCard, HEART, 3),
    (HarvestCard, HEART, 4),
    (RedUFOCard, HEART, 5),
    (SealingArrayCard, HEART, 6),
    (NazrinRodCard, HEART, 7),
    (NazrinRodCard, HEART, 8),
    (NazrinRodCard, HEART, 9),
    (AttackCard, HEART, 10),
    (NazrinRodCard, HEART, J),
    (DemolitionCard, HEART, Q),
    (GreenUFOCard, HEART, K),

    (DonationBoxCard, HEART, 7),
    (MaidenCostumeCard, HEART, 10),
    (YinYangOrbCard, HEART, J),
    # (LotteryCard, HEART, J),
    (SinsackCard, HEART, Q),
    (YinYangOrbCard, HEART, K),

    (RejectCard, HEART, 1),
    (CameraCard, HEART, 2),
    (CameraCard, HEART, 3),
    (AttackCard, HEART, 4),
    (HealCard, HEART, 5),
    (HealCard, HEART, 6),
    (AttackCard, HEART, 7),
    (GrazeCard, HEART, 8),
    (GrazeCard, HEART, 9),
    (GrazeCard, HEART, 10),
    (AttackCard, HEART, J),
    (GrazeCard, HEART, Q),
    (RejectCard, HEART, K),

    # ======= Club =======
    (ElementalReactorCard, CLUB, 1),
    (AttackCard, CLUB, 2),
    (AttackCard, CLUB, 3),
    (AttackCard, CLUB, 4),
    (AttackCard, CLUB, 5),
    (AttackCard, CLUB, 6),
    (AttackCard, CLUB, 7),
    (AttackCard, CLUB, 8),
    (AttackCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (DollControlCard, CLUB, Q),
    (DollControlCard, CLUB, K),

    (DuelCard, CLUB, 1),
    (OpticalCloakCard, CLUB, 2),
    (DemolitionCard, CLUB, 3),
    (DemolitionCard, CLUB, 4),
    (GreenUFOCard, CLUB, 5),
    (SealingArrayCard, CLUB, 6),
    (SinsackCarnivalCard, CLUB, 7),
    (AttackCard, CLUB, 8),
    (AttackCard, CLUB, 9),
    (AttackCard, CLUB, 10),
    (AttackCard, CLUB, J),
    (RejectCard, CLUB, Q),
    (RejectCard, CLUB, K),

    (SaigyouBranchCard, CLUB, 2),
    (FrozenFrogCard, CLUB, 3),
    (ExinwanCard, CLUB, 10),
    (ExinwanCard, CLUB, J),
    (ExinwanCard, CLUB, Q),

    (YoumuPhantomCard, CLUB, 1),
    (SuwakoHatCard, CLUB, 2),
    (WineCard, CLUB, 3),
    (FrozenFrogCard, CLUB, 4),
    (AttackCard, CLUB, 5),
    (AttackCard, CLUB, 6),
    (AttackCard, CLUB, 7),
    (AttackCard, CLUB, 8),
    (WineCard, CLUB, 9),
    (IbukiGourdCard, CLUB, 10),
    (DonationBoxCard, CLUB, J),
    (DonationBoxCard, CLUB, Q),
    (WitchBroomCard, CLUB, K),

    # ======= Diamond =======
    (ElementalReactorCard, DIAMOND, 1),
    (GrazeCard, DIAMOND, 2),
    (YukariDimensionCard, DIAMOND, 3),
    (YukariDimensionCard, DIAMOND, 4),
    (ScarletRhapsodySwordCard, DIAMOND, 5),
    (AttackCard, DIAMOND, 6),
    (AttackCard, DIAMOND, 7),
    (AttackCard, DIAMOND, 8),
    (AttackCard, DIAMOND, 9),
    (AttackCard, DIAMOND, 10),
    (GrazeCard, DIAMOND, J),
    (HealCard, DIAMOND, Q),
    (AttackCard, DIAMOND, K),

    (DuelCard, DIAMOND, 1),
    (GrazeCard, DIAMOND, 2),
    (GrazeCard, DIAMOND, 3),
    (GrazeCard, DIAMOND, 4),
    (GrazeCard, DIAMOND, 5),
    (GrazeCard, DIAMOND, 6),
    (GrazeCard, DIAMOND, 7),
    (GrazeCard, DIAMOND, 8),
    (GrazeCard, DIAMOND, 9),
    (GrazeCard, DIAMOND, 10),
    (GrazeCard, DIAMOND, J),
    (LaevateinCard, DIAMOND, Q),
    (GreenUFOCard, DIAMOND, K),

    (ExinwanCard, DIAMOND, 5),
    (MaidenCostumeCard, DIAMOND, 10),
    (HouraiJewelCard, DIAMOND, J),
    (RejectCard, DIAMOND, Q),

    (AyaRoundfanCard, DIAMOND, 1),
    (HealCard, DIAMOND, 2),
    (HealCard, DIAMOND, 3),
    (AttackCard, DIAMOND, 4),
    (AttackCard, DIAMOND, 5),
    (GrazeCard, DIAMOND, 6),
    (GrazeCard, DIAMOND, 7),
    (GrazeCard, DIAMOND, 8),
    (WineCard, DIAMOND, 9),
    (GrazeCard, DIAMOND, 10),
    (GrazeCard, DIAMOND, J),
    (GrimoireCard, DIAMOND, Q),
    (RedUFOCard, DIAMOND, K),
]

del J, Q, K
