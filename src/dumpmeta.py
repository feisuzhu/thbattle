# -*- coding: utf-8 -*-
# flake8: noqa

import sys
import os.path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# -- stdlib --
import gc
import json
import sys

# -- third party --
# -- own --
import game
import thb.meta


# -- code --

kls = [
    c for c in gc.get_objects()
    if isinstance(c, type) and issubclass(c, game.base.GameObject)
]

intermediates = set()
for c in kls:
    intermediates.update(c.__bases__)

is_leaf = lambda c: c not in intermediates

modes = [c for c in kls if issubclass(c, game.base.Game) and is_leaf(c)]

roles = {}
for m in modes:
    roles.update(m.ui_meta.roles)

roles = [{'Name': v['name'], 'Type': k} for k, v in roles.items()]

# ----------
chars = [c for c in kls if issubclass(c, thb.characters.base.Character) and is_leaf(c)]
char_cls = chars
chars = {}

for c in char_cls:
    chars[c.__name__] = {
        'Type': c.__name__,
        'Name': c.ui_meta.name,
        'MaxLife': c.maxlife,
        'Title': c.ui_meta.title,
        'Designer': getattr(c.ui_meta, 'designer', ''),
        'Illustrator': getattr(c.ui_meta, 'illustrator', ''),
        'CharacterVoice': getattr(c.ui_meta, 'cv', ''),
    }


chars = list(chars.values())


# ----------
def distadj(c):
    if sk := getattr(c, 'equipment_skill', None):
        if c.equipment_category == 'weapon':
            return sk.range
        elif issubclass(sk, thb.cards.equipment.UFOSkill):
            return sk.increment
    return 0


card_cls = [
    c for c in kls
    if issubclass(c, thb.cards.base.PhysicalCard)
    and is_leaf(c)
    and c not in (thb.cards.base.DummyCard, thb.characters.parsee.EnvyRecycle)
]


physical_cards = {}


for c in card_cls:
    physical_cards[c.__name__] = {
        'Type': c.__name__,
        'Name': c.ui_meta.name,
        'Categories': c.category,
        'EquipmentCategory': getattr(c, 'equipment_category', ''),
        'DistanceAdjust': distadj(c),
        'Description': c.ui_meta.description,
    }


physical_cards = list(physical_cards.values())


# ----------
skill_cls = [
    c for c in kls
    if issubclass(c, thb.cards.base.Skill) and is_leaf(c)
]

skills = {}
for c in skill_cls:
    skills[c] = {
        'Type': c.__name__,
        'Name': c.ui_meta.name,
        'SkillCategories': c.skill_category,
        'ParamsUIId': getattr(c.ui_meta, 'params_ui', ''),
        'Description': getattr(c.ui_meta, 'description', None),
    }


skills = list(skills.values())

# ----------
modes_cls = modes
modes = {}

for c in modes_cls:
    modes[c] = {
        'Type': c.__name__,
        'Name': c.ui_meta.name,
        'Roles': {
            k: None for k in c.ui_meta.roles
        }
    }

modes = list(modes.values())

# ----------
ilets = {}
ilet_cls = [c for c in kls if issubclass(
    c, thb.inputlets.Inputlet) and c is not thb.inputlets.Inputlet]
ilets = [v.tag() for v in ilet_cls]
ilets = [v for v in ilets if v]

# =========================
rst = {
    'Characters': {v['Type']: json.dumps(v) for v in chars},
    'UIMetaInputHandlers': json.dumps(ilets),
    'PhysicalCards': {v['Type']: json.dumps(v) for v in physical_cards},
    'RoleDefinitions': {v['Type']: json.dumps(v) for v in roles},
    'Skills': {v['Type']: json.dumps(v) for v in skills},
    'Modes': {v['Type']: json.dumps(v) for v in modes},
}

print(json.dumps(rst))
