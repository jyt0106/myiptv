import csv
import sys
import json
import os
import re
import traceback
import requests
import subprocess
import time
import shutil
from ffmpy import FFprobe
from subprocess import PIPE
from sys import stdout
from termcolor import colored, RESET
from datetime import datetime
from func_timeout import func_set_timeout, FunctionTimedOut
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse

dt=datetime.now()
check_success_domain = {}
# Channel	Group	Source	Link    Description
# Description 应当对该源的已知参数进行标注（如码率，HDR）

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf8') 


SKIP_FFPROBE_MESSAGES = [re.compile(pattern) for pattern in (
	'Last message repeated',
	'mmco: unref short failure',
	'number of reference frames .+ exceeds max',
)]


uniqueList = []

@func_set_timeout(18)
def get_stream(num, clist, uri):
    try:
        ffprobe = FFprobe(inputs={uri: '-v error -show_format -show_streams -print_format json'})
        cdata = json.loads(ffprobe.run(stdout=PIPE,stderr=PIPE)[0].decode('utf-8'))
        return cdata
    except Exception as e:
        #traceback.print_exc()
        print('[{}] {}({}) Error:{}'.format(str(num), clist[0], clist[2], str(e)))
        return False

def check_channel(clist,num):
    # clist 为一行 csv
    uri = clist[3]
    requests.adapters.DEFAULT_RETRIES = 3
    try:
        domain = urlparse(uri).netloc
        if domain not in check_success_domain:
            check_success_domain[domain] = False
        elif check_success_domain[domain]:
            return [1920,1080,'']
        else:
            return False
        r = requests.get(clist[3], timeout=1.5) # 先测能不能正常访问
        if(r.status_code == requests.codes.ok):
            #ffprobe = FFprobe(inputs={uri: '-v warning'})
            #errors = tuple(filter(
			#    lambda line: not (line in ('', RESET) or any(regex.search(line) for regex in SKIP_FFPROBE_MESSAGES)),
			#    ffprobe.run(stderr=PIPE)[1].decode('utf-8').split('\n')
		    #))
            #if errors: # https://github.com/Jamim/iptv-checker/blob/master/iptv-checker.py#L26
            #    print('[{}] {}({}) Error:{}'.format(str(num), clist[0], clist[2], str(errors)))
            #    return False
            #else: # 查视频信息
            cdata = get_stream(num, clist, uri)
            if cdata:
                check_success_domain[domain] = True
                # flagAudio = 0
                # flagVideo = 0
                # flagHDR = 0
                # flagHEVC = 0
                # vwidth = 0
                # vheight = 0
                # for i in cdata['streams']:
                #     if i['codec_type'] == 'video':
                #         flagVideo = 1
                #         if 'color_space' in i:
                #             # https://www.reddit.com/r/ffmpeg/comments/kjwxm9/how_to_detect_if_video_is_hdr_or_sdr_batch_script/
                #             if 'bt2020' in i['color_space']:
                #                 flagHDR = 1
                #         if i['codec_name'] == 'hevc':
                #             flagHEVC = 1
                #         if vwidth <= i['coded_width']: # 取最高分辨率
                #             vwidth = i['coded_width']
                #             vheight = i['coded_height']
                #     elif i['codec_type'] == 'audio':
                #         flagAudio = 1
                # if flagAudio == 0:
                #     print('[{}] {}({}) Error: Video Only!'.format(str(num), clist[0], clist[2]))
                #     return False
                # if flagVideo == 0:
                #     print('[{}] {}({}) Error: Audio Only!'.format(str(num), clist[0], clist[2]))
                #     return False
                # if (vwidth == 0) or (vheight == 0):
                #     print('[{}] {}({}) Error: {}x{}'.format(str(num), clist[0], clist[2],vwidth,vheight))

                # if flagHDR == 0:
                #     print('[{}] {}({}) PASS: {}*{}'.format(str(num), clist[0], clist[2], vwidth, vheight))
                #     return [vwidth,vheight,'']
                # if flagHDR == 1:
                #     print('[{}] {}({}) PASS(HDR Enabled): {}*{}'.format(str(num), clist[0], clist[2], vwidth, vheight))
                #     return [vwidth,vheight,'HDR']
                # if flagHEVC == 1: # https://news.ycombinator.com/item?id=19389496  默认有HDR的算HEVC
                #     print('[{}] {}({}) PASS(HEVC Enabled): {}*{}'.format(str(num), clist[0], clist[2], vwidth, vheight))
                #     return [vwidth,vheight,'HEVC']
            else:
                return False
        else:
            print('[{}] {}({})  {} Error:{}'.format(str(num), clist[0], clist[2], uri,str(r.status_code)))
            return False
    except Exception as e:
        #traceback.print_exc()
        print('[{}] {}({}) {} Error:{}'.format(str(num), clist[0], clist[2],uri, str(e)))
        return False

def print_info():
    print('Time: {}-{}-{} {}:{}'.format(dt.year,dt.month,dt.day,dt.hour,dt.minute))
    #subprocess.run(['ffprobe'])

def rm_files(target, selection):
    if selection == 1:  # 删目录
        try:
            shutil.rmtree(target)
        except OSError:
            pass
        try:
            os.mkdir(target)
        except OSError:
            pass
    else: # 删文件
        try:
            os.remove(target)
        except OSError:
            pass   
        

def getdes(st): # 不是所有的源都有描述
    if st:
        return '[{}]'.format(st)
    else:
        return ''

# TODO:
def main():
    print_info()
    Total = 0
    fulltimes = '-{}{}{}{}{}'.format(dt.year,dt.month,dt.day,dt.hour,dt.minute) # 时间后缀
    # times = fulltimes # 有时间后缀
    times = '' # 无时间后缀
    # 清空旧文件
    rm_files('D:\\code\\python\\myiptv\\utf8\\groups',1)
    rm_files('D:\\code\\python\\myiptv\\utf8\\merged.txt',2)
    rm_files('D:\\code\\python\\myiptv\\utf8\\merged-simple.txt',2)
    with open('D:\\code\\python\\myiptv\\utf8\\data.csv' ,encoding='utf8') as f:
        f_csv = csv.reader(f)
        headers = next(f_csv)
        num = 1
        with open('D:\\code\\python\\myiptv\\utf8\\data{}.csv'.format(fulltimes), 'a+' ,encoding='utf8') as f0: # 写入检测后新data
            print('Channel,Group,Source,Link', file=f0)
            for row in f_csv:
                try:
                    if row[3] in uniqueList:
                        ret = False
                    else:
                        uniqueList.append(row[3]) 
                        ret = check_channel(row,num)
                except FunctionTimedOut as e:
                    #traceback.print_exc()

                    print('[{}] {}({}) Error:{}'.format(str(num), row[0], row[2], str(e)))
                    ret = False
                if(ret): # 通过，写入
                    with open('D:\\code\\python\\myiptv\\utf8\\groups/{}{}.txt'.format(row[1],times), 'a+',encoding='utf8') as f1:
                        # print('{}({}{}-{}*{}),{}'.format(row[0],row[2],getdes(row[4]),ret[0],ret[1],row[3]), file=f1)
                        print('{}({}-{}P{}),{}'.format(row[0],row[2],ret[1],ret[2],row[3]), file=f1)
                    with open('D:\\code\\python\\myiptv\\utf8\\groups/{}-simple{}.txt'.format(row[1],times), 'a+',encoding='utf8') as f1:
                        print('{},{}'.format(row[0],row[3]), file=f1)
                    with open('D:\\code\\python\\myiptv\\utf8\\merged{}.txt'.format(times),'a+',encoding='utf8') as f1:
                        # print('{}({}{}-{}*{}),{}'.format(row[0],row[2],getdes(row[4]),ret[0],ret[1],row[3]), file=f1)
                        print('{}({}-{}P{}),{}'.format(row[0],row[2],ret[1],ret[2],row[3]), file=f1)
                    with open('D:\\code\\python\\myiptv\\utf8\\erged-simple{}.txt'.format(times),'a+',encoding='utf8') as f1:
                        print('{},{}'.format(row[0],row[3]), file=f1)
                    print('{},{},{},{}'.format(row[0],row[1],row[2],row[3]), file=f0)
                    Total = Total + 1
                num = num + 1
                time.sleep(0.25)
    print('Total: {}'.format(Total))
if __name__ == '__main__':
    main()



