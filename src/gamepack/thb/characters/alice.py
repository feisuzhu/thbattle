# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
# -- own --
from ..actions import DrawCards, DropCardStage, DropCards, UserAction, random_choose_card
from ..actions import user_choose_players
from ..cards import Skill, t_None
from ..inputlets import ChooseOptionInputlet, ChoosePeerCardInputlet
from baseclasses import Character, register_character
from game.autoenv import EventHandler, Game, user_input


# -- code --
class LittleLegion(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class LittleLegionDrawCards(DrawCards):
    pass


class LittleLegionAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        tgt = self.target

        catnames = ['cards', 'showncards', 'equips']
        cats = [getattr(tgt, i) for i in catnames]
        card = user_input([src], ChoosePeerCardInputlet(self, tgt, catnames))
        if not card:
            card = random_choose_card(cats)
            if not card:
                return False

        self.card = card
        g.players.exclude(tgt).reveal(card)
        g.process_action(
            DropCards(target=tgt, cards=[card])
        )
        return True


class LittleLegionHandler(EventHandler):
    interested = ('choose_target', 'post_card_migration')
    def handle(self, evt_type, arg):
        if evt_type == 'choose_target':
            lca, tl = arg
            if 'equipment' not in lca.card.category: return arg

            src = lca.source
            if src.dead or not src.has_skill(LittleLegion): return arg
            if not user_input([src], ChooseOptionInputlet(self, (False, True))):
                return arg
            g = Game.getgame()
            g.process_action(LittleLegionDrawCards(src, 1))

        elif evt_type == 'post_card_migration':
            pl = set([_from.owner for _, _from, _ in arg
                      if _from is not None and _from.type == 'equips'])
            pl = [p for p in pl if p.has_skill(LittleLegion) and not p.dead]

            g = Game.getgame()
            for p in pl:
                self.source = p
                if not user_input([p], ChooseOptionInputlet(self, (False, True))):
                    continue
                tl = user_choose_players(self, p, g.players.exclude(p))
                if tl:
                    assert len(tl) == 1
                    g.process_action(LittleLegionAction(p, tl[0]))

        return arg

    def cond(self, cl):
        return True

    def choose_player_target(self, tl):
        if not tl:
            return tl, False

        tgt = tl[0]
        if tgt is self.source:
            return [], False

        return ([tgt], bool(tgt.equips or tgt.cards or tgt.showncards))


class MaidensBunraku(Skill):
    associated_action = None
    skill_category = ('character', 'passive')
    target = t_None


class MaidensBunrakuHandler(EventHandler):
    interested = ('action_apply',)
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, DropCardStage):
            tgt = act.target
            if not tgt.has_skill(MaidensBunraku): return act
            amount = (len(tgt.equips) + 1) / 2
            act.dropn -= amount if amount > 1 else 1

        return act


@register_character
class Alice(Character):
    skills = [LittleLegion, MaidensBunraku]
    eventhandlers_required = [LittleLegionHandler, MaidensBunrakuHandler]
    maxlife = 3
