# -*- coding: utf-8 -*-
from game.autoenv import EventHandler, user_input, Game
from baseclasses import Character, register_character
from ..actions import DrawCards, UserAction, ActionStageLaunchCard, user_choose_players, DropCards
from ..cards import Skill, TreatAsSkill, AttackCardHandler, DollControlCard, t_None
from ..inputlets import ChoosePeerCardInputlet, ChooseOptionInputlet


class LittleLegion(Skill):
    pass


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
    execute_after = ('ElementalReactorHandler', )

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


class MaidensBunraku(TreatAsSkill):
    treat_as = DollControlCard

    def check(self):
        cl = self.associated_cards
        if not cl and len(cl) == 1: return False
        c = cl[0]
        if c.resides_in.type not in ('cards', 'showncards', 'equips'):
            return False

        return 'instant_spellcard' in c.category


class MaidensBunrakuHandler(EventHandler):
    def handle(self, evt_type, arg):
        if evt_type == 'action_after' and isinstance(arg, ActionStageLaunchCard):
            c = arg.card
            if c.is_card(MaidensBunraku):
                src = arg.source
                src.tags['alice_bunraku_tag'] = src.tags['turn_count']

        elif evt_type == 'action_can_fire':
            act, valid = arg
            if isinstance(act, ActionStageLaunchCard):
                c = act.card
                if c.is_card(MaidensBunraku):
                    t = act.source.tags
                    if t['alice_bunraku_tag'] >= t['turn_count']:
                        return act, False

        return arg

@register_character
class Alice(Character):
    skills = [LittleLegion, MaidensBunraku]
    eventhandlers_required = [LittleLegionHandler, MaidensBunrakuHandler]
    maxlife = 4
