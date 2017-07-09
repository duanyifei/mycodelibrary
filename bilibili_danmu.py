#coding:utf8
"""
python3

B站 弹幕分析
视频地址:
https://www.bilibili.com/video/av10418941/index_4.html#page=4
时间:
2017/07/09
"""
import os
import sys
import string
import datetime
from xml.etree import ElementTree
from collections import Counter

import jieba
import pandas
import requests
import matplotlib.pyplot as plt

chinese_punctuation = """。，、＇：∶；?‘’“”〝〞ˆˇ﹕︰﹔﹖﹑·¨….¸;！´？！～—ˉ｜‖＂〃｀@﹫¡¿﹏﹋﹌︴々﹟#﹩$﹠&﹪%*﹡﹢﹦﹤‐￣¯―﹨ˆ˜﹍﹎+=<­­＿_-\ˇ~﹉﹊（）〈〉‹›﹛﹜『』〖〗［］《》〔〕{}「」【】︵︷︿︹︽_﹁﹃︻︶︸﹀︺︾ˉ﹂﹄︼"""

cur_path = os.path.abspath('.')

#获取弹幕信息
def get_comment():
    url = 'https://comment.bilibili.com/17206367.xml'
    response = requests.get(url)
    xml_text = response.content
    # 获取弹幕信息
    xml_parser = ElementTree.fromstring(xml_text)
    d_node_list = xml_parser.findall('d')
    d_info = []
    for d in d_node_list:
        p = d.attrib.get('p').split(',')
        movie_time = float(p[0])
        post_time = int(p[4])
        d_info.append({
            "movie_time": movie_time, # 电影播放时长
            "post_time": post_time, # 弹幕发送时间
            "text": d.text, # 弹幕内容
            })
    print("获取弹幕信息成功，共%s条" % len(d_info))
    return d_info

# 获取停用词表
def init_stopwords():
    url = 'https://raw.githubusercontent.com/dongxiexidian/Chinese/master/stopwords.dat'
    response = requests.get(url)
    with open('stopwords.txt', 'w') as f:
        f.write(response.text)
    print("获取停用词表成功")
    return

def main():
    d_info = get_comment()
    # 获取停用词
    with open('stopwords.txt') as f:
        stopwords = f.readlines()
        stopwords = [x.strip() for x in stopwords]
        stopwords += list(string.punctuation)
        stopwords += list(chinese_punctuation)
    #
    dt = pandas.DataFrame(d_info)
    # 增加一列电影播放时长的分钟表示
    dt['movie_time_minute'] = dt.movie_time // 60
    # 统计弹幕最多的10个分钟区间
    max_minutes = dt.groupby('movie_time_minute').count().sort_values('movie_time', axis='index').index[-10:].values.tolist()
    max_minutes.reverse()
    max_minutes.insert(0, -1)
    for minute in max_minutes:
        if minute == -1:
            _dt = dt
        else:
            _dt = dt[dt.movie_time_minute==minute]
        all_text = []
        for text in _dt.text.values:
            cut_words = jieba.cut(text)
            # 去除停用词
            cut_words = [x for x in cut_words if x not in stopwords and x.strip()]
            all_text += cut_words
        text_counter = Counter(all_text)
        if minute == -1:
            print("全片弹幕关键词: %s" % (",".join([word for word, num in text_counter.most_common(10)])))
            print("以下关键词按此分钟内弹幕数量排序:")
        else:
            print("\t第%s分钟: %s" % (minute, ",".join([word for word, num in text_counter.most_common(10)])))

    #  按天统计弹幕数
    dt['post_time_day'] = dt.post_time.map(lambda x:datetime.datetime.fromtimestamp(x).date().strftime('%Y-%m-%d'))
    # 每天弹幕数趋势图
    dt.groupby('post_time_day').post_time.count().plot()
    plt.savefig("post_time_days.png")
    print("趋势图已保存 %s" % (os.path.join(cur_path, 'post_time_days.png')))
    pass


if __name__ == "__main__":
    if sys.version < '3':
        print(u"请使用python 3 ")
        sys.exit(1)
    if not os.path.exists('stopwords.txt'):
        init_stopwords()
    main()
