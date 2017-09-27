# coding:utf8
import os
import time
import Queue

import functools
import threading
import multiprocessing

import log
import setting

_logger = log.get_logger(__file__)

cur_path = os.path.dirname(os.path.abspath(__file__))
pid_dir = os.path.join(cur_path, "pid")
if not os.path.isdir(pid_dir):
    os.makedirs(pid_dir)


def log_error(e, func):
    _logger.exception(e)
    return 1


def keepalive(handle_func=log_error, interval=1):
    """装饰器
    功能：
       捕获被装饰函数的异常并重新调用函数
       函数正常结束则结束
    装饰器参数：
       @handle_func:function
          异常处理函数 默认接收参数 e(异常对象), func(被装饰函数)
       @interval:number
          函数重启间隔
    """

    def wrapper(func):
        @functools.wraps(func)
        def keep(*args, **kwargs):
            while 1:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    if handle_func:
                        handle_func(e, func)
                    time.sleep(interval)
                    continue
                break
            return result

        return keep

    return wrapper


def launch_process(target, args=(), kwargs=None, type=setting.PROCESS_MODE):
    if type == "thread":
        p = threading.Thread(target=target, args=args, kwargs=kwargs)
    elif type == "process":
        if kwargs is None:
            kwargs = {}
        p = multiprocessing.Process(target=target, args=args, kwargs=kwargs)
    p.start()
    return p


def get_queue(type=setting.PROCESS_MODE):
    if type == "thread":
        return Queue.Queue()
    elif type == "process":
        return multiprocessing.Queue()


def get_event(type=setting.PROCESS_MODE):
    if type == "thread":
        return threading.Event()
    elif type == "process":
        return multiprocessing.Event()


def set_pid(filename):
    filename = filename.split(os.sep)[-1].split(".")[0]
    filename = filename + ".pid"
    filename = os.path.join(pid_dir, filename)
    if os.path.exists(filename):
        return ""
    else:
        with open(filename, "w") as f:
            f.write("%s" % os.getpid())
        return filename


def check_stop(filename, stop_event):
    while 1:
        if os.path.exists(filename) and not stop_event.is_set():
            time.sleep(2)
            continue
        elif stop_event.is_set():
            os.remove(filename)
            break
        else:
            stop_event.set()
            break
    return


def stop_process(filename):
    for pid_file in os.listdir(pid_dir):
        if filename in pid_file or filename == "all":
            os.remove(os.path.join(pid_dir, pid_file))
    return 1


@keepalive()
def executer(stop_event, func, **kwargs):
    """
    这些参数都是executer自己要用到的
    :param stop_event:
    :param func: 任务主体执行函数
    :param in_queue: 任务接收队列
    :param out_queue: 任务下发队列
    :param logger: 日志
    :param worker_name: 进程名称
    :param loop_sleep: 每轮任务休眠时间
    :param _locals: 需要在进程fork之后执行的函数 比如新建mongo连接
    :param kwargs: 目标函数需要的参数
    :return:
    """
    in_queue= kwargs.get("in_queue", None)
    out_queue = kwargs.get("out_queue", None)
    logger = kwargs.get("logger", None)
    worker_name = kwargs.get("worker_name", None)
    loop_sleep = kwargs.get("loop_sleep", 0)
    _locals = kwargs.get("_locals", {})
    kwargs.update({
            "stop_event": stop_event,
            "func": func,
            })
    # 创建执行locals中的函数
    new_locals = {}
    for var_name, var_func in _locals.items():
        new_locals.update({var_name: var_func()})
    kwargs.update(new_locals)

    if not logger:
        logger = _logger

    _count = 0
    while 1:
        # 心跳
        if _count > 0 and _count % 100 == 0:
            logger.debug(u"%s alived" % worker_name)
            _count = 0
        if not in_queue and stop_event.is_set():
            # 生产者 当停止信号发出时即结束
            # 消费者要等到in_queue中无任务
            break

        new_task = []

        # 消费者接受任务
        if in_queue:
            try:
                task = in_queue.get(True, 1)
                _count += 1
                if stop_event.is_set():
                    logger.info(u"%s: stop event set, but tasks not down, please waiting..." % worker_name)
            except:
                # 消费者  无任务时响应 stop event
                if stop_event.is_set():
                    logger.info(u"%s stoped" % worker_name)
                    break
                time.sleep(1)
                continue
            try:
                new_task = func(task, **kwargs)
            except Exception as e:
                logger.exception(e)
        else:
            # 生产者 生产任务
            try:
                new_task = func(**kwargs)
            except Exception as e:
                logger.exception(e)

        # 生产者分发新的任务
        if out_queue is not None and new_task:
            if not isinstance(out_queue, list):
                out_queue = [out_queue]
            for queue in out_queue:
                # todo size判断
                queue.put(new_task)

        if loop_sleep:
            sleep(loop_sleep, stop_event)
    return

def sleep(ts, stop_event=None):
    if stop_event is not None:
        ts = int(ts)
        for i in range(ts):
            if not stop_event.is_set():
                time.sleep(1)
            else:
                break
    else:
        time.sleep(ts)
    return

if __name__ == "__main__":
    pass
