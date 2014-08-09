# -*- coding: utf-8 -*-

# -- prioritized --
import sys
reload(sys)
sys.setdefaultencoding(sys.getfilesystemencoding())

# -- stdlib --
import HTMLParser
import argparse
import re
import time

# -- third party --
from sqlalchemy import create_engine, text as sq_text
import redis

# -- own --
from utils.interconnect import Interconnect


# -- code --
def forum_noti():
    parser = argparse.ArgumentParser('forum_noti')
    parser.add_argument('--redis-url', default='redis://localhost:6379')
    parser.add_argument('--connect-str', default='mysql://root@localhost/ultrax?charset=utf8')
    parser.add_argument('--discuz-dbpre', default='pre_')
    parser.add_argument('--forums', default='2,36,38,40,78,82')
    parser.add_argument('--forums-thread-only', default='78')
    options = parser.parse_args()

    text = lambda t: sq_text(t.replace('cdb_', options.discuz_dbpre))

    engine = create_engine(
        options.connect_str,
        encoding='utf-8',
        convert_unicode=True,
    )

    forum_ids = map(int, options.forums.split(','))
    forums = engine.execute(text('''
        SELECT fid, name FROM cdb_forum_forum
        WHERE fid IN :fids
    '''), fids=forum_ids).fetchall()
    forums = {i.fid: i.name for i in forums}

    r = redis.from_url(options.redis_url)
    interconnect = Interconnect('forum', options.redis_url)

    pid = int(r.get('aya:forum_lastpid') or 495985)

    post_template = u'|G{user}|r在|G{forum}|r发表了新主题|G{subject}|r：{excerpt}'
    reply_template = u'|G{user}|r回复了|G{forum}|r的主题|G{subject}|r：{excerpt}'

    threads_only = set(map(int, options.forums_thread_only.split(',')))

    while True:
        time.sleep(5)
        posts = engine.execute(text('''
            SELECT * FROM cdb_forum_post
            WHERE pid > :pid AND
                  fid IN :fids
            ORDER BY pid ASC
        '''), pid=pid, fids=forum_ids)

        if not posts:
            continue

        for p in posts:
            if not p.first and p.fid in threads_only:
                continue

            t = engine.execute(text('''
                SELECT * FROM cdb_forum_thread
                WHERE tid = :tid
            '''), tid=p.tid).fetchone()

            template = post_template if p.first else reply_template

            excerpt = p.message.replace(u'\n', '')
            excerpt = HTMLParser.HTMLParser().unescape(excerpt)
            excerpt = re.sub(r'\[quote\].*?\[/quote\]', u'', excerpt)
            excerpt = re.sub(r'\[img\].*?\[/img\]', u'[图片]', excerpt)
            excerpt = re.sub(r'\[.+?\]', u'', excerpt)
            excerpt = re.sub(r'\{:.+?:\}', u'[表情]', excerpt)
            excerpt = re.sub(r' +', u' ', excerpt)
            excerpt = excerpt.strip()
            if len(excerpt) > 60:
                excerpt = excerpt[:60] + u'……'

            msg = template.format(
                user=p.author,
                forum=forums[t.fid],
                subject=t.subject,
                excerpt=excerpt,
            )
            interconnect.publish('speaker', [u'文文', msg])
            pid = p.pid

        r.set('aya:forum_lastpid', pid)


if __name__ == '__main__':
    forum_noti()
