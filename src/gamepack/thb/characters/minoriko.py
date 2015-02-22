# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCardStage, UserAction, migrate_cards
from ..cards import Card, Harvest, HarvestCard, Skill, TreatAs, t_None
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class Foison(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class FoisonDrawCardStage(DrawCardStage):
    def apply_action(self):
        self.amount = max(self.amount, 5 - len(self.target.cards) - len(self.target.showncards))
        return DrawCardStage.apply_action(self)


class FoisonHandler(EventHandler):
    interested = ('action_before',)
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if tgt.has_skill(Foison):
                act.__class__ = FoisonDrawCardStage
        return act


class AutumnFeastAction(Harvest):
    def apply_action(self):
        tags = self.source.tags
        tags['autumnfeast_tag'] = tags['turn_count']
        return Harvest.apply_action(self)

    def is_valid(self):
        tags = self.source.tags
        if tags['turn_count'] <= tags['autumnfeast_tag']:
            return False
        return Harvest.is_valid(self)


class AutumnFeast(TreatAs, Skill):
    treat_as = HarvestCard
    associated_action = AutumnFeastAction
    skill_category = ('character', 'active')

    def check(self):
        cl = self.associated_cards
        if cl and len(cl) == 2 and all(c.color == Card.RED for c in cl):
            return True
        return False


class AkiTribute(Skill):
    associated_action = None
    skill_category = ('character', 'passive', 'compulsory')
    target = t_None


class AkiTributeCollectCard(UserAction):
    def __init__(self, target, cards):
        self.source = self.target = target
        self.cards = cards

    def apply_action(self):
        migrate_cards(self.cards, self.target.showncards)
        return True


class AkiTributeHandler(EventHandler):
    interested = ('choose_target', 'harvest_finish')
    def handle(self, evt_type, act):
        if evt_type == 'choose_target':
            act, tl = arg = act
            card = act.card
            if not card.is_card(HarvestCard): return arg
            pl = [p for p in tl if p.has_skill(AkiTribute) and not p.dead]
            assert len(pl) <= 1, 'Multiple AkiTributes!'
            if not pl: return arg
            p = pl[0]
            tl.remove(p)
            tl.insert(0, p)
            return act, tl

        elif evt_type == 'harvest_finish':
            g = Game.getgame()
            pl = [p for p in g.players if p.has_skill(AkiTribute) and not p.dead]
            assert len(pl) <= 1, 'Multiple AkiTributes!'
            if not pl: return act
            p = pl[0]
            g.process_action(AkiTributeCollectCard(p, [
                c for c in act.cards
                if c.resides_in is g.deck.disputed
            ]))

        return act


@register_character
class Minoriko(Character):
    skills = [Foison, AutumnFeast, AkiTribute]
    eventhandlers_required = [FoisonHandler, AkiTributeHandler]
    maxlife = 3
