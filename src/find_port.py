#!/usr/bin/env python3
"""
自动寻找可用端口。从 base_port 开始递增探测，返回第一个空闲端口。
绝不杀任何已有进程。

用法:
  python find_port.py              # 默认从 37000 开始
  python find_port.py 38000        # 从 38000 开始
  python find_port.py 37000 37100  # 在 37000-37100 范围内找

在其他 Python 脚本中:
  from find_port import find_free_port
  port = find_free_port(37000)
"""

import socket
import sys


def find_free_port(base: int = 37000, end: int = 0) -> int:
    """从 base 开始找第一个空闲端口。end=0 表示 base+100。"""
    if end <= 0:
        end = base + 100
    for port in range(base, end + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"在 {base}-{end} 范围内找不到空闲端口")


if __name__ == "__main__":
    base = int(sys.argv[1]) if len(sys.argv) > 1 else 37000
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    port = find_free_port(base, end)
    print(port)
