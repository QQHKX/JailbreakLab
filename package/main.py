import subprocess
import sys
import winreg
import time
import os
import threading
import signal
from typing import List
from collections import defaultdict
import psutil

# 全局控制变量
kill_counts = defaultdict(int)
running = True
exit_event = threading.Event()

def graceful_exit():
    """安全退出程序"""
    global running
    running = False
    exit_event.set()
    print("\n[!] 正在停止所有操作...")
    time.sleep(0.5)
    print("[+] 安全退出完成")
    os._exit(0)

def signal_handler(sig, frame):
    """信号处理"""
    print("\n[!] 接收到退出信号(Ctrl+C)")
    graceful_exit()

def enable_cmd():
    """启用CMD功能"""
    try:
        reg_path = r"Software\Policies\Microsoft\Windows\System"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "DisableCMD")
                print("[+] CMD 已解除限制")
            except FileNotFoundError:
                print("[*] CMD 未被禁用")
    except Exception as e:
        print(f"[!] CMD 解除异常: {e}")

def enable_registry_editor():
    """启用注册表编辑器"""
    try:
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "DisableRegistryTools")
                print("[+] 注册表编辑器已解除限制")
            except FileNotFoundError:
                print("[*] 注册表未被禁用")
    except Exception as e:
        print(f"[!] 注册表解除异常: {e}")


def kill_malicious_process(process_name: str) -> int:
    """结束进程"""
    count = 0
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    proc.kill()
                    count += 1
            except Exception:
                continue
    except Exception:
        pass
    return count

def print_kill_stats():
    """打印统计信息"""
    print("\n=== 进程终止统计 ===")
    for name, count in kill_counts.items():
        print(f"[+] {name}: {count}次")
    print("===================")

def monitor_system(malicious_process_names: List[str]):
    """进程监控"""
    print("[*] 机房软件主动防御已启动")
    while running and not exit_event.is_set():
        try:
            total_killed = 0
            for name in malicious_process_names:
                killed = kill_malicious_process(name)
                if killed > 0:
                    kill_counts[name] += killed
                    total_killed += killed
          
            if total_killed > 0:
                print("[+] 已自动防御机房软件自启操作")
          
            time.sleep(3)
        except Exception as e:
            print(f"[!] 监控异常: {e}")

def generate_dummy_exe():
    """生成无效exe"""
    return (
        b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00\xB8\x00'
        b'\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00INVALID_EXE' * 50
    )

def terminate_and_replace(target_process: str):
    """终止并替换进程"""
    try:
        import psutil
        found = False
        dummy_data = generate_dummy_exe()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            if not running:
                break
            try:
                if proc.info['name'].lower() == target_process.lower():
                    found = True
                    exe_path = proc.info['exe']
                    folder = os.path.dirname(exe_path)
                    target_path = os.path.join(folder, target_process)

                    print(f"\n[!] 发现目标进程 {target_process} (PID: {proc.pid})")

                    try:
                        parent = proc.parent()
                        if parent:
                            parent.kill()
                    except Exception as e:
                        print(f"    [!] 父进程终止失败: {e}")

                    try:
                        proc.kill()
                        print("[+] 进程已终止，等待清理...")
                        time.sleep(2)
                    except Exception as e:
                        print(f"    [!] 进程终止失败: {e}")

                    try:
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        with open(target_path, 'wb') as f:
                            f.write(dummy_data)
                        os.chmod(target_path, 0o444)
                        print(f"[+] 已创建防复活文件: {target_path}")
                    except Exception as e:
                        print(f"    [!] 文件操作失败: {e}")

            except Exception as e:
                print(f"    处理进程时发生未知错误: {e}")

        if not found:
            print(f"[*] 未找到运行中的 {target_process}")

    except Exception as e:
        print(f"[!] 操作失败: {e}")

def input_handler(target_processes: List[str]):
    """命令输入处理"""
    while running and not exit_event.is_set():
        try:
            cmd = input("\n命令输入 [help显示菜单] > ").strip().lower()
          
            if cmd == "help":
                print("\n=== 帮助菜单 ===")
                print("status   - 查看防御统计")
                print("break    - 使用破坏模式")
                print("exit     - 安全退出程序")
                print("=================")
          
            elif cmd == "status":
                print_kill_stats()
          
            elif cmd == "break":
                confirm = input("确认执行不可逆操作？(y/N) > ").lower()
                if confirm == "y":
                    print("[!] 开始破坏操作...")
                    for process in target_processes:
                        terminate_and_replace(process)
                    print("[!] 破坏操作完成")
          
            elif cmd == "exit":
                graceful_exit()
          
            else:
                print("未知命令，输入 help 查看菜单")

        except (KeyboardInterrupt, EOFError):
            graceful_exit()
        except Exception as e:
            print(f"[!] 输入错误: {e}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
  
    print(r"""
   ██████╗  ██████╗ ██╗  ██╗██╗  ██╗██╗  ██╗
  ██╔═══██╗██╔═══██╗██║  ██║██║ ██╔╝╚██╗██╔╝
  ██║██╗██║██║██╗██║███████║█████═╝  ╚███╔╝ 
  ╚██████╔╝╚██████╔╝██╔══██║██╔═██╗  ██╔██╗ 
   ╚═██╔═╝  ╚═██╔═╝ ██║  ██║██║ ╚██╗██╔╝╚██╗
                                            
    机房自由助手 v2.2 - 输入 help 获取帮助
        Made by: -qqhkx-
        个人主页: https://qqhkx.com
        获取更新: https://blog.qqhkx.com
    """)

    print("开始初始化操作...")

    enable_cmd()
    enable_registry_editor()

    monitor_list = [
        "jfglzs.exe", "zmserv.exe", "srvany.exe",
        "StudentMain.exe", "GATESRV.exe",
        "ProcHelper64.exe", "MasterHelper.exe",
        "awa.exe"
    ]
  
    monitor_thread = threading.Thread(target=monitor_system, args=(monitor_list,))
    monitor_thread.start()

    target_list = [
        "jfglzs.exe", "zmserv.exe", "srvany.exe",
        "GATESRV.exe", "ProcHelper64.exe", "MasterHelper.exe"
    ]

    try:
        input_handler(target_list)
    finally:
        graceful_exit()

if __name__ == "__main__":
    main()

