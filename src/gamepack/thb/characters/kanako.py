# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game
from gamepack.thb.actions import DrawCardStage, DrawCards, DropCards, ForEach, LaunchCard, ShowCards
from gamepack.thb.actions import UserAction, migrate_cards, random_choose_card, user_choose_cards
from gamepack.thb.actions import user_choose_players, user_input
from gamepack.thb.cards import AttackCard, Card, DuelCard, Skill, TreatAs, VirtualCard, t_None
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet


# -- code --
class KanakoFaithCheers(UserAction):
    def apply_action(self):
        return Game.getgame().process_action(DrawCards(self.target, 1))


class KanakoFaithAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class KanakoFaithDuel(TreatAs, VirtualCard):
    treat_as = DuelCard


class KanakoFaithCounteract(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(KanakoFaithCounteractPart1(src, tgt))
        g.process_action(KanakoFaithCounteractPart2(src, tgt))
        return True


class KanakoFaithCounteractPart1(UserAction):

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]

        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        card = card or random_choose_card(cats)

        assert card
        self.card = card

        g.players.reveal(card)
        g.process_action(DropCards(src, tgt, [card]))
        return True


class KanakoFaithCounteractPart2(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        choice = user_input([src], ChooseOptionInputlet(self, ('duel', 'attack')))

        if choice == 'duel':
            cls = KanakoFaithDuel
        elif choice == 'attack':
            cls = KanakoFaithAttack
        else:
            cls = KanakoFaithAttack

        g.process_action(LaunchCard(tgt, [src], cls(tgt), bypass_check=True))

        return True


class KanakoFaithEffect(UserAction):
    card_usage = 'drop'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        has_card = src.cards or src.showncards or src.equips

        if has_card and user_input([tgt], ChooseOptionInputlet(self, ('drop', 'draw'))) == 'drop':
            g.process_action(KanakoFaithCounteract(tgt, src))
        else:
            g.process_action(KanakoFaithCheers(tgt, src))

        return True


class KanakoFaithAction(ForEach):
    action_cls = KanakoFaithEffect

    def prepare(self):
        self.source.tags['kanako_faith'] = True

    def is_valid(self):
        return not self.source.tags['kanako_faith']


class KanakoFaith(Skill):
    associated_action = KanakoFaithAction
    skill_category = ('character', 'active', 'once')

    def check(self):
        return not self.associated_cards

    @staticmethod
    def target(g, p, tl):
        l = g.players.rotate_to(p)
        del l[0]

        dists = LaunchCard.calc_raw_distance(p, AttackCard())
        return ([t for t in l if not t.dead and dists[t] <= 1], True)


class VirtueAction(UserAction):
    card_usage = 'handover'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()
        g.process_action(DrawCards(tgt, 2))

        cl = user_choose_cards(self, tgt, ('cards', 'showncards', 'equips'))
        c = cl[0] if cl else random_choose_card([tgt.cards, tgt.showncards, tgt.equips])

        if c:
            g.players.reveal(c)
            g.process_action(ShowCards(tgt, [c]))

            migrate_cards([c], src.cards)
            if c.suit == Card.HEART:
                g.process_action(DrawCards(src, 1))

        return True

    def cond(self, cl):
        return len(cl) == 1 and not cl[0].is_card(VirtualCard)


class VirtueHandler(EventHandler):
    interested = ('action_before',)

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, DrawCardStage):
            if act.cancelled:
                return act

            tgt = act.target
            if not tgt.has_skill(Virtue):
                return act

            g = Game.getgame()
            pl = [p for p in g.players if not p.dead and p is not tgt]
            pl = pl and user_choose_players(self, tgt, pl)
            if not pl:
                return act

            act.cancelled = True
            g.process_action(VirtueAction(tgt, pl[0]))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


class Virtue(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


@register_character
class Kanako(Character):
    skills = [Virtue, KanakoFaith]
    eventhandlers_required = [VirtueHandler]
    maxlife = 4
