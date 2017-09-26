# coding:utf8
"""
多任务管理器
执行
    # 启动所有已注册脚本
    python main.py --all &
用法
    # 查看命令选项
    python main.py --help
    # 执行指定命令
    python main.py --sample &
    # 停止指定命令
    python main.py --stop --sample
"""
import argparse
import multiprocessing

import log
import util

task_module_list = [
    # 在此处添加任务脚本文件名
    "sample",
]

# import 任务脚本
task_module_dict = {
    module_name: __import__(module_name) for module_name in task_module_list
}

logger = log.get_logger(__file__)


def launch_process(target):
    p = multiprocessing.Process(target=target)
    p.start()
    return p


def main():
    parser = argparse.ArgumentParser()
    for module_name in task_module_list:
        parser.add_argument("--%s" % module_name, action="store_true", help=task_module_dict[module_name].__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--stop", action="store_true")

    process_list = []

    cmd_args = parser.parse_args()
    if not cmd_args.stop:
        if cmd_args.all:
            print("--all is forbidden")
            pass
            # 禁用
            # func_list = [_module.run for _module in task_module_dict.values()]
            # for func in func_list:
            #     process_list.append(launch_process(func))
        else:
            for module_name, _module in task_module_dict.items():
                if getattr(cmd_args, module_name):
                    process_list.append(launch_process(_module.run))
    else:
        if cmd_args.all:
            util.stop_process("all")
        else:
            for module_name, _module in task_module_dict.items():
                if getattr(cmd_args, module_name):
                    util.stop_process(module_name)

    for p in process_list:
        p.join()
    logger.info("main stoped !!!")
    return


if __name__ == "__main__":
    main()
