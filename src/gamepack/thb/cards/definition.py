# -*- coding: utf-8 -*-
# Cards and Deck definition

from .base import *

def card_meta(clsname, bases, _dict):
    cls = type(clsname, (Card,), _dict)
    for a in ('associated_action', 'target'):
        assert hasattr(cls, a)
    Card.card_classes[clsname] = cls
    return cls

__metaclass__ = card_meta

# ==================================================

class DummyCard:
    associated_action = None
    target = t_None

from . import basic

class AttackCard:
    associated_action = basic.Attack
    target = t_OtherOne
    distance = 1

class GrazeCard:
    associated_action = None
    target = t_None

class HealCard:
    associated_action = basic.Heal
    target = t_Self

class WineCard:
    associated_action = basic.Wine
    target = t_Self

class ExinwanCard:
    associated_action = basic.Exinwan
    target = t_Self

# --------------------------------------------------

from . import spellcard

class DemolitionCard:
    associated_action = spellcard.Demolition
    target = t_OtherOne

class RejectCard:
    associated_action = None
    target = t_None

class SealingArrayCard:
    associated_action = spellcard.SealingArray
    target = t_OtherOne

class NazrinRodCard:
    associated_action = spellcard.NazrinRod
    target = t_Self

class SinsackCard:
    associated_action = spellcard.Sinsack
    target = t_Self

class YukariDimensionCard:
    associated_action = spellcard.YukariDimension
    target = t_OtherOne
    distance = 1

class DuelCard:
    associated_action = spellcard.Duel
    target = t_OtherOne

class MapCannonCard:
    associated_action = spellcard.MapCannon
    target = t_All

class SinsackCarnivalCard:
    associated_action = spellcard.SinsackCarnival
    target = t_All

class FeastCard:
    associated_action = spellcard.Feast
    target = t_AllInclusive

class HarvestCard:
    associated_action = spellcard.Harvest
    target = t_AllInclusive

class CameraCard:
    associated_action = spellcard.Camera
    target = t_OtherOne

class DollControlCard:
    associated_action = spellcard.DollControl

    @staticmethod
    def target(g, source, tl):
        if not tl: return ([], False)
        tl = tl[:]
        while tl and source is tl[0]:
            del tl[0]
        return (tl[:2], len(tl) >= 2)

class DonationBoxCard:
    associated_action = spellcard.DonationBox
    target = t_OtherLessEqThanN(2)


# --------------------------------------------------

from . import equipment

class OpticalCloakCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.OpticalCloakSkill
    equipment_category = 'shield'

class GreenUFOCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.GreenUFOSkill
    equipment_category = 'greenufo'

class RedUFOCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.RedUFOSkill
    equipment_category = 'redufo'

class HakuroukenCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.HakuroukenSkill
    equipment_category = 'weapon'

class ElementalReactorCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.ElementalReactorSkill
    equipment_category = 'weapon'

class UmbrellaCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.UmbrellaSkill
    equipment_category = 'shield'

class RoukankenCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.RoukankenSkill
    equipment_category = 'weapon'

class GungnirCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.GungnirSkill
    equipment_category = 'weapon'

class LaevateinCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.LaevateinSkill
    equipment_category = 'weapon'

class TridentCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.TridentSkill
    equipment_category = 'weapon'

class RepentanceStickCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.RepentanceStickSkill
    equipment_category = 'weapon'

class MaidenCostumeCard:
    associated_action = equipment.WearEquipmentAction
    target = t_One
    equipment_skill = equipment.MaidenCostumeSkill
    equipment_category = 'shield'
    distance = 2

class IbukiGourdCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.IbukiGourdSkill
    equipment_category = 'redufo'

class HouraiJewelCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.HouraiJewelSkill
    equipment_category = 'weapon'

class SaigyouBranchCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.SaigyouBranchSkill
    equipment_category = 'shield'

class FlirtingSwordCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.FlirtingSwordSkill
    equipment_category = 'weapon'

class AyaRoundfanCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.AyaRoundfanSkill
    equipment_category = 'weapon'

class ScarletRhapsodySwordCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.ScarletRhapsodySwordSkill
    equipment_category = 'weapon'

class DeathSickleCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.DeathSickleSkill
    equipment_category = 'weapon'

class KeystoneCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.KeystoneSkill
    equipment_category = 'greenufo'

class WitchBroomCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.WitchBroomSkill
    equipment_category = 'redufo'

class YinYangOrbCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.YinYangOrbSkill
    equipment_category = 'accessories'

class SuwakoHatCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.SuwakoHatSkill
    equipment_category = 'accessories'

class YoumuPhantomCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.YoumuPhantomSkill
    equipment_category = 'accessories'

class IceWingCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.IceWingSkill
    equipment_category = 'accessories'

class GrimoireCard:
    associated_action = equipment.WearEquipmentAction
    target = t_Self
    equipment_skill = equipment.GrimoireSkill
    equipment_category = 'weapon'

# ==================================================

__metaclass__ = type

card_definition = [
    (OpticalCloakCard, Card.SPADE, 1),
    (AttackCard, Card.CLUB, 1),
    (GrazeCard, Card.SPADE, 1),

    (SealingArrayCard, Card.CLUB, 3),
    (DemolitionCard, Card.SPADE, 1),
    (GreenUFOCard, Card.SPADE, 3),
    (RedUFOCard, Card.SPADE, 4),
    (MapCannonCard, Card.SPADE, 12),
    (GungnirCard, Card.SPADE, 1),
    (DonationBoxCard, Card.SPADE, 1),
    (KeystoneCard, Card.SPADE, 1),
    (SuwakoHatCard, Card.SPADE, 1),
    (WitchBroomCard, Card.SPADE, 1),
    (ScarletRhapsodySwordCard, Card.SPADE, 1),
    (TridentCard, Card.SPADE, 1),
    (HakuroukenCard, Card.SPADE, 1),
    (HarvestCard, Card.SPADE, 1),
    (DonationBoxCard, Card.SPADE, 1),
    (WineCard, Card.SPADE, 1),
    (RejectCard, Card.SPADE, 1),
    (DonationBoxCard, Card.SPADE, 1),
    (SinsackCarnivalCard, Card.SPADE, 1),
    (SaigyouBranchCard, Card.SPADE, 1),
    (AyaRoundfanCard, Card.SPADE, 1),
    (GrimoireCard, Card.SPADE, 1),
    (RepentanceStickCard, Card.CLUB, 1),
    (SinsackCard, Card.SPADE, 1),
    (ExinwanCard, Card.SPADE, 1),

] * 2
