# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from gamepack.thb.actions import DropCards, PlayerTurn, UserAction, migrate_cards
from gamepack.thb.actions import random_choose_card, ttags, user_choose_cards, user_choose_players
from gamepack.thb.cards import AttackCard, CardList, Heal, HiddenCard, PhysicalCard, Skill, t_Self
from gamepack.thb.characters.baseclasses import Character, register_character
from gamepack.thb.inputlets import ChooseIndividualCardInputlet


# -- code --
class QiliaoAction(UserAction):

    def apply_action(self):
        tgt = self.target
        ttags(tgt)['qiliao'] = True
        g = Game.getgame()

        cl = getattr(tgt, 'meirin_qiliao', None)
        if cl is None:
            cl = CardList(tgt, 'meirin_qiliao')
            tgt.meirin_qiliao = cl
            tgt.showncardlists.append(cl)

        migrate_cards([self.associated_card], cl, unwrap=True)

        g.deck.shuffle(cl)

        return True

    def is_valid(self):
        tgt = self.target
        return not ttags(tgt)['qiliao']


class Qiliao(Skill):
    associated_action = QiliaoAction
    skill_category = ('character', 'active')
    target = t_Self
    no_reveal = True
    no_drop = True
    usage = 'move'

    def check(self):
        cl = self.associated_cards
        if not 0 < len(cl) <= 3: return False
        if not all([c.is_card(PhysicalCard) or c.is_card(HiddenCard) for c in cl]):
            return False

        if not all([
            c.resides_in is not None and
            c.resides_in.type in ('cards', 'showncards', 'equips')
            for c in cl
        ]): return False

        return True


class QiliaoDropHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            actor = act.target
            g = Game.getgame()

            for p in g.players:
                if not p.has_skill(Qiliao): continue
                qi = getattr(p, 'meirin_qiliao', None)
                if not qi: continue
                cl = user_choose_cards(self, actor, ('cards', 'showncards'))
                if not cl: continue
                g.process_action(DropCards(actor, actor, cl))
                if actor.dead: continue
                c = user_input([actor], ChooseIndividualCardInputlet(self, qi)) or random_choose_card([qi])
                g.players.reveal(c)
                g.process_action(DropCards(actor, p, [c]))

        return act

    def cond(self, cl):
        if len(cl) != 1: return False
        c, = cl
        return c.is_card(PhysicalCard) and c.is_card(AttackCard)


class QiliaoRecoverAction(UserAction):

    def apply_action(self):
        src, tgt = self.source, self.target
        qi = src.meirin_qiliao
        assert qi
        g = Game.getgame()
        tgt.reveal(list(qi))
        migrate_cards(qi, tgt.cards, unwrap=True)
        g.process_action(Heal(src, tgt, 1))
        return True


class QiliaoRecoverHandler(EventHandler):
    interested = ('action_apply',)

    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, PlayerTurn):
            tgt = act.target
            if not tgt.has_skill(Qiliao): return act
            qi = getattr(tgt, 'meirin_qiliao', None)
            if not qi: return act
            g = Game.getgame()
            pl = user_choose_players(self, tgt, [p for p in g.players if not p.dead])
            if not pl: return act
            g.process_action(QiliaoRecoverAction(tgt, pl[0]))

        return act

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)


@register_character
class Meirin20150714(Character):
    skills = [Qiliao]
    eventhandlers_required = [QiliaoDropHandler, QiliaoRecoverHandler]
    maxlife = 4
