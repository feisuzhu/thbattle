# -*- coding: utf-8 -*-

from settings import ACCOUNT_TBLPREFIX as PREFIX, ACCOUNT_DJANGOCONFIG

from django import conf
conf.settings.configure(**ACCOUNT_DJANGOCONFIG)

from django.db import models

class UCenterMember(models.Model):
    uid = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=45, unique=True)
    password = models.CharField(max_length=96)
    email = models.CharField(max_length=96)
    myid = models.CharField(max_length=90)
    myidkey = models.CharField(max_length=48)
    regip = models.CharField(max_length=45)
    regdate = models.IntegerField()
    lastloginip = models.IntegerField()
    lastlogintime = models.IntegerField()
    salt = models.CharField(max_length=18)
    secques = models.CharField(max_length=24)

    class Meta:
        db_table = PREFIX + u'ucenter_members'

    def calc_password(self, pwd):
        from hashlib import md5
        return md5(md5(pwd.encode('utf-8')).hexdigest() + self.salt).hexdigest()

    def validate_password(self, pwd):
        return self.calc_password(pwd) == self.password

    # def set_password(self, pwd): <not needed>

class ForumMember(models.Model):
    ucmember = models.OneToOneField(
        UCenterMember,
        to_field='uid', db_column='uid',
        related_name='forum_member', primary_key=True
    )
    email = models.CharField(max_length=120)
    username = models.CharField(max_length=45, unique=True)
    password = models.CharField(max_length=96)
    status = models.IntegerField()
    emailstatus = models.IntegerField()
    avatarstatus = models.IntegerField()
    videophotostatus = models.IntegerField()
    adminid = models.IntegerField()
    groupid = models.IntegerField()
    groupexpiry = models.IntegerField()
    extgroupids = models.CharField(max_length=60)
    regdate = models.IntegerField()
    credits = models.IntegerField()
    notifysound = models.IntegerField()
    timeoffset = models.CharField(max_length=12)
    newpm = models.IntegerField()
    newprompt = models.IntegerField()
    accessmasks = models.IntegerField()
    allowadmincp = models.IntegerField()
    onlyacceptfriendpm = models.IntegerField()
    conisbind = models.IntegerField()
    class Meta:
        db_table = PREFIX + u'common_member'

class ForumCount(models.Model):
    ucmember = models.OneToOneField(
        UCenterMember,
        to_field='uid', db_column='uid',
        related_name='forum_count', primary_key=True
    )
    extcredits1 = models.IntegerField()
    extcredits2 = models.IntegerField()
    extcredits3 = models.IntegerField()
    extcredits4 = models.IntegerField()
    extcredits5 = models.IntegerField()
    extcredits6 = models.IntegerField()
    extcredits7 = models.IntegerField()
    extcredits8 = models.IntegerField()
    friends = models.IntegerField()
    posts = models.IntegerField()
    threads = models.IntegerField()
    digestposts = models.IntegerField()
    doings = models.IntegerField()
    blogs = models.IntegerField()
    albums = models.IntegerField()
    sharings = models.IntegerField()
    attachsize = models.IntegerField()
    views = models.IntegerField()
    oltime = models.IntegerField()
    todayattachs = models.IntegerField()
    todayattachsize = models.IntegerField()
    feeds = models.IntegerField()
    follower = models.IntegerField()
    following = models.IntegerField()
    newfollower = models.IntegerField()
    class Meta:
        db_table = PREFIX + u'common_member_count'

class ForumField(models.Model):
    ucmember = models.OneToOneField(
        UCenterMember,
        to_field='uid', db_column='uid',
        related_name='forum_field', primary_key=True
    )
    publishfeed = models.IntegerField()
    customshow = models.IntegerField()
    customstatus = models.CharField(max_length=90)
    medals = models.TextField()
    sightml = models.TextField()
    groupterms = models.TextField()
    authstr = models.CharField(max_length=60)
    groups = models.TextField()
    attentiongroup = models.CharField(max_length=765)
    class Meta:
        db_table = PREFIX + u'common_member_field_forum'
