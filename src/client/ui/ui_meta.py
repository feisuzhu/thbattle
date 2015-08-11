# -*- coding: utf-8 -*-

from utils import ObjectDict

# -----BEGIN BADGES UI META-----
badges = {}


def badge_metafunc(clsname, bases, _dict):
    _dict.pop('__module__')
    data = ObjectDict.parse(_dict)
    badges[clsname] = data

__metaclass__ = badge_metafunc


class dev:
    badge_anim = 'c-badges-dev'
    badge_text = u'符斗祭程序开发组成员'


class jcb_1_gold:
    badge_anim = 'c-badges-jcb_gold'
    badge_text = u'第一届“节操杯”符斗祭比赛冠军队'


class jcb_1_silver:
    badge_anim = 'c-badges-jcb_silver'
    badge_text = u'第一届“节操杯”符斗祭比赛亚军队'


class jcb_1_bronze:
    badge_anim = 'c-badges-jcb_bronze'
    badge_text = u'第一届“节操杯”符斗祭比赛季军队'


class jcb_2_gold:
    badge_anim = 'c-badges-jcb_gold'
    badge_text = u'第二届“节操杯”符斗祭比赛冠军队'


class jcb_2_silver:
    badge_anim = 'c-badges-jcb_silver'
    badge_text = u'第二届“节操杯”符斗祭比赛亚军队'


class jcb_2_bronze:
    badge_anim = 'c-badges-jcb_bronze'
    badge_text = u'第二届“节操杯”符斗祭比赛季军队'


class jcb_3_gold:
    badge_anim = 'c-badges-jcb_gold'
    badge_text = u'第三届“节操杯”符斗祭比赛冠军队'


class jcb_3_silver:
    badge_anim = 'c-badges-jcb_silver'
    badge_text = u'第三届“节操杯”符斗祭比赛亚军队'


class jcb_3_bronze:
    badge_anim = 'c-badges-jcb_bronze'
    badge_text = u'第三届“节操杯”符斗祭比赛季军队'


class jcb_4_gold:
    badge_anim = 'c-badges-jcb_gold'
    badge_text = u'第四届“节操杯”符斗祭比赛冠军队'


class jcb_4_silver:
    badge_anim = 'c-badges-jcb_silver'
    badge_text = u'第四届“节操杯”符斗祭比赛亚军队'


class jcb_4_bronze:
    badge_anim = 'c-badges-jcb_bronze'
    badge_text = u'第四届“节操杯”符斗祭比赛季军队'


class jcb_5_gold:
    badge_anim = 'c-badges-jcb_gold'
    badge_text = u'第五届“节操杯”符斗祭比赛冠军队'


class jcb_5_silver:
    badge_anim = 'c-badges-jcb_silver'
    badge_text = u'第五届“节操杯”符斗祭比赛亚军队'


class jcb_5_bronze:
    badge_anim = 'c-badges-jcb_bronze'
    badge_text = u'第五届“节操杯”符斗祭比赛季军队'


class dsb_1_gold:
    badge_anim = 'c-badges-dsb_gold'
    badge_text = u'第一届大师杯冠军'


class dsb_1_silver:
    badge_anim = 'c-badges-dsb_silver'
    badge_text = u'第一届大师杯亚军'


class dsb_1_bronze:
    badge_anim = 'c-badges-dsb_bronze'
    badge_text = u'第一届大师杯季军'


class dsb_2_gold:
    badge_anim = 'c-badges-dsb_gold'
    badge_text = u'第二届大师杯冠军'


class dsb_2_silver:
    badge_anim = 'c-badges-dsb_silver'
    badge_text = u'第二届大师杯亚军'


class dsb_2_bronze:
    badge_anim = 'c-badges-dsb_bronze'
    badge_text = u'第二届大师杯季军'


class xyb_1_gold:
    badge_anim = 'c-badges-dsb_gold'
    badge_text = u'第一届信仰杯冠军'


class xyb_1_silver:
    badge_anim = 'c-badges-dsb_silver'
    badge_text = u'第一届信仰杯亚军'


class xyb_1_bronze:
    badge_anim = 'c-badges-dsb_bronze'
    badge_text = u'第一届信仰杯季军'


class fff_1_gold:
    badge_anim = 'c-badges-fff_gold'
    badge_text = u'第一届“FFF杯”符斗祭比赛冠军队'


class fff_1_silver:
    badge_anim = 'c-badges-fff_silver'
    badge_text = u'第一届“FFF杯”符斗祭比赛亚军队'


class fff_2_bronze:
    badge_anim = 'c-badges-fff_bronze'
    badge_text = u'第二届“FFF杯”符斗祭比赛季军队'


class fff_2_gold:
    badge_anim = 'c-badges-fff_gold'
    badge_text = u'第二届“FFF杯”符斗祭比赛冠军队'


class fff_2_silver:
    badge_anim = 'c-badges-fff_silver'
    badge_text = u'第二届“FFF杯”符斗祭比赛亚军队'


class fff_1_bronze:
    badge_anim = 'c-badges-fff_bronze'
    badge_text = u'第二届“FFF杯”符斗祭比赛季军队'


class contributor:
    badge_anim = 'c-badges-contributor'
    badge_text = (
        u'|B符斗祭贡献者|r\n\n'
        u'在官方发起的公开任务中积极参与并做出贡献的玩家'
    )


# -----END BADGES UI META-----
