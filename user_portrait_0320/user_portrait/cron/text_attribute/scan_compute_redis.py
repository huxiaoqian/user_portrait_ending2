# -*- coding: UTF-8 -*-
import sys
import time
import json
from weibo_api_v2 import read_flow_text, read_flow_text_sentiment
from cron_text_attribute import test_cron_text_attribute_v2
reload(sys)
sys.path.append('../../')
from global_utils import R_RECOMMENTATION as r
from parameter import WEIBO_API_INPUT_TYPE
from time_utils import ts2datetime, datetime2ts, ts2date

def scan_compute_redis():
    hash_name = 'compute'
    results = r.hgetall('compute')
    iter_user_list = []
    mapping_dict = dict()
    for uid in results:
        user_list = json.loads(results[uid])
        in_date = user_list[0]
        status = user_list[1]
        if status == '2':
            iter_user_list.append(uid)
            mapping_dict[uid] = json.dumps([in_date, '3']) # mark status:3 computing
        if len(iter_user_list) % 100 == 0 and len(iter_user_list) != 0:
            #mark status from 1 to 3 as identify_compute to computing
            r.hmset('compute', mapping_dict)
            #acquire bulk user weibo data
            if WEIBO_API_INPUT_TYPE == 0:
                user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts = read_flow_text_sentiment(iter_user_list)
            else:
                user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts = read_flow_text(iter_user_list)
            #compute text attribute
            compute_status = test_cron_text_attribute_v2(user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts)
            
            if compute_status==True:
                change_status_computed(mapping_dict)
            else:
                change_status_compute_fail(mapping_dict)

            #deal user no weibo to compute portrait attribute
            if len(user_keywords_dict) != len(iter_user_list):
                change_mapping_dict = dict()
                change_user_list = set(iter_user_list) - set(user_keywords_dict.keys())
                for change_user in change_user_list:
                    change_mapping_dict[change_user] = json.dumps([in_date, '2'])
                r.hmset('compute', change_mapping_dict)

            iter_user_list = []
            mapping_dict = {}
            
    if iter_user_list != [] and mapping_dict != {}:
        r.hmset('compute', mapping_dict)
        #acquire bulk user weibo date
        if WEIBO_API_INPUT_TYPE == 0:
            user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts = read_flow_text_sentiment(iter_user_list)
        else:
            user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts = read_flow_text(iter_user_list)
        #compute text attribute
        compute_status = test_cron_text_attribute_v2(user_keywords_dict, user_weibo_dict, online_pattern_dict, character_start_ts)
        if compute_status==True:
            change_status_computed(mapping_dict)
        else:
            change_status_compute_fail(mapping_dict)
        #deal user no weibo to compute portrait attribute
        if len(user_keywords_dict) != len(iter_user_list):
            change_mapping_dict = dict()
            change_user_list = set(iter_user_list) - set(user_keywords_dict.keys())
            for change_user in change_user_list:
                change_mapping_dict[change_user] = json.dumps([in_date, '2'])
            r.hmset(change_mapping_dict)


def change_status_computed(mapping_dict):
    hash_name = 'compute'
    status = 4
    new_mapping_dict = {}
    for uid in mapping_dict:
        user_list = json.loads(mapping_dict[uid])
        user_list[1] = '4'
        new_mapping_dict[uid] = json.dumps(user_list)
    r.hmset(hash_name, new_mapping_dict)

#use to deal compute fail situation
def change_status_compute_fail(mapping_dict):
    hash_name = 'compute'
    status = 2
    new_mapping_dict = {}
    for uid in mapping_dict:
        user_list = json.loads(mapping_dict[uid])
        user_list[1] = '2'
        new_mapping_dict[uid] = json.dumps(user_list)
    r.hmset(hashname, new_mapping_dict)


if __name__=='__main__':
    log_time_ts = time.time()
    log_time_date = ts2datetime(log_time_ts)
    print 'cron/text_attribute/scan_compute_redis.py&start&' + log_time_date
   
    try: 
        scan_compute_redis()
    except Exception, e:
        print e, '&error&', ts2date(time.time())
    log_time_ts = time.time()
    log_time_date = ts2datetime(log_time_ts)
    print 'cron/text_attribute/scan_compute_redis.py&end&' + log_time_date
