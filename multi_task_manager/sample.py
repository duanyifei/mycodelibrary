# coding:utf8
"""
示例任务写法
"""
import time
import pymongo

import log
import util
import setting

logger = log.get_logger(__file__)


def get_mongodb_connect():
    """
    pymongo建立的链接不能跨进程 所以建立此函数 用于在进程启动后建立链接
    """
    client = pymongo.MongoClient(host="127.0.0.1", port=27017)
    collection = client.test_db.test_collection
    return collection

def producer(**kwargs):
    """
    生产者
        执行特定任务
        需要的参数可以从 kwargs中获取
    """
    print("I am a producer")
    task = "%s producer " % (time.time())
    time.sleep(1)
    return task

def middle_worker(task, **kwargs):
    """
    中间人
        既消费又生产
    """
    print("I am a middle workeer")
    print task
    task += "middle"
    return task

def customer(task, **kwargs):
    """
    消费者
        消费接收的任务
    """
    print("I am a customer")
    print("task: %s is ok" % task)
    return None


@util.keepalive()
def run():
    pid_file = util.set_pid(__file__)
    if not pid_file:
        logger.error("set_pid %s failed: pid_file exists" % pid_file)
        return
    logger.info("%s starting!!!" % pid_file)
    stop_event = util.get_event()
    # 生产者使用 分发任务队列
    producer_out_queue = util.get_queue()
    # 中间人使用 分发任务队列
    middle_out_queue = util.get_queue()

    thread_list = []
    # 启动生产者
    for i in range(1):
        kwargs = {
            "out_queue": [producer_out_queue,],
            "logger": logger,
            "worker_name": "producer",
        }
        t = util.launch_process(target=util.executer,
                                # 传递 函数 和 stop_event
                                args=(stop_event, producer),
                                kwargs=kwargs)
        thread_list.append(t)

    # 启动中间人
    for i in range(2):
        kwargs = {
            "in_queue": producer_out_queue,
            "out_queue": middle_out_queue,
            "logger": logger,
            "worker_name": "middle_worker",
            # 设置进程启动后指定的函数
            "_locals": {
                "collection": get_mongodb_connect,
            }
        }
        t = util.launch_process(target=util.executer, args=(stop_event, middle_worker), kwargs=kwargs)
        thread_list.append(t)

    # 启动消费者
    for i in range(1):
        kwargs = {
            "logger": logger,
            "worker_name": "customer",
            "in_queue": middle_out_queue,
        }
        t = util.launch_process(target=util.executer, args=(stop_event, customer), kwargs=kwargs)
        thread_list.append(t)

    # 阻塞监测是否停止程序
    util.check_stop(pid_file, stop_event)

    for t in thread_list:
        t.join()
    logger.info("%s stoped!!!" % pid_file)
    return


if __name__ == "__main__":
    pass
