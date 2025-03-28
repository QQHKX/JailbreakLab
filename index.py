import subprocess
import sys
import winreg
import time
import os
import threading
import signal
import psutil
from typing import List
from collections import defaultdict

# 配置参数
MONITOR_PROCESSES = [
    "jfglzs.exe", "zmserv.exe", "srvany.exe",
    "StudentMain.exe", "GATESRV.exe",
    "ProcHelper64.exe", "MasterHelper.exe",
    "awa.exe"
]

TARGET_PROCESSES = [
    "jfglzs.exe", "zmserv.exe", "srvany.exe",
    "GATESRV.exe", "ProcHelper64.exe", "MasterHelper.exe"
]

CONFIG = {
    "monitor_interval": 3,  # 监控间隔(秒)
    "psutil_install_source": "https://pypi.tuna.tsinghua.edu.cn/simple"
}

# 全局控制变量
kill_counts = defaultdict(int)
psutil_available = False
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

def enable_feature(feature_type: str):
    """启用系统功能通用方法"""
    registry_paths = {
        'cmd': (r"Software\Policies\Microsoft\Windows\System", "DisableCMD"),
        'registry': (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableRegistryTools"),
        'taskmgr': (r"Software\Microsoft\Windows\CurrentVersion\Policies\System", "DisableTaskMgr")
    }

    if feature_type not in registry_paths:
        raise ValueError(f"不支持的功能类型: {feature_type}")

    reg_path, value_name = registry_paths[feature_type]
    feature_names = {
        'cmd': "CMD",
        'registry': "注册表编辑器",
        'taskmgr': "任务管理器"
    }

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, value_name)
                print(f"[+] {feature_names[feature_type]} 已解除限制")
            except FileNotFoundError:
                print(f"[*] {feature_names[feature_type]} 未被禁用")
        return True
    except Exception as e:
        print(f"[!] {feature_names[feature_type]} 解除异常: {e}")
        return False

def show_file_extensions():
    """启用文件后缀显示"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as reg_key:
            winreg.SetValueEx(reg_key, "HideFileExt", 0, winreg.REG_DWORD, 0)
            print("[+] 文件后缀显示已启用")
        
        print("[*] 正在尝试重启资源管理器以应用更改...")
        try:
            subprocess.check_call(
                ["taskkill", "/f", "/im", "explorer.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("[+] 资源管理器已重启")
        except subprocess.CalledProcessError:
            print("[!] 无法自动重启资源管理器，请手动重启或注销以应用设置")
        except Exception as e:
            print(f"[!] 重启资源管理器时出错: {e}")
        return True
    except Exception as e:
        print(f"[!] 启用文件后缀显示失败: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    global psutil_available
    try:
        import psutil
        psutil_available = True
        return True
    except ImportError:
        print("[!] 正在尝试自动安装必要依赖...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "psutil",
                "-i", CONFIG["psutil_install_source"]
            ], creationflags=subprocess.CREATE_NO_WINDOW)
            print("[+] 依赖安装成功")
            psutil_available = True
            return True
        except Exception as e:
            print(f"[!] 自动安装失败，请手动执行：\n{sys.executable} -m pip install psutil")
            return False

def kill_malicious_process(process_name: str) -> int:
    """结束进程"""
    count = 0
    if not psutil_available:
        return 0
    try:
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

def monitor_system():
    """进程监控"""
    print("[*] 机房软件主动防御已启动")
    while running and not exit_event.is_set():
        try:
            total_killed = 0
            for name in MONITOR_PROCESSES:
                killed = kill_malicious_process(name)
                if killed > 0:
                    kill_counts[name] += killed
                    total_killed += killed
          
            if total_killed > 0:
                print("[+] 已自动防御机房软件自启操作")
          
            time.sleep(CONFIG["monitor_interval"])
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
    if not psutil_available:
        print("[!] 需要先安装依赖 (输入 install)")
        return

    try:
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

def input_handler():
    """命令输入处理"""
    while running and not exit_event.is_set():
        try:
            cmd = input("\n命令输入 [help显示菜单] > ").strip().lower()
          
            if cmd == "help":
                print("\n=== 帮助菜单 ===")
                print("status   - 查看防御统计")
                print("break    - 使用破坏模式")
                print("install  - 重试安装依赖")
                print("exit     - 安全退出程序")
                print("=================")
          
            elif cmd == "status":
                print_kill_stats()
          
            elif cmd == "break":
                confirm = input("确认执行不可逆操作？(y/N) > ").lower()
                if confirm == "y":
                    print("[!] 开始破坏操作...")
                    for process in TARGET_PROCESSES:
                        terminate_and_replace(process)
                    print("[!] 破坏操作完成")
          
            elif cmd == "install":
                install_dependencies()
          
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

    # 启用系统功能
    enable_feature('cmd')
    enable_feature('registry')
    enable_feature('taskmgr')
    show_file_extensions()
    
    # 安装依赖
    install_dependencies()

    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_system)
    monitor_thread.start()

    # 处理用户输入
    input_handler()

if __name__ == "__main__":
    main()
