#coding:utf8
'''
找相似图片
'''
import os
from PIL import Image
from functools import reduce

def hamming(h1, h2):
    h, d = 0, h1 ^ h2
    while d:
        h += 1
        # 分情况讨论 最后一位为 1 或者 0 每 & 一次 就会少个 1
        d = d & (d-1)
    return h

def get_img_hash(img_path):
    img = Image.open(img_path)
    # 转换为 8 * 8 灰度
    img = img.resize((8, 8), Image.ANTIALIAS).convert('L')
    # 计算灰度平均值
    avg = reduce(lambda x, y: x + y, img.getdata()) / 64.
    # 计算hash
    img_hash = reduce(lambda x, y: x | y[1] << y[0], enumerate(map(lambda i: 0 if i < avg else 1, img.getdata())), 0)
    return img_hash


# 初始化测试环境
example_img = './pictures/0.jpeg'
example_hash = get_img_hash(example_img)

for img_name in os.listdir('./pictures'):
    temp_hash = get_img_hash('./pictures/' + img_name)
    print("%s %s" % (hamming(example_hash, temp_hash), img_name))
