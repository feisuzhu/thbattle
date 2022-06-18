# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
from django.db import models

# -- own --
from player.models import Player


# -- code --
_ = lambda s: {'help_text': s, 'verbose_name': s}


class FixedText(models.Model):

    class Meta:
        verbose_name        = '定型文'
        verbose_name_plural = '定型文'

    id        = models.AutoField(**_('ID'), primary_key=True)
    text      = models.CharField(**_('文本'), max_length=200)
    voice     = models.URLField(**_('配音'), null=True, blank=True)
    actor     = models.CharField(**_('配音演员'), max_length=50, null=True, blank=True)
    character = models.CharField(**_('角色限定'), null=True, blank=True, max_length=200)
    avail_to  = models.ManyToManyField(Player, **_('可使用玩家'), blank=True, related_name='fixed_texts')
    pinned_by = models.ManyToManyField(Player, **_('Pin 在常用列表的玩家'), blank=True, related_name='pinned_fixed_texts')

    def __str__(self):
        cv = '🎤' if self.voice else ''
        ch = self.character
        ch = f'[{ch}] ' if ch else ''
        return f'[#{self.id}] {ch}{cv}{self.text}'


class SharedFixedText(models.Model):

    class Meta:
        verbose_name        = '公共定型文'
        verbose_name_plural = '公共定型文'

    ref = models.OneToOneField(FixedText, **_('定型文'), on_delete=models.CASCADE, related_name='shared')

    def __str__(self):
        return str(self.ref)


class EmojiPack(models.Model):

    class Meta:
        verbose_name        = '大表情包'
        verbose_name_plural = '大表情包'

    id       = models.AutoField(**_('ID'), primary_key=True)
    name     = models.CharField(**_('表情包名称'), max_length=100)
    avail_to = models.ManyToManyField(Player, **_('可使用玩家'), blank=True, related_name='emoji_sets')

    def __str__(self):
        return f'[#{self.id}] {self.name}'


class SharedEmojiPack(models.Model):

    class Meta:
        verbose_name        = '公共大表情包'
        verbose_name_plural = '公共大表情包'

    ref = models.OneToOneField(EmojiPack, **_('大表情包'), on_delete=models.CASCADE, related_name='shared')

    def __str__(self):
        return str(self.ref)


class Emoji(models.Model):

    class Meta:
        verbose_name        = '大表情'
        verbose_name_plural = '大表情'

    id   = models.AutoField(**_('ID'), primary_key=True)
    pack = models.ForeignKey(EmojiPack, **_('表情包'), on_delete=models.CASCADE, related_name='items')
    name = models.CharField(**_('名称'), max_length=100)
    url  = models.URLField(**_('URL'))

    def __str__(self):
        return f'[#{self.id}] {self.name}'
