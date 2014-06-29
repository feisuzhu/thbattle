# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, Game, user_input
from .baseclasses import Character, register_character
from ..actions import DropCards, UserAction, migrate_cards, PlayerTurn, PlayerDeath, DropCardStage, random_choose_card
from ..inputlets import ChoosePeerCardInputlet
from ..cards import Skill, t_One, CardList


class SpiritingAwayAction(UserAction):
    def apply_action(self):
        tgt = self.target
        src = self.source
        
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        if not card:
            card = random_choose_card(cats)
            if not card:
                return False

        self.card = card
        src.reveal(card)

        src.tags['spirit_away_tag'] += 1
        def spirited_away(p):
            try:
                return p.yukari_dimension
            except AttributeError:
                cl = CardList(p, 'yukari_dimension')
                p.yukari_dimension = cl
                p.showncardlists.append(cl)
                return cl

        migrate_cards([card], spirited_away(tgt))

        return True

    def is_valid(self):
        tgt = self.target
        catnames = ['cards', 'showncards', 'equips', 'fatetell']
        if not any(getattr(tgt, i) for i in catnames):
            return False

        return self.source.tags['spirit_away_tag'] < 2


class SpiritingAway(Skill):
    associated_action = SpiritingAwayAction
    target = t_One

    def check(self):
        return not self.associated_cards


class SpiritingAwayHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_apply' and isinstance(arg, PlayerTurn):
            tgt = arg.target
            if tgt.has_skill(SpiritingAway):
                tgt.tags['spirit_away_tag'] = 0

        elif evt_type == 'action_after' and isinstance(arg, PlayerDeath):
            g = Game.getgame()
            if not g.current_turn.has_skill(SpiritingAway):
                for p in g.players:
                    try:
                        cl = p.yukari_dimension
                    except AttributeError:
                        cl = None

                    if cl:
                        g.process_action(DropCards(p, cl))
                        p.showncardlists.remove(cl)
                        assert cl not in p.showncardlists

        elif evt_type == 'action_after' and isinstance(arg, DropCardStage):
            if not arg.target.has_skill(SpiritingAway):
                return arg

            g = Game.getgame()
            for p in g.players:
                try:
                    cl = p.yukari_dimension
                except AttributeError:
                    cl = None

                if cl:
                    migrate_cards(cl, p.cards)

        return arg


@register_character
class SpYukari(Character):
    skills = [SpiritingAway]
    eventhandlers_required = [SpiritingAwayHandler]
    maxlife = 4
