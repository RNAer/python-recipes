# -*- coding: utf-8 -*-

from requests.exceptions import RequestException
import requests
import json
import sys
import re
import os

class ximalaya:
    def __init__(self, url):
        # album url, eg http://www.ximalaya.com/16960840/album/294567
        self.url = url
        self.urlheader = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': ('Mozilla/5.0 (Windows NT 6.1; WOW64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/53.0.2785.116 Safari/537.36'),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': self.url,
            'Cookie': '_ga=GA1.2.1628478964.1476015684; _gat=1',
        }

    def getpage(self):
        '''获取分页数方法'''
        pagelist = []  # 保存分页数
        try:
            response = requests.get(self.url, headers=self.urlheader).text
        except RequestException as e:
            print(e)
        else:
            reg_list = [
                re.compile(r"class=\"pagingBar_wrapper\" url=\"(.*?)\""),
                re.compile(r"<a href='(/\d+/album/\d+\?page=\d+)' data-page='\d+'")
            ]
            for reg in reg_list:
                pagelist.extend(reg.findall(response))
        print(pagelist)
        if pagelist:
            return ['http://www.ximalaya.com' + x for x in pagelist[:-1]]
        else:
            return [self.url]

    def analyze(self, trackid):
        '''Get the real mp3 ULR address'''
        trackurl = 'http://www.ximalaya.com/tracks/%s.json' % trackid
        try:
            response = requests.get(trackurl, headers=self.urlheader).text
        except RequestException as e:
            print(e)
        else:
            jsonobj = json.loads(response)
            title = jsonobj['title']
            mp3 = jsonobj['play_path']
            filename = title.strip() + '.mp3'
            return filename, mp3

    def todownlist(self):
        '''生成待下载的文件列表'''
        if 'sound' in self.url:
            # 解析单条mp3
            trackid = self.url[self.url.rfind('/') + 1:]
            self.analyze(trackid)
        else:
            for purl in self.getpage():  # 解析每个专辑页面中的所有mp3地址
                response = requests.get(purl, headers=self.urlheader).text
                ids_reg = re.compile(r'sound_ids="(.+?)"')
                ids_res = ids_reg.findall(response)
                idslist = [j for j in ids_res[0].split(',')]
                for trackid in idslist:
                    self.analyze(trackid)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('用法: ' + os.path.basename(sys.argv[0]) + u' 你要下载的专辑mp3主页地址,地址如下：')
        print('实例: ' + os.path.basename(sys.argv[0]) + ' http://www.ximalaya.com/12495477/album/269179')
        sys.exit()
    ximalaya = ximalaya(sys.argv[1])  # 实例化类
    ximalaya.todownlist()
