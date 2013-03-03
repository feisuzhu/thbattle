# -*- coding: utf-8 -*-

from ..actions import *
from . import basic
from . import base

from game.autoenv import PlayerList

class SpellCardAction(UserAction): pass
class InstantSpellCardAction(SpellCardAction): pass
class NonResponsiveInstantSpellCardAction(InstantSpellCardAction): pass

class Demolition(InstantSpellCardAction):
    # 城管执法

    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        #cards = random_choose_card(target, target.cards, 1)
        categories = [
            target.cards,
            target.showncards,
            target.equips,
            target.fatetell,
        ]
        card = choose_peer_card(source, target, categories)
        if not card:
            card = random_choose_card(categories)
            if not card:
                return False

        self.card = card
        g.players.exclude(target).reveal(card)
        g.process_action(
            DropCards(target=target, cards=[card])
        )
        return True


class Reject(InstantSpellCardAction):
    # 好人卡
    def __init__(self, source, target_act):
        self.source = source
        self.target_act = target_act
        self.target = target_act.target

    def apply_action(self):
        if not isinstance(self.target_act, SpellCardAction):
            return False
        self.target_act.cancelled = True
        return True


class LaunchReject(GenericAction):
    def __init__(self, source, target_act, card):
        self.source = source
        self.target_act = target_act
        self.target = target_act.target
        self.card = card

    def apply_action(self):
        action = Reject(source=self.source, target_act=self.target_act)
        action.associated_card = self.card
        g = Game.getgame()
        g.process_action(DropUsedCard(self.source, [self.card]))
        g.process_action(action)
        return True


@register_eh
class RejectHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            if act.cancelled: return act  # some other thing have done the job
            if isinstance(act, NonResponsiveInstantSpellCardAction):
                return act

            g = Game.getgame()
            self.target_act = act # for ui

            pl = PlayerList(p for p in g.players if not g.dead)
            p, input = pl.user_input_any(
                'choose_card_and_player_reject', self._expects, (self, [])
            )

            if not p: return act

            sid_list, cid_list, _ = input
            cards = g.deck.lookupcards(cid_list)

            if sid_list: # skill selected
                card = skill_wrap(p, sid_list, cards)
            else:
                card = cards[0]

            g.players.exclude(p).reveal(card)

            if not (card and self.cond([card])):
                return act

            g.process_action(LaunchReject(p, act, card))

        return act

    def _expects(self, p, input):
        from utils import check, CheckFailed
        try:
            check_type([[int, Ellipsis], [int, Ellipsis], []], input)

            sid_list, cid_list, _ = input

            g = Game.getgame()
            cards = g.deck.lookupcards(cid_list)
            check(cards)

            if sid_list:
                check(len(sid_list) == 1) # FIXME: HACK, but seems enough
                sid = sid_list[0]
                check(0 <= sid < len(p.skills))
                skill_cls = p.skills[sid]
                card = skill_cls.wrap(cards, p)
            else:
                card = cards[0]
                check(card in p.cards or card in p.showncards)

            return True
        except CheckFailed as e:
            return False

    def cond(self, cardlist):
        from utils import check, CheckFailed
        from .. import cards
        try:
            check(len(cardlist) == 1)
            check(cardlist[0].is_card(cards.RejectCard))
            return True
        except CheckFailed:
            return False


class DelayedSpellCardAction(SpellCardAction): pass # 延时SC


class DelayedLaunchCard(UserAction):
    def apply_action(self):
        g = Game.getgame()
        card = self.associated_card
        action = card.delayed_action
        card.fatetell_source = self.source
        assert issubclass(action, DelayedSpellCardAction)

        t = self.target
        migrate_cards([card], t.fatetell)

        return True

    def is_valid(self):
        if not self.associated_card: return False
        if not len(self.target_list) == 1: return False
        return True


class SealingArray(DelayedSpellCardAction):
    # 封魔阵
    def apply_action(self):
        g = Game.getgame()
        target = self.target
        from ..cards import Card
        ft = Fatetell(target, lambda card: card.suit != Card.HEART)
        g.process_action(ft)
        if ft.succeeded:
            target.tags['sealed'] = True
            return True
        else:
            return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        target = self.target
        g.process_action(DropCards(target, [self.associated_card]))


@register_eh
class SealingArrayHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            target = act.target
            if target.tags.get('sealed'):
                del target.tags['sealed']
                act.cancelled = True
        return act


class NazrinRod(InstantSpellCardAction):
    # 纳兹琳的探宝棒

    def apply_action(self):
        g = Game.getgame()
        g.process_action(DrawCards(self.target, amount=2))
        return True


class Sinsack(DelayedSpellCardAction):
    # 罪袋
    def apply_action(self):
        g = Game.getgame()
        target = self.target
        from ..cards import Card
        ft = Fatetell(target, lambda card: card.suit == Card.SPADE and 1 <= card.number <= 8)
        g.process_action(ft)
        if ft.succeeded:
            dmg = Damage(None, target, amount=3)
            dmg.associated_action = self
            g.process_action(dmg)
            return True
        return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        target = self.target
        if (not self.cancelled) and self.succeeded:
            g.process_action(DropCards(target, [self.associated_card]))
        else:
            pl = g.players
            stop = pl.index(target)
            n = len(pl)
            next = stop - len(pl) + 1
            while next < stop:
                if not pl[next].dead:
                    migrate_cards([self.associated_card], pl[next].fatetell)
                    return
                next += 1


class YukariDimension(InstantSpellCardAction):
    # 紫的隙间

    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        categories = [
            target.cards,
            target.showncards,
            target.equips,
            target.fatetell,
        ]
        card = choose_peer_card(source, target, categories)
        if not card:
            card = random_choose_card(categories)
            if not card:
                return False

        self.card = card
        source.reveal(card)
        migrate_cards([card], source.cards, unwrap=True)
        source.need_shuffle = True
        return True


class BaseDuel(UserAction):
    # 弹幕战
    def __init__(self, source, target, damage=1):
        self.source = source
        self.target = target
        self.source_damage = self.target_damage = damage

    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        d = (source, target)
        dmg = (self.source_damage, self.target_damage)
        while True:
            d = (d[1], d[0])
            dmg = (dmg[1], dmg[0])
            if not g.process_action(basic.UseAttack(d[0])): break

        dact = Damage(d[1], d[0], amount=dmg[1])
        dact.associated_action = self
        g.process_action(dact)
        return d[1] is source


class Duel(BaseDuel, InstantSpellCardAction):
    pass


class MapCannonEffect(InstantSpellCardAction):
    # 地图炮
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = basic.UseGraze(target)
        if not g.process_action(graze_action):
            dmg = Damage(source, target, amount=1)
            dmg.associated_action = self
            g.process_action(dmg)
            return True
        else:
            return False


class MapCannon(ForEach):
    action_cls = MapCannonEffect


class SinsackCarnivalEffect(InstantSpellCardAction):
    # 罪袋狂欢
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        use_action = basic.UseAttack(target)
        if not g.process_action(use_action):
            dmg = Damage(source, target, amount=1)
            dmg.associated_action = self
            g.process_action(dmg)
            return True
        else:
            return False


class SinsackCarnival(ForEach):
    action_cls = SinsackCarnivalEffect


class FeastEffect(InstantSpellCardAction):
    # 宴会
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        if tgt.life < tgt.maxlife:
            g.process_action(basic.Heal(src, tgt))
        else:
            g.process_action(basic.Wine(src, tgt))
        return True

class Feast(ForEach):
    action_cls = FeastEffect

class HarvestEffect(InstantSpellCardAction):
    # 五谷丰登 效果
    def apply_action(self):
        g = Game.getgame()
        cards = self.parent_action.cards
        cards_avail = [c for c in cards if c.resides_in is g.deck.special]
        if not cards_avail: return False
        cmap = {c.syncid:c for c in cards_avail}
        tgt = self.target
        cid = tgt.user_input('harvest_choose', cards_avail)
        card = cmap.get(cid)
        if not card:
            card = random_choose_card([cards_avail])
        migrate_cards([card], tgt.cards)
        tgt.need_shuffle = True
        g.emit_event('harvest_choose', card)
        self.card = card
        return True

class Harvest(ForEach):
    action_cls = HarvestEffect
    def prepare(self):
        tl = self.target_list
        g = Game.getgame()
        cards = g.deck.getcards(len(tl))
        g.players.reveal(cards)
        migrate_cards(cards, g.deck.special)
        g.emit_event('harvest_cards', cards)
        self.cards = cards

    def cleanup(self):
        g = Game.getgame()
        g.emit_event('harvest_finish', self)
        dropped = g.deck.droppedcards
        migrate_cards([c for c in self.cards if c.resides_in is g.deck.special], dropped)

class Camera(InstantSpellCardAction):
    # 文文的相机
    def apply_action(self):
        src = self.source
        tgt = self.target

        cards = list(tgt.cards)[:2]
        g = Game.getgame()
        g.players.exclude(tgt).reveal(cards)
        migrate_cards(cards, tgt.showncards)

        return True

class DollControl(InstantSpellCardAction):
    def apply_action(self):
        tl = self.target_list
        assert len(tl) == 2
        src = self.source

        controllee, attackee = tl
        cats = [
            controllee.cards,
            controllee.showncards,
        ]
        cards = user_choose_cards(self, controllee, cats)
        g = Game.getgame()

        if cards:
            g.players.reveal(cards)
            g.process_action(LaunchCard(controllee, [attackee], cards[0]))
        else:
            l = [e for e in controllee.equips if e.equipment_category == 'weapon']
            migrate_cards(l, src.cards)
            src.need_shuffle = True
        return True

    def cond(self, cl):
        from .definition import AttackCard
        if len(cl) != 1: return False
        if not cl[0].associated_action: return False
        if issubclass(cl[0].associated_action, basic.Attack): return True
        return False


class DonationBoxEffect(InstantSpellCardAction):
    def apply_action(self):
        t = self.target
        src = self.source
        g = Game.getgame()

        cats = [
            t.cards,
            t.showncards,
            t.equips,
        ]
        cards = user_choose_cards(self, t, cats)
        if not cards:
            cards = [random_choose_card(cats)]

        if cards:
            g.players.exclude(t).reveal(cards)
            migrate_cards(cards, src.showncards)

        return True

    def cond(self, cards):
        from .base import CardList
        return len(cards) == 1 and cards[0].resides_in.type != 'fatetell'

    def is_valid(self):
        t = self.target
        if t.cards or t.showncards or t.equips: return True
        return False

class DonationBox(ForEach):
    action_cls = DonationBoxEffect
    def is_valid(self):
        tl = self.target_list
        if not 0 < len(tl) <= 2: return False

        if not all(
            t.cards or t.showncards or t.equips
            for t in tl
        ): return False

        return True


class FrozenFrog(DelayedSpellCardAction):
    # 冻青蛙
    def apply_action(self):
        g = Game.getgame()
        target = self.target
        from ..cards import Card
        ft = Fatetell(target, lambda card: card.suit != Card.SPADE)
        g.process_action(ft)
        if ft.succeeded:
            target.tags['freezed'] = True
            return True
        else:
            return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        target = self.target
        g.process_action(DropCards(target, [self.associated_card]))


@register_eh
class FrozenFrogHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            tgt = act.target
            if tgt.tags.get('freezed'):
                del tgt.tags['freezed']
                act.cancelled = True
        return act


class LotteryHeart(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()
        candidates = [
            p for p in g.players
            if (p.cards or p.showncards or p.equips or p.fatetell) and not p.dead
        ]
        pl = user_choose_players(self, tgt, candidates)
        if not pl:
            return True

        p = pl[0]

        cats = [p.cards, p.showncards, p.equips, p.fatetell]
        card = choose_peer_card(tgt, p, cats)
        if not card:
            return True

        tgt.reveal(card)
        migrate_cards([card], tgt.cards, unwrap=True)
        return True

    def choose_player_target(self, pl):
        return (pl[-1:], True)


class LotteryDiamond(GenericAction):
    def apply_action(self):
        tgt = self.target
        g = Game.getgame()

        cards = user_choose_cards(self, tgt, [tgt.cards, tgt.showncards])
        if not cards:
            return True

        g.process_action(DropCards(tgt, cards))
        g.process_action(DrawCards(tgt, len(cards)))

        return True

    def cond(self, cards):
        return len(cards) <= 2


class LotteryClub(GenericAction):
    def apply_action(self):
        tgt = self.target
        cats = [tgt.cards, tgt.showncards, tgt.equips]
        if not any(cats):
            return True

        cards = user_choose_cards(self, tgt, cats)
        if not cards:
            cards = [random_choose_card(cats)]

        g = Game.getgame()
        g.players.reveal(cards)
        g.process_action(DropCards(tgt, cards))
        return True
    
    def cond(self, cards):
        return len(cards) == 1


class LotterySpade(GenericAction):
    def apply_action(self):
        tgt = self.target
        Game.getgame().process_action(LifeLost(tgt, tgt, 1))
        return True


class Lottery(InstantSpellCardAction):
    # 御神签
    mapping = {
        base.Card.HEART: LotteryHeart,
        base.Card.DIAMOND: LotteryDiamond,
        base.Card.CLUB: LotteryClub,
        base.Card.SPADE: LotterySpade,
    }
    def apply_action(self):
        src = self.source
        g = Game.getgame()
        g.process_action(DrawCards(src, 1))
        if not self.target_list:
            return True

        for tgt in self.target_list:
            ft = TurnOverCard(tgt, lambda card: True)
            g.process_action(ft)
            suit = ft.card.suit
            ActionClass = self.mapping[suit]
            g.process_action(ActionClass(src, tgt))

        return True
