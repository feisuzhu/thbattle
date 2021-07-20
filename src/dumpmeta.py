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
    if (
        issubclass(c, thb.cards.base.PhysicalCard) or
        issubclass(c, thb.cards.base.TreatAs)
    )
    and is_leaf(c)
    and c not in (thb.cards.base.DummyCard, thb.characters.parsee.EnvyRecycle)
]


cards = {}


for c in card_cls:
    if issubclass(c, thb.cards.base.PhysicalCard):
        cards[c.__name__] = {
            'Type': c.__name__,
            'Name': c.ui_meta.name,
            'CategoryStrings': c.category,
            'EquipmentCategoryString': getattr(c, 'equipment_category', ''),
            'EquipmentSkill': getattr(getattr(c, 'equipment_skill', None), '__name__', ''),
            'DistanceAdjust': distadj(c),
            'Description': c.ui_meta.description,
            'Illustrator': c.ui_meta.illustrator,
            'CV': c.ui_meta.cv,
        }

    elif issubclass(c, thb.cards.base.TreatAs):
        if not hasattr(c, 'ui_meta'):
            continue

        if not hasattr(c.ui_meta, 'description'):
            continue

        cats = ['skill', 'treat_as']
        if hasattr(c, 'treat_as') and isinstance(c.treat_as, list):
             cats += list(c.treat_as.category)

        cards[c.__name__] = {
            'Type': c.__name__,
            'Name': c.ui_meta.name,
            'CategoryStrings': cats,
            'DistanceAdjust': 0,
            'Description': getattr(c.ui_meta, 'description', ''),
            'Illustrator': '',
            'CV': '',
        }


cards = list(cards.values())


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
        'Description': c.ui_meta.description,
        'Players': c.n_persons,
        'RoleIDs': [k for k in c.ui_meta.roles],
    }

modes = list(modes.values())

# ----------
ilets = {}
ilet_cls = [c for c in kls if issubclass(c, thb.inputlets.Inputlet) and c is not thb.inputlets.Inputlet]
ilets = [v.tag() for v in ilet_cls]
ilets = [v for v in ilets if v]
ilets.extend([
    'ActionStageAction',
    'AskForRejectAction',
    'BanGirl',
    'ChooseGirl',
    'Pindian',
])


# =========================
rst = {
    'Characters': [{'Key': v['Type'], 'Value': json.dumps(v)} for v in chars],
    'UIMetaInputHandlers': ilets,
    'Cards': [{'Key': v['Type'], 'Value': json.dumps(v)} for v in cards],
    'RoleDefinitions': [{'Key': v['Type'], 'Value': json.dumps(v)} for v in roles],
    'Skills': [{'Key': v['Type'], 'Value': json.dumps(v)} for v in skills],
    'Modes': [{'Key': v['Type'], 'Value': json.dumps(v)} for v in modes],
}

print(json.dumps(rst))
