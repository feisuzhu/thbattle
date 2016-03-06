# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from game.autoenv import EventHandler, Game, user_input
from thb.actions import Damage, LaunchCard, UserAction, migrate_cards, user_choose_cards
from thb.cards import AttackCard, BaseAttack, Card, RedUFOSkill, Skill, TreatAs
from thb.cards import VirtualCard, t_None
from thb.characters.baseclasses import Character, register_character_to
from thb.inputlets import ChooseOptionInputlet


# -- code --
class SentryHandler(EventHandler):
    interested = ('action_before',)
    execute_after = (
        'RepentanceStickHandler',
        'UmbrellaHandler',
    )
    card_usage = 'launch'

    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, Damage):
            g = Game.getgame()
            pact = g.action_stack[-1]
            pcard = getattr(pact, 'associated_card', None)
            if not pcard: return act
            if pcard.is_card(SentryAttack):
                # Sentry effect
                src = pact.source
                if not src.dead and user_input([src], ChooseOptionInputlet(self, (False, True))):
                    # Guard
                    dmg = pcard.target_damage
                    dmg.amount = max(0, dmg.amount - 1)
                    act.cancelled = True
                else:
                    # Attack
                    pass

            elif pcard.is_card(AttackCard) and isinstance(pact, BaseAttack):
                # Sentry fire
                for p in g.players:
                    if p.dead: continue
                    if not p.has_skill(Sentry): continue
                    if p is pact.source: continue

                    tgt = pact.source
                    self.target = tgt  # for ui
                    self.act = act
                    dist = LaunchCard.calc_distance(p, AttackCard())
                    if dist.get(tgt, 1) > 0: continue
                    cl = user_choose_cards(self, p, ('cards', 'showncards', 'equips'))
                    if not cl: continue
                    c = SentryAttack.wrap(cl, p)
                    c.target_damage = act
                    g.process_action(LaunchCard(p, [tgt], c))
            else:
                return act

        return act

    def cond(self, cl):
        if not len(cl) == 1: return False
        c = cl[0]
        if c.is_card(AttackCard):
            return True

        return not c.is_card(Skill) and c.suit == Card.CLUB

    def ask_for_action_verify(self, p, cl, tl):
        c = SentryAttack.wrap(cl, p)
        tgt = self.target
        c.target_damage = self.act
        return LaunchCard(p, [tgt], c).can_fire()


class SentryAttack(TreatAs, VirtualCard):
    treat_as = AttackCard


class Sentry(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class SharpEye(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


class SharpEyeKOF(RedUFOSkill):
    skill_category = ('character', 'passive', 'compulsory')
    increment = 1


class SharpEyeKOFAction(UserAction):
    def __init__(self, source, target, cards):
        self.source = source
        self.target = target
        self.cards = cards

    def apply_action(self):
        g = Game.getgame()
        c = self.cards[0]
        g.players.reveal(c)
        migrate_cards([c], self.target.showncards, unwrap=True)
        return True


class SharpEyeKOFHandler(EventHandler):
    interested = ('post_card_migration',)

    def handle(self, evt_type, arg):
        if evt_type == 'post_card_migration':
            g = Game.getgame()
            a, b = g.players
            if not a.has_skill(SharpEyeKOF):
                a, b = b, a

            if not a.has_skill(SharpEyeKOF):
                return arg

            trans = arg

            cl = []
            for cards, _from, to, is_bh in trans.get_movements():
                if to is None: continue
                if to.owner is not b: continue
                if _from.owner is b: continue
                if to.type != 'cards': continue
                cl.extend(cards)

            if cl:
                g.process_action(SharpEyeKOFAction(a, b, cl))

        return arg


@register_character_to('common', '-kof')
class Momiji(Character):
    skills = [Sentry, SharpEye]
    eventhandlers_required = [SentryHandler]
    maxlife = 4


@register_character_to('kof')
class MomijiKOF(Character):
    skills = [Sentry, SharpEyeKOF]
    eventhandlers_required = [SentryHandler, SharpEyeKOFHandler]
    maxlife = 4
