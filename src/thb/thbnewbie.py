# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from enum import Enum
from itertools import chain, combinations, cycle
from typing import Any, Callable, Dict, List, cast
import logging
import random

# -- third party --
# -- own --
from game.base import BootstrapAction, Game, GameItem, InputTransaction, InterruptActionFlow, NPC
from game.base import Player
from thb.actions import ActionStage, ActionStageLaunchCard, CardChooser, DrawCards, DropCards, GenericAction
from thb.actions import FatetellStage, LaunchCard, PlayerDeath, PlayerTurn, RevealRole
from thb.actions import ask_for_action, migrate_cards
from thb.cards.base import Card, Deck
from thb.cards.classes import AskForHeal, AttackCard, Demolition, DemolitionCard
from thb.cards.classes import ElementalReactorCard, ExinwanCard, FrozenFrogCard, GrazeCard
from thb.cards.classes import GreenUFOCard, Heal, HealCard, LaunchGraze, MomijiShieldCard
from thb.cards.classes import NazrinRodCard, RedUFOCard, Reject, RejectCard, RejectHandler
from thb.cards.classes import SinsackCard, WineCard
from thb.common import PlayerRole
from thb.inputlets import ActionInputlet, GalgameDialogInputlet
from thb.mode import THBEventHandler, THBattle
from utils.misc import BatchList


# -- code --
log = logging.getLogger('THBattleNewbie')


class OneShotActionStage(ActionStage):
    one_shot = True


class DeathHandler(THBEventHandler):
    interested = ['action_apply']

    def handle(self, evt_type, act):
        if evt_type != 'action_apply': return act
        if not isinstance(act, PlayerDeath): return act
        tgt = act.target

        g = self.game
        pl = g.players

        g.winners = [pl[1]] if tgt is pl[0] else [pl[0]]
        g.game_end()

        return act


class THBNewbieRole(Enum):
    HIDDEN = 0
    NEWBIE = 1
    BAKA = 2


class CirnoAI(object):

    def __init__(self, trans, ilet):
        self.trans = trans
        self.ilet = ilet

    def entry(self):
        ilet = self.ilet
        trans = self.trans
        p = ilet.actor

        g = self.game
        g.pause(1.2)

        if trans.name == 'ActionStageAction':
            tl = g.players[1:]
            cl = list(p.showncards) + list(p.cards)
            if random.random() > 0.6:
                return False

            for c in cl:
                if c.is_card(AttackCard):
                    if self.try_launch(c, tl[:1]): return True

        elif trans.name == 'Action' and isinstance(ilet, ActionInputlet):
            if not (ilet.categories and not ilet.candidates):
                return True

            if isinstance(ilet.initiator, AskForHeal):
                return False

            cond = cast(CardChooser, ilet.initiator).cond
            cl = list(p.showncards) + list(p.cards)
            _, C = chain, lambda r: combinations(cl, r)
            for c in _(C(1), C(2)):
                if cond(c):
                    ilet.set_result(skills=[], cards=c, players=[])
                    return True

        elif trans.name == 'ChoosePeerCard':
            tgt = ilet.target
            if tgt.cards:
                ilet.set_card(tgt.cards[0])
            elif tgt.showncards:
                ilet.set_card(tgt.showncards[0])

    def try_launch(self, c, tl, skills=[]):
        p = self.ilet.actor
        act = ActionStageLaunchCard(p, tl, c)
        if act.can_fire():
            self.ilet.set_result(skills=skills, cards=[c], players=tl)
            return True

        return False

    @classmethod
    def ai_main(cls, trans, ilet):
        cls(trans, ilet).entry()


class AdhocEventHandler(THBEventHandler):
    def __init__(self, g: Game, hook: Callable[[str, Any], Any]):
        self._handle = hook  # typing: ignore

    def handle(self, evt_type: str, arg: Any) -> Any:
        return self._handle(evt_type, arg)


class DrawShownCards(DrawCards):
    def __init__(self, target, amount=2):
        self.source = self.target = target
        self.amount = amount

    def apply_action(self):
        g = self.game
        target = self.target

        cards = g.deck.getcards(self.amount)

        target.reveal(cards)
        migrate_cards(cards, target.showncards)
        self.cards = cards
        return True

    def is_valid(self):
        return not self.target.dead


class DummyPlayerTurn(PlayerTurn):
    def apply_action(self):
        return True


class THBattleNewbieBootstrap(BootstrapAction):
    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        self.source = self.target = None
        self.players = players
        self.params = params
        self.items = items

    def apply_action(self):
        g = self.game

        from thb.characters.meirin import Meirin
        from thb.characters.cirno import Cirno

        # ----- Init -----
        pl = self.players
        g.deck = Deck(g)

        cirno_p, meirin_p = pl

        g.roles = {
            cirno_p: PlayerRole(THBNewbieRole),
            meirin_p: PlayerRole(THBNewbieRole),
        }
        g.roles[cirno_p].set(THBNewbieRole.BAKA)
        g.roles[meirin_p].set(THBNewbieRole.NEWBIE)

        g.process_action(RevealRole(g.roles[cirno_p], pl))
        g.process_action(RevealRole(g.roles[meirin_p], pl))

        cirno = Cirno(cirno_p)
        meirin = Meirin(meirin_p)

        g.players = BatchList([cirno, meirin])

        g.refresh_dispatcher()
        g.emit_event('switch_character', (None, cirno))
        g.emit_event('switch_character', (None, meirin))

        g.emit_event('game_begin', g)
        # ----- End Init -----

        pt = PlayerTurn(cirno)
        pt.pending_stages = [ScriptedStage]
        g.process_action(pt)

        for i, idx in enumerate(cycle([1, 0])):
            p = g.players[idx]
            if i >= 6000: break
            try:
                g.process_action(PlayerTurn(p))
            except InterruptActionFlow:
                pass

        return True


class ScriptedStage(GenericAction):
    def __init__(self, target):
        self.source = target
        self.target = target

    def apply_action(self):
        g = self.game

        from thb.characters.meirin import Meirin
        from thb.characters.cirno import Cirno
        from thb.characters.sakuya import Sakuya

        def dialog(character, dialog, voice):
            if voice is not None:
                voice = 'thb-cv-newbie-%s-%s' % (character.__name__.lower(), ('000' + str(voice))[-3:])

            g.user_input([meirin], GalgameDialogInputlet(g, character, dialog, voice), timeout=60)

        def inject_eh(hook: Callable[[str, Any], Any]):
            eh = AdhocEventHandler(g, hook)
            g.add_adhoc_event_handler(eh)
            return eh

        def remove_eh(eh):
            try:
                g.remove_adhoc_event_handler(eh)
            except Exception:
                pass

        def fail():
            dialog(Meirin, '喂剧本不是这么写的啊，重来重来！', 1)

        cirno, meirin = g.players  # update
        turn = PlayerTurn.get_current(g)

        dialog(Meirin, '一个pad，两个pad，三个pad……', 2)
        dialog(Sakuya, '（唰', None)
        dialog(Meirin, '啊，我头上的是……', 3)
        dialog(Sakuya, '别做白日梦，起床了起床了。那边那个妖精可又来门口找麻烦了，为了你的晚餐考虑，还是去解决一下吧？', 1)
        dialog(Meirin, '是是是……这都已经是第999次了吧，那家伙真是不知道什么叫做放弃吗……', 4)

        dialog(Cirno, '俺又来啦，这次绝对要打赢你！赌上大酱的100场陪练！', 1)
        dialog(Meirin, '前面998次你也都是这么说的……好了，废话少说，放马过来吧！', 5)
        dialog(Cirno, '正合我意！', 2)

        turn.target = cirno

        c = g.deck.inject(AttackCard, Card.SPADE, 1)
        g.process_action(DrawCards(cirno, 1))
        dialog(Cirno, '“吃我大弹幕啦！”', 3)
        g.process_action(LaunchCard(cirno, [meirin], c))

        # 红美铃受到一点伤害

        dialog(Meirin, '呜哇！？', 6)
        dialog(Sakuya, '怎么搞的，被一只妖精弄伤了？', 2)
        dialog(Meirin, '不不不，那个咲夜你听我说，这是偷袭……', 7)
        dialog(Sakuya, '嗯……明明游戏已经开始了，不打起十二分的精神迎战可是不行的啊。在玩thb的时候请注意队友的感受，不要挂机喔。', 3)
        dialog(Meirin, '啥啊又在对着不存在的人说些莫名其妙的东西……', 8)
        dialog(Sakuya, '嗯？', 4)
        dialog(Meirin, '我可什么都没说！', 9)

        # 红美铃的回合【目的:使用基本牌（麻薯，弹幕）】
        turn.target = meirin
        c = g.deck.inject(HealCard, Card.HEART, 2)
        g.process_action(DrawCards(meirin, 1))

        while c in meirin.cards:
            text = (
                '总之，这里先回复……\n'
                '（请使用麻薯）\n'
                '（在PC版中鼠标移动到卡牌/人物上，或者手机版中长按卡牌/人物头像，就会弹出说明，很有用的）'
            )
            dialog(Meirin, text, 10)
            g.process_action(OneShotActionStage(meirin))

        atkcard = g.deck.inject(AttackCard, Card.SPADE, 3)
        g.process_action(DrawCards(meirin, 1))

        while atkcard in meirin.cards:
            text = (
                '好，状态全满！那边的妖精！吃我大弹幕啦！\n'
                '（请首先点击弹幕，然后点击琪露诺，最后点击出牌）\n'
                '（在PC版中鼠标移动到卡牌/人物上，或者手机版中长按卡牌/人物头像，就会弹出说明，很有用的）'
            )
            dialog(Meirin, text, 11)
            g.process_action(OneShotActionStage(meirin))

        dialog(Cirno, '哎呀！？', 4)
        dialog(Sakuya, '啊啦，干的不错。', 5)
        dialog(Meirin, '那是自然啦，对付一些这样的妖精还是不在话下的……', 12)
        dialog(Cirno, '喂！悄悄话说的也太大声了！！', 5)

        # 琪露诺的回合【目的:使用基本牌（擦弹）】【使用太极（1）】
        turn.target = cirno
        g.deck.inject(HealCard, Card.HEART, 4)
        g.process_action(DrawCards(cirno, 1))
        while True:
            if meirin.life < meirin.maxlife:
                g.process_action(Heal(meirin, meirin, meirin.maxlife - meirin.life))

            if meirin.cards:
                g.process_action(DropCards(meirin, meirin, meirin.cards))

            atkcard = g.deck.inject(AttackCard, Card.SPADE, 5)
            g.process_action(DrawCards(cirno, 1))
            graze = g.deck.inject(GrazeCard, Card.DIAMOND, 6)
            g.process_action(DrawCards(meirin, 1))

            dialog(Cirno, '这回就轮到我了！接招！超⑨武神霸斩！', 6)

            lc = LaunchCard(cirno, [meirin], atkcard)

            @inject_eh
            def resp(evt_type: str, act: Any):
                if evt_type == 'choose_target' and act[0] is lc:
                    g.pause(1)
                    dialog(Meirin, '来的正好！', 13)

                elif evt_type == 'action_after' and isinstance(act, LaunchGraze) and act.succeeded:
                    g.pause(1)
                    dialog(Cirno, '我的计谋竟被……', 7)
                    text = (
                        '还没完呐！\n'
                        '（使用技能，震飞琪露诺一张手牌）\n'
                        '（每一名角色都有自己独特的技能，灵活利用好这些技能是你取得胜利的关键所在）'
                    )
                    dialog(Meirin, text, 14)

                return act

            g.process_action(lc)
            remove_eh(resp)

            if graze in meirin.cards or cirno.cards:
                fail()
                continue

            break

        dialog(Cirno, '切，再让你嘚瑟一会儿，我还有自己的杀手锏呢……', 8)
        dialog(Meirin, '在这种时候放空话可是谁都不会相信的啦。', 15)
        green = g.deck.inject(GreenUFOCard, Card.DIAMOND, 7)
        g.process_action(DrawCards(cirno, 1))
        dialog(Cirno, '总之不能再让你这么自在地用弹幕打到俺了……看我的杀手锏！', 9)
        g.process_action(LaunchCard(cirno, [cirno], green))

        dialog(Meirin, '咦……', 16)
        dialog(Sakuya, '不会连这个你也不清楚吧。', 6)
        dialog(Meirin, '我记得是记得啦，似乎是我现在够不到琪露诺了之类的而琪露诺可以够到我……吧？说回来，这样的解释似乎很不科学诶，为什么我够不到但是对方够得到我啊，这个|G绿色UFO|r到底是什么东西……', 17)
        dialog(Sakuya, '……你只要好好打完这局就可以了，再问这么多为什么，我可不保证你的脑门上会多出什么奇怪的金属制品。', 7)
        dialog(Meirin, '是！', 18)

        # 红美铃的回合【目的:使用延时符卡（冻青蛙），使用太极（2），使用红色UFO】'
        turn.target = meirin
        frozen = g.deck.inject(FrozenFrogCard, Card.SPADE, 8)
        g.process_action(DrawCards(meirin, 1))

        dialog(Meirin, '咦，这张牌是……', 19)
        dialog(Sakuya, '这是|G冻青蛙|r。\n（咳嗽了一声）|G冻青蛙|r是一种|R延时符卡|r，它和|G封魔阵|r一样在使用时并不会立即发生作用，只有轮到了那个角色的行动回合时，才会进行一次判定来执行该符卡的后续效果。', 8)
        dialog(Meirin, '原来是这样……那就先贴到她脸上再说！', 20)

        g.process_action(OneShotActionStage(meirin))

        dialog(Meirin, '这是怎么回事…为什么不能使用…那就先来一发|G弹幕|r好了！', 21)

        atkcard = g.deck.inject(AttackCard, Card.SPADE, 9)
        g.process_action(DrawCards(meirin, 1))

        g.process_action(OneShotActionStage(meirin))

        dialog(Meirin, '咲夜咲夜咲夜，我没法打她啊！', 22)
        dialog(Sakuya, '……你忘了琪露诺的|G绿色UFO|r吗。现在从你这边看来和琪露诺的距离为2，也就是，赤手空拳的距离1是没有办法用|G弹幕|r打中她的。我记得鬼族有她们的方法，但是很显然你并不会。', 9)
        dialog(Meirin, '好吧……所以？', 23)
        dialog(Sakuya, '（掏出飞刀', None)
        dialog(Meirin, '好啦好啦，我不问啦！', 24)

        red = g.deck.inject(RedUFOCard, Card.HEART, 10)
        g.process_action(DrawCards(meirin, 1))

        while red in meirin.cards:
            text = (
                '哈，我找到了这个！\n'
                '（红色UFO可以拉近其他角色与你的距离，快装备上吧）'
            )
            dialog(Meirin, text, 25)
            g.process_action(OneShotActionStage(meirin))

        dialog(Sakuya, '你这不是知道UFO的规则嘛。', 10)
        dialog(Meirin, '只是想趁这次机会和咲夜多说说话啦，平时总是一副大忙人的样子来无影去无踪的……', 26)
        dialog(Sakuya, '你以为奉承一下我就会给你涨工资吗。', 11)
        dialog(Meirin, '啊哈，啊哈哈。', 27)

        g.pause(1)

        g.deck.inject(NazrinRodCard, Card.HEART, 11)
        graze = g.deck.inject(GrazeCard, Card.DIAMOND, 12)
        g.process_action(DrawCards(cirno, 2))

        while True:
            if atkcard not in meirin.cards:
                atkcard = g.deck.inject(AttackCard, Card.SPADE, 9)
                g.process_action(DrawCards(meirin, 1))

            if graze not in cirno.cards:
                graze = g.deck.inject(GrazeCard, Card.DIAMOND, 12)
                g.process_action(DrawCards(cirno, 1))

            dialog(Cirno, '喂，读条要过了你们在那儿干嘛呢，说好的弹幕呢！', 10)
            dialog(Meirin, '我这辈子还没听过这么欠扁的要求！吃我一弹！', 28)

            @inject_eh
            def handle_longquan(evt_type: str, act: Any):
                if evt_type == 'action_after' and isinstance(act, LaunchGraze) and act.target is cirno:
                    g.pause(1)
                    dialog(Cirno, '你以为只有你会闪开吗！', 11)
                    dialog(Meirin, '确实谁都会闪啦，不过接下来的，可就不是谁都会的咯？', 29)

                return act

            g.process_action(OneShotActionStage(meirin))
            remove_eh(resp)

            if atkcard in meirin.cards:
                continue

            if cirno.cards:
                fail()
                continue

            break

        g.pause(1)
        dialog(Cirno, '呜哇你赖皮！', 12)
        dialog(Meirin, '哪来的什么赖皮不赖皮，我有自己的能力，但是你也有啊。', 30)
        dialog(Cirno, '可是我又不会用！你这不是赖皮是什么嘛！', 13)
        dialog(Meirin, '……', None)
        dialog(Sakuya, '……还是不要跟笨蛋说话的比较好，智商会下降的。', 12)

        while frozen in meirin.cards:
            dialog(Meirin, '那么，把这张|G冻青蛙|r也贴上去吧！', 31)
            g.process_action(ActionStage(meirin))

        turn.target = cirno
        g.deck.inject(SinsackCard, Card.SPADE, 13)
        g.process_action(FatetellStage(cirno))

        g.pause(2)

        dialog(Sakuya, '所谓“笨蛋的运气总会很不错”吗。', 13)
        dialog(Cirno, '哼，俺可是自带⑨翅膀的天才呀！', 14)
        dialog(Meirin, '可惜依旧是笨蛋。', 32)

        shield = g.deck.inject(MomijiShieldCard, Card.SPADE, 1)
        g.process_action(DrawCards(cirno, 1))
        dialog(Cirno, '无路赛……我要出王牌啦！', 15)
        g.process_action(LaunchCard(cirno, [cirno], shield))

        dialog(Meirin, '这是……', 33)
        dialog(Cirno, '这是我在妖怪之山的妖精那里【借】来的宝物，怎么样，接下来你就没办法用弹幕伤到俺了吧~', 16)
        dialog(Sakuya, '只是黑色的弹幕无效而已。', 14)
        dialog(Meirin, '对呀对呀。', 34)
        dialog(Sakuya, '而且，只要拆掉的话不就好了吗。', 15)
        dialog(Meirin, '对呀对……啥？', 35)
        dialog(Sakuya, '真是的，你之前的998局到底是怎么赢的……', 16)

        # 红美铃的回合【目的:使用符卡（城管执法，好人卡）】
        turn.target = meirin

        demolition = g.deck.inject(DemolitionCard, Card.CLUB, 2)
        g.process_action(DrawCards(meirin, 1))
        cirnoreject = g.deck.inject(RejectCard, Card.CLUB, 3)
        g.process_action(DrawCards(cirno, 1))

        while demolition in meirin.cards:
            dialog(Meirin, '咲夜咲夜！', 36)
            dialog(Sakuya, '是啦，这就是我说的那张符卡了。和其他的|R非延时符卡|r使用方法都一样，属于发动之后就会立即生效的类型。', 17)
            dialog(Meirin, '……不是很好理解诶。', 37)

            dialog(Sakuya, '用用看就知道了。快去卸掉她的|G天狗盾|r吧。', 18)

            @inject_eh
            def handle_rejectcard(evt_type: str, act: Any):
                if evt_type == 'action_before' and isinstance(act, Demolition):
                    g.pause(1.5)
                    dialog(Cirno, '哈哈，早知道你会用这一招，怎能让你轻易得逞！', 17)
                    g.process_action(LaunchCard(cirno, [cirno], cirnoreject, Reject(cirno, act)))

                elif evt_type == 'action_before' and isinstance(act, Reject) and act.associated_card is cirnoreject:
                    g.pause(1.5)
                    dialog(Meirin, '这又是怎么回事……好像|G城管执法|r并没有起作用？', 38)
                    dialog(Sakuya, '咦，这笨蛋居然知道用|G好人卡|r啊……', 19)
                    dialog(Cirno, '什么笨蛋，老娘是天才，天～才～', 18)
                    text = (
                        '|G好人卡|r的效果是|R抵消符卡效果|r，也就是说，你的|G城管执法|r的效果被无效化了。\n'
                        '（在PC版中鼠标移动到卡牌/人物上，或者手机版中长按卡牌/人物头像，就会弹出说明，很有用的）'
                    )
                    dialog(Sakuya, text, 20)
                    dialog(Sakuya, '但是，|G好人卡|r的“无效符卡”的效果，本身也是符卡效果，是可以被|G好人卡|r抵消的！', 21)

                    meirinreject = g.deck.inject(RejectCard, Card.CLUB, 4)
                    g.process_action(DrawCards(meirin, 1))

                    while not act.cancelled:
                        dialog(Meirin, '我知道了，我也用|G好人卡|r去抵消她的|G好人卡|r效果就好了！', 39)

                        rej = RejectHandler(g)
                        rej.target_act = act
                        with InputTransaction('AskForRejectAction', [meirin]) as trans:
                            p, rst = ask_for_action(rej, [meirin], ('cards', 'showncards'), [], trans=trans)

                        if not p: continue
                        assert rst
                        cards, _ = rst
                        assert cards[0] is meirinreject
                        g.process_action(LaunchCard(meirin, [cirno], meirinreject, Reject(meirin, act)))

                return act

            g.process_action(OneShotActionStage(meirin))
            remove_eh(resp)

        if shield in cirno.equips:
            dialog(Sakuya, '喂，不是说要拆掉|G天狗盾|r吗，你明明装备着|G红色UFO|r的，她是在你的距离范围内的。', 22)
            dialog(Meirin, '哎呀，手抖了的说……', 40)
        else:
            dialog(Cirno, '呜哇你赔我的|G天狗盾|r！', 19)
            dialog(Meirin, '怪我咯！？', 41)

        g.deck.inject(ExinwanCard, Card.CLUB, 3)
        g.process_action(DrawCards(meirin, 1))

        dialog(Meirin, '咦？咲夜，这张牌好奇怪……为什么是负面的效果？', 42)
        dialog(Sakuya, '是|G恶心丸|r啊……你的运气不太好哦。不过尽管说是一张负面效果的牌，但是看发动条件的话，是可以恶心到别人的。情况允许的话就留在手里好了，直接吃掉肯定是不合算的。', 23)

        turn.target = cirno
        demolition = g.deck.inject(DemolitionCard, Card.CLUB, 4)
        g.process_action(DrawCards(cirno, 1))
        dialog(Cirno, '可恶，你到底有没有认真的在打啊！看我双倍奉还！', 20)
        g.process_action(LaunchCard(cirno, [meirin], demolition))

        dialog(Cirno, '呜哇，这是什么！不要来找我！', 21)
        dialog(Meirin, '哈哈，说好的双倍奉还呢？', 43)

        # 美铃的觉醒和主动技能
        er = g.deck.inject(ElementalReactorCard, Card.DIAMOND, 5)
        atks = [g.deck.inject(AttackCard, Card.SPADE, i) for i in (6, 7, 8, 9)]
        g.process_action(DrawCards(cirno, 5))
        dialog(Cirno, '真是伤脑筋……看来我要拿出真正的实力来了！', 22)
        g.process_action(LaunchCard(cirno, [cirno], er))

        dialog(Cirno, '接招啦！！', 23)

        for c in atks[:-1]:
            g.pause(0.5)
            g.process_action(LaunchCard(cirno, [meirin], c))

        dialog(Meirin, '唔，不好，再这样下去就要撑不住了……', 44)
        wine = g.deck.inject(WineCard, Card.DIAMOND, 10)
        g.process_action(DrawCards(meirin, 1))

        while wine in meirin.cards:
            dialog(Meirin, '没办法，这瓶|G酒|r本来是想留着|R来一发2点伤害的弹幕|r用的，现在只能用来|R抵挡1点致命伤害|r了……', 45)
            g.process_action(ActionStage(meirin))

        g.pause(0.5)
        g.process_action(LaunchCard(cirno, [meirin], atks[-1]))

        g.pause(0.5)
        dialog(Cirno, '怎么样，老娘最强！', 24)

        dialog(Meirin, '呼呼，撑过来了……', 46)
        dialog(Meirin, '咲夜，这是怎么回事？|G弹幕|r不应该|R一回合只能使用一次|r吗？', 47)
        dialog(Sakuya, '嗯……说的不错。|R一回合只能使用一次|r这个规则是没错啦，不过你看她的手上，是河童们研制的迷你|G八卦炉|r，只要装备上的话，一回合就可以使用任意次数的|G弹幕|r了。', 24)
        dialog(Meirin, '你这家伙好像【借】来了不少东西嘛……不过笨蛋就是笨蛋，我怎么可能会输在笨蛋的手上！', 48)

        g.process_action(DummyPlayerTurn(meirin))  # awake!
        g.pause(2)

        dialog(Cirno, '你怎么会突然多出来一个技能，这一点也不公平！', 25)
        dialog(Sakuya, '“笨蛋就是笨蛋”这句话说的一点没错……你像这样打伤美铃，触发了美铃的|R觉醒技|r。|R觉醒技|r通常都是很厉害的技能，但是要满足一定条件以后才可以开始使用。据我所知，那个三途川的草鞋船夫也有类似的能力，而美铃的觉醒技，就是|G太极|r了。', 25)
        dialog(Cirno, '啊，原来是这样……不不，才不是笨蛋，老娘最强！', 26)

        graze = g.deck.inject(GrazeCard, Card.DIAMOND, 11)
        g.process_action(DrawCards(meirin, 1))

        while graze in meirin.cards:
            text = (
                '现在说不是笨蛋是不是有点晚啊……见识一下吧，这来自古老东方的两仪|G太极|r之力！\n'
                '（使用主动发动的技能：请点击技能按钮，然后选择擦弹，然后选择琪露诺，最后出牌）'
            )
            dialog(Meirin, text, 49)
            g.process_action(OneShotActionStage(meirin))

        dialog(Cirno, '呜啊……', 27)
        dialog(Sakuya, '我要回去做晚饭了。一会儿到了饭点你还没有解决掉这个妖精，我可不会给你留吃的。', 26)
        dialog(Meirin, '喂咲夜你先等等……', 50)
        dialog(Sakuya, '（The World', None)
        dialog(Meirin, '……好吧。那边的妖精！', 51)
        dialog(Cirno, '诶？', 28)
        dialog(Meirin, '以晚饭之名！我要制裁你！', 52)
        dialog(Cirno, '虽然不知道为什么突然燃起了斗志，不过……', 29)
        dialog(Cirno, '来吧！老娘是不可能会输的！', 30)

        g.process_action(Heal(cirno, cirno, cirno.maxlife - cirno.life))
        g.process_action(Heal(meirin, meirin, meirin.maxlife - meirin.life))
        g.process_action(DrawCards(cirno, 4))
        g.process_action(DrawCards(meirin, 4))


class THBattleNewbie(THBattle):
    n_persons   = 1
    game_ehs    = [DeathHandler]
    npc_players = [NPC('琪露诺', CirnoAI.ai_main)]
    bootstrap   = THBattleNewbieBootstrap

    def can_leave(g, p):
        return True
