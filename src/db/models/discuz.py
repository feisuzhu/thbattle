# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
# -- third party --
from sqlalchemy import Column, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import relationship

# -- own --
from db.base import Model


# -- code --
class DiscuzMember(Model):
    __tablename__ = 'pre_common_member'

    uid                = Column(Integer, primary_key=True)
    email              = Column(String(40), nullable=False, index=True, default='')
    username           = Column(String(15), nullable=False, unique=True, default='')
    password           = Column(String(32), nullable=False, default='')
    status             = Column(Integer, nullable=False, default=0)
    emailstatus        = Column(Integer, nullable=False, default=0)
    avatarstatus       = Column(Integer, nullable=False, default=0)
    videophotostatus   = Column(Integer, nullable=False, default=0)
    adminid            = Column(Integer, nullable=False, default=0)
    groupid            = Column(SmallInteger, nullable=False, index=True, default=0)
    groupexpiry        = Column(Integer, nullable=False, default=0)
    extgroupids        = Column(String(20), nullable=False, default='')
    regdate            = Column(Integer, nullable=False, index=True, default=0)
    credits            = Column(Integer, nullable=False, default=0)
    notifysound        = Column(Integer, nullable=False, default=0)
    timeoffset         = Column(String(4), nullable=False, default='')
    newpm              = Column(SmallInteger, nullable=False, default=0)
    newprompt          = Column(SmallInteger, nullable=False, default=0)
    accessmasks        = Column(Integer, nullable=False, default=0)
    allowadmincp       = Column(Integer, nullable=False, default=0)
    onlyacceptfriendpm = Column(Integer, nullable=False, default=0)
    conisbind          = Column(Integer, nullable=False, index=True, default=0)
    freeze             = Column(Integer, nullable=False, default=0)

    member_count  = relationship('DiscuzMemberCount', uselist=False)
    member_status = relationship('DiscuzMemberStatus', uselist=False)
    member_field  = relationship('DiscuzMemberField', uselist=False)
    ucmember      = relationship('DiscuzUCenterMember', uselist=False)


class DiscuzMemberCount(Model):
    __tablename__ = 'pre_common_member_count'

    uid             = Column(Integer, ForeignKey('pre_common_member.uid'), primary_key=True)
    extcredits1     = Column(Integer, nullable=False, default=0)
    jiecao          = Column('extcredits2', Integer, nullable=False, default=0)
    extcredits3     = Column(Integer, nullable=False, default=0)
    extcredits4     = Column(Integer, nullable=False, default=0)
    extcredits5     = Column(Integer, nullable=False, default=0)
    extcredits6     = Column(Integer, nullable=False, default=0)
    drops           = Column('extcredits7', Integer, nullable=False, default=0)
    games           = Column('extcredits8', Integer, nullable=False, default=0)
    friends         = Column(SmallInteger, nullable=False, default=0)
    posts           = Column(Integer, nullable=False, index=True, default=0)
    threads         = Column(Integer, nullable=False, default=0)
    digestposts     = Column(SmallInteger, nullable=False, default=0)
    doings          = Column(SmallInteger, nullable=False, default=0)
    blogs           = Column(SmallInteger, nullable=False, default=0)
    albums          = Column(SmallInteger, nullable=False, default=0)
    sharings        = Column(SmallInteger, nullable=False, default=0)
    attachsize      = Column(Integer, nullable=False, default=0)
    views           = Column(Integer, nullable=False, default=0)
    oltime          = Column(SmallInteger, nullable=False, default=0)
    todayattachs    = Column(SmallInteger, nullable=False, default=0)
    todayattachsize = Column(Integer, nullable=False, default=0)
    feeds           = Column(Integer, nullable=False, default=0)
    follower        = Column(Integer, nullable=False, default=0)
    following       = Column(Integer, nullable=False, default=0)
    newfollower     = Column(Integer, nullable=False, default=0)
    blacklist       = Column(Integer, nullable=False, default=0)


class DiscuzMemberStatus(Model):
    __tablename__ = 'pre_common_member_status'
    __table_args__ = (
        Index('lastactivity', 'lastactivity', 'invisible'),
    )

    uid             = Column(Integer, ForeignKey('pre_common_member.uid'), primary_key=True)
    regip           = Column(String(15), nullable=False, default='')
    lastip          = Column(String(15), nullable=False, default='')
    port            = Column(SmallInteger, nullable=False, default=0)
    lastvisit       = Column(Integer, nullable=False, default=0)
    lastactivity    = Column(Integer, nullable=False, default=0)
    lastpost        = Column(Integer, nullable=False, default=0)
    lastsendmail    = Column(Integer, nullable=False, default=0)
    invisible       = Column(Integer, nullable=False, default=0)
    buyercredit     = Column(SmallInteger, nullable=False, default=0)
    sellercredit    = Column(SmallInteger, nullable=False, default=0)
    favtimes        = Column(Integer, nullable=False, default=0)
    sharetimes      = Column(Integer, nullable=False, default=0)
    profileprogress = Column(Integer, nullable=False, default=0)


class DiscuzUCenterMember(Model):
    __tablename__ = 'pre_ucenter_members'

    uid           = Column(Integer, ForeignKey('pre_common_member.uid'), primary_key=True)
    username      = Column(String(15), nullable=False, unique=True, default='')
    password      = Column(String(32), nullable=False, default='')
    email         = Column(String(32), nullable=False, index=True, default='')
    myid          = Column(String(30), nullable=False, default='')
    myidkey       = Column(String(16), nullable=False, default='')
    regip         = Column(String(15), nullable=False, default='')
    regdate       = Column(Integer, nullable=False, default=0)
    lastloginip   = Column(Integer, nullable=False, default=0)
    lastlogintime = Column(Integer, nullable=False, default=0)
    salt          = Column(String(6), nullable=False)
    secques       = Column(String(8), nullable=False, default='')


class DiscuzMemberField(Model):
    __tablename__ = 'pre_common_member_field_forum'

    uid            = Column(Integer, ForeignKey('pre_common_member.uid'), primary_key=True)
    publishfeed    = Column(Integer, nullable=False, default=0)
    customshow     = Column(Integer, nullable=False, default=26)
    customstatus   = Column(String(30), nullable=False, default='')
    medals         = Column(Text, nullable=False)
    sightml        = Column(Text, nullable=False)
    groupterms     = Column(Text, nullable=False)
    authstr        = Column(String(20), nullable=False, default='')
    groups         = Column(String, nullable=False)
    attentiongroup = Column(String(255), nullable=False, default='')
