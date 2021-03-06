# -*- coding: UTF-8 -*-
'''
use to scan the user_portrait uid, fansnum, domain to redis 
'''
import sys
import time
import json
from elasticsearch.helpers import scan

reload(sys)
sys.path.append('../../')
from global_utils import es_user_portrait, portrait_index_name, portrait_index_type
from global_utils import update_week_redis, UPDATE_WEEK_REDIS_KEY
from time_utils import ts2datetime, ts2date


#scan es to redis as a queue for update_week
#write in version: 15-12-08
#order time task for every week
def scan_es2redis_week():
    count = 0
    s_re = scan(es_user_portrait, query={'query':{'match_all': {}}, 'size':1000}, index=portrait_index_name, doc_type=portrait_index_type)
    user_info = {}
    start_ts = time.time()
    while True:
        try:
            scan_re = s_re.next()['_source']
            count += 1
            uid = scan_re['uid']
            user_info[uid] = {'fansnum':scan_re['fansnum'], 'domain':scan_re['domain']}
            update_week_redis.lpush(UPDATE_WEEK_REDIS_KEY, json.dumps(user_info))
            user_info = {}
            #log_should_delete
            if count % 1000 == 0 and count != 0:
                end_ts = time.time()
                print '%s sec count 1000' % (end_ts - start_ts)
                start_ts = end_ts
            #log_should_delete
        except StopIteration:
            if user_info:
                update_week_redis.lpush(UPDATE_WEEK_REDIS_KEY, json.dumps(user_info))
                user_info = {}
            break
        except Exception, r:
            raise r
            break

    if user_info:
        update_week_redis.lpush(UPDATE_WEEK_REDIS_KEY, json.dumps(user_info))

if __name__=='__main__':
    log_time_ts = time.time()
    log_time_date = ts2datetime(log_time_ts)
    print 'cron/text_attribute/scan_es2redis_week.py&start&' + log_time_date
    
    try:
        scan_es2redis_week()
    except Exception, e:
        print e, '&error&', ts2date(time.time())

    log_time_ts = time.time()
    log_time_date = ts2datetime(log_time_ts)
    print 'cron/text_attribute/scan_es2redis_week.py&end&' + log_time_date
