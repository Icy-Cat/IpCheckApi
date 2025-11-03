"""
缓存管理命令行工具。

使用示例：
    python manage_cache.py clear-cache    # 清除所有缓存
"""

import argparse

from cache import cache_manager


def clear_cache() -> None:
    removed = cache_manager.clear_all()
    print(f"已清空缓存，共删除 {removed} 条记录。")


COMMANDS = {
    "clear-cache": clear_cache,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="IP 缓存管理工具")
    parser.add_argument(
        "command",
        choices=COMMANDS.keys(),
        help="要执行的操作",
    )
    args = parser.parse_args()

    COMMANDS[args.command]()


if __name__ == "__main__":
    main()
