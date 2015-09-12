# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game import sync_primitive
from game.autoenv import EventHandler, Game, InputTransaction, user_input
from gamepack.thb.actions import ActionStage, Damage, DrawCardStage, DrawCards, DropCards
from gamepack.thb.actions import FatetellAction, ForEach, LaunchCard, PlayerTurn, UserAction
from gamepack.thb.actions import ask_for_action, detach_cards, migrate_cards, random_choose_card
from gamepack.thb.actions import register_eh, user_choose_cards
from gamepack.thb.cards import basic
from gamepack.thb.inputlets import ChooseIndividualCardInputlet, ChoosePeerCardInputlet
from utils import BatchList, CheckFailed, check, flatten


# -- code --
class SpellCardAction(UserAction):
    non_responsive = False


class InstantSpellCardAction(SpellCardAction):
    pass


class Demolition(InstantSpellCardAction):
    # 城管执法

    def apply_action(self):
        g = Game.getgame()
        src, tgt = self.source, self.target

        catnames = ('cards', 'showncards', 'equips', 'fatetell')
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        if not card:
            card = random_choose_card(cats)
            if not card:
                return False

        self.card = card
        g.players.exclude(tgt).reveal(card)
        g.process_action(
            DropCards(src, tgt, cards=[card])
        )
        return True

    def is_valid(self):
        tgt = self.target
        catnames = ('cards', 'showncards', 'equips', 'fatetell')
        return not tgt.dead and any(getattr(tgt, i) for i in catnames)


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


@register_eh
class RejectHandler(EventHandler):
    interested = ('action_before',)
    card_usage = 'launch'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, SpellCardAction):
            if act.cancelled: return act  # some other thing have done the job
            if act.non_responsive:
                return act

            g = Game.getgame()

            has_reject = False
            while g.SERVER_SIDE:
                from ..characters.reimu import Reimu
                for p in g.players:
                    if isinstance(p, Reimu):
                        has_reject = True
                        break

                if has_reject: break

                from .definition import RejectCard
                for c in flatten([[p.cards, p.showncards] for p in g.players]):
                    if isinstance(c, RejectCard):
                        has_reject = True
                        break

                break

            has_reject = sync_primitive(has_reject, g.players)
            if not has_reject: return act

            self.target_act = act

            pl = BatchList(p for p in g.players if not p.dead)

            with InputTransaction('AskForRejectAction', pl) as trans:
                p, rst = ask_for_action(self, pl, ('cards', 'showncards'), [], trans)

            if not p: return act
            cards, _ = rst
            assert cards and self.cond(cards)
            g.process_action(LaunchCard(p, [act.target], cards[0], Reject(p, act)))

        return act

    def cond(self, cardlist):
        from .. import cards
        try:
            check(len(cardlist) == 1)
            check(cardlist[0].is_card(cards.RejectCard))
            return True
        except CheckFailed:
            return False

    def ask_for_action_verify(self, p, cl, tl):
        act = self.target_act
        return LaunchCard(p, [act.target], cl[0], Reject(p, act)).can_fire()


class DelayedSpellCardAction(SpellCardAction): pass  # 延时SC


class DelayedLaunchCard(UserAction):
    def apply_action(self):
        card = self.associated_card
        action = card.delayed_action
        assert issubclass(action, DelayedSpellCardAction)

        t = self.target
        migrate_cards([card], t.fatetell)

        return True

    def is_valid(self):
        if not self.associated_card: return False
        if not len(self.target_list) == 1: return False
        return not self.target.dead


class SealingArray(DelayedSpellCardAction, FatetellAction):
    # 封魔阵
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

        from ..cards import Card
        self.fatetell_cond = lambda card: card.suit != Card.HEART

    def fatetell_action(self, ft):
        if ft.succeeded:
            turn = PlayerTurn.get_current(self.target)
            try:
                turn.pending_stages.remove(ActionStage)
            except Exception:
                pass

            return True

        return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        tgt = self.target
        g.process_action(DropCards(None, tgt, [self.associated_card]))


class NazrinRod(InstantSpellCardAction):
    # 纳兹琳的探宝棒

    def apply_action(self):
        g = Game.getgame()
        g.process_action(DrawCards(self.target, amount=2))
        return True


class SinsackDamage(Damage):
    pass


class Sinsack(DelayedSpellCardAction, FatetellAction):
    # 罪袋
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

        from ..cards import Card
        self.fatetell_cond = lambda c: c.suit == Card.SPADE and 1 <= c.number <= 8

    def fatetell_action(self, ft):
        if ft.succeeded:
            g = Game.getgame()
            g.process_action(SinsackDamage(None, self.target, amount=3))
            return True

        return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        tgt = self.target
        if not self.cancelled and self.succeeded:
            g.process_action(DropCards(None, tgt, [self.associated_card]))
        else:
            pl = g.players
            stop = pl.index(tgt)
            next = stop - len(pl) + 1
            while next < stop:
                if not pl[next].dead:
                    migrate_cards([self.associated_card], pl[next].fatetell)
                    return
                next += 1


class YukariDimension(InstantSpellCardAction):
    # 紫的隙间

    def apply_action(self):
        src = self.source
        tgt = self.target

        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        if not card:
            card = random_choose_card(cats)
            if not card:
                return False

        self.card = card
        src.reveal(card)
        migrate_cards([card], src.cards, unwrap=True)
        return True

    def is_valid(self):
        if self.source.dead:
            return False

        tgt = self.target
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        return not tgt.dead and any(getattr(tgt, i) for i in catnames)


class BaseDuel(UserAction):
    # 弹幕战
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def apply_action(self):
        g = Game.getgame()
        source = self.source
        target = self.target

        s, t = source, target
        while True:
            if t.dead: break
            if not g.process_action(basic.UseAttack(t)): break
            s, t = t, s

        if not t.dead:
            g.process_action(Damage(s, t, amount=1))

        self.winner = s

        return True

    def is_valid(self):
        return not self.target.dead


class Duel(BaseDuel, InstantSpellCardAction):
    pass


class MapCannonEffect(InstantSpellCardAction):
    # 地图炮
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        graze_action = basic.UseGraze(target)
        if not g.process_action(graze_action):
            g.process_action(Damage(source, target, amount=1))
            return True
        else:
            return False

    def is_valid(self):
        return not self.target.dead


class MapCannon(ForEach):
    action_cls = MapCannonEffect
    group_effect = True


class SinsackCarnivalEffect(InstantSpellCardAction):
    # 罪袋狂欢
    def apply_action(self):
        g = Game.getgame()
        source, target = self.source, self.target
        use_action = basic.UseAttack(target)
        if not g.process_action(use_action):
            g.process_action(Damage(source, target, amount=1))
            return True
        else:
            return False

    def is_valid(self):
        return not self.target.dead


class SinsackCarnival(ForEach):
    action_cls = SinsackCarnivalEffect
    group_effect = True


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

    def is_valid(self):
        return not self.target.dead


class Feast(ForEach):
    action_cls = FeastEffect
    group_effect = True


class HarvestEffect(InstantSpellCardAction):
    # 五谷丰登 效果
    def apply_action(self):
        pact = ForEach.get_actual_action(self)
        cards = pact.cards
        cards_avail = [c for c in cards if c.detached]
        if not cards_avail: return False
        tgt = self.target

        card = user_input(
            [tgt],
            ChooseIndividualCardInputlet(self, cards_avail),
            trans=pact.trans,
        ) or random_choose_card([cards_avail])

        migrate_cards([card], tgt.cards)

        pact.trans.notify('harvest_choose', card)
        self.card = card
        return True

    def is_valid(self):
        try:
            cards = ForEach.get_actual_action(self).cards
        except:
            return False

        if self.target.dead:
            return False

        return bool([c for c in cards if c.detached])


class Harvest(ForEach):
    action_cls = HarvestEffect
    group_effect = True

    def prepare(self):
        tl = self.target_list
        g = Game.getgame()
        cards = g.deck.getcards(len(tl))
        g.players.reveal(cards)
        detach_cards(cards)
        trans = InputTransaction('HarvestChoose', g.players, cards=cards)
        trans.begin()
        self.cards = cards
        self.trans = trans

    def cleanup(self):
        g = Game.getgame()
        self.trans.end()
        g.emit_event('harvest_finish', self)
        dropped = g.deck.droppedcards
        migrate_cards([c for c in self.cards if c.detached], dropped, is_bh=True)


class DollControl(InstantSpellCardAction):
    card_usage = 'launch'

    def apply_action(self):
        tl = self.target_list
        assert len(tl) == 2
        src = self.source

        controllee, attackee = tl
        cards = user_choose_cards(self, controllee, ['cards', 'showncards'])
        g = Game.getgame()

        if cards:
            g.players.reveal(cards)
            g.process_action(LaunchCard(controllee, [attackee], cards[0]))
        else:
            l = [e for e in controllee.equips if e.equipment_category == 'weapon']
            migrate_cards(l, src.cards)
        return True

    def cond(self, cl):
        if len(cl) != 1: return False
        c = cl[0]
        if not c.associated_action: return False
        return issubclass(c.associated_action, basic.Attack)

    def ask_for_action_verify(self, p, cl, tl):
        attacker, victim = self.target_list
        return LaunchCard(attacker, [victim], cl[0]).can_fire()

    def is_valid(self):
        return not self.target.dead


class DonationBoxEffect(InstantSpellCardAction):
    card_usage = 'handover'

    def apply_action(self):
        t = self.target
        src = self.source
        g = Game.getgame()

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(t, i) for i in catnames]
        cards = user_choose_cards(self, t, catnames)
        if not cards:
            cards = [random_choose_card(cats)]

        if cards:
            g.players.exclude(t).reveal(cards)
            migrate_cards(cards, src.showncards)

        return True

    def cond(self, cards):
        from .base import Skill
        return len(cards) == 1 and cards[0].resides_in.type in (
            'cards', 'showncards', 'equips'
        ) and not cards[0].is_card(Skill)

    def is_valid(self):
        t = self.target
        if t.dead or self.source.dead: return False
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


class FrozenFrog(DelayedSpellCardAction, FatetellAction):
    # 冻青蛙
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.fatetell_target = target

        from ..cards import Card
        self.fatetell_cond = lambda c: c.suit != Card.SPADE

    def fatetell_action(self, ft):
        if ft.succeeded:
            turn = PlayerTurn.get_current(self.target)
            try:
                turn.pending_stages.remove(DrawCardStage)
            except Exception:
                pass

            return True

        return False

    def fatetell_postprocess(self):
        g = Game.getgame()
        tgt = self.target
        g.process_action(DropCards(None, tgt, [self.associated_card]))
