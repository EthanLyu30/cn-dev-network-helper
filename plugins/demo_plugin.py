
import time
from datetime import datetime

# 这是一个示例插件
# 它可以被 "全能开发环境助手" 的插件系统自动加载

def run(context):
    """
    插件入口函数
    :param context: 包含 logger, utils 等工具的上下文对象
    """
    logger = context.get('logger')
    
    # 1. 打印日志
    if logger:
        logger(f"Hello! 这是来自插件的消息。当前时间: {datetime.now()}")
    
    # 2. 模拟一些耗时操作
    print("插件正在运行一些计算任务...")
    time.sleep(1)
    
    # 3. 返回结果
    return {
        "status": "success",
        "message": "示例插件运行成功！你可以参照 plugins/demo_plugin.py 编写自己的脚本。",
        "data": {
            "timestamp": time.time()
        }
    }
