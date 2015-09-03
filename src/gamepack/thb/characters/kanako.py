# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCardStage, DrawCards, DropCards, UserAction, ShowCards
from ..actions import user_choose_cards, random_choose_card, migrate_cards
from ..actions import ForEach, LaunchCard, user_input, user_choose_players
from ..cards import Skill, t_None, Card, AttackCard, TreatAs, VirtualCard, DuelCard
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from .baseclasses import Character, register_character
from game.autoenv import EventHandler, Game


# -- code --
class KanakoFaithDrawCards(DrawCards):
    pass


class KanakoFaithDropCards(DropCards):
    pass


class KanakoFaithAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class KanakoFaithDuel(TreatAs, VirtualCard):
    treat_as = DuelCard


class KanakoFaithByForce(UserAction):
    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        if user_input([src], ChooseOptionInputlet(self, (False, True))):
            g.process_action(LaunchCard(src, [tgt], KanakoFaithDuel(src), bypass_check=True))

        else:
            g.process_action(LaunchCard(src, [tgt], KanakoFaithAttack(src), bypass_check=True))

        return True


class KanakoFaithEffect(UserAction):
    card_usage = 'drop'

    def apply_action(self):
        src, tgt = self.source, self.target
        g = Game.getgame()

        catnames = ('cards', 'showncards', 'equips')
        cats = [getattr(tgt, i) for i in catnames]

        if any(cats) and user_input([tgt], ChooseOptionInputlet(self, (False, True))):
            card = user_input([tgt], ChoosePeerCardInputlet(self, src, catnames))
            if not card:
                card = random_choose_card(cats)

            assert card
            g.players.reveal(card)
            g.process_action(KanakoFaithDropCards(tgt, src, [card]))
            g.process_action(KanakoFaithByForce(src, tgt))

        else:
            g.process_action(KanakoFaithDrawCards(src, 1))

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
        c = cl[0] if cl else random_choose_card([src.cards, src.showncards, src.equips])

        if c:
            g.players.reveal(c)
            g.process_action(ShowCards(tgt, [c]))

            migrate_cards([c], src.cards)
            if c.suit == Card.HEART:
                g.process_action(DrawCards(src, 1))

        return True

    def cond(self, cl):
        return len(cl) == 1 and cl[0] in self.cards


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
