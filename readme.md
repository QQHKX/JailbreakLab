# 机房自由助手 - JailbreakLab

## 📜 项目描述

本工具是针对Windows平台机房管理系统开发的防御解除工具，主要用于解决以下问题：

- 恢复被系统策略限制的CMD命令提示符
- 解除注册表编辑器的禁用状态
- 实时监控并拦截管理软件进程
- 破坏性清除顽固监控程序（可配置）
- 统计防御操作数据

特别适用于学校机房环境，实现系统自主脱离控制。

---

## 🎯 核心功能

### ⚙️ 系统恢复模块

| 功能         | 实现原理                                                     |
| ------------ | ------------------------------------------------------------ |
| CMD解除      | 删除`HKCU\Software\Policies\Microsoft\Windows\System\DisableCMD` |
| 注册表解除   | 删除`HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System\DisableRegistryTools` |
| 依赖自动安装 | 无缝安装必要的psutil库，使用清华镜像加速                     |

### 🔍 进程监控系统

```text
监控频率：      每3秒扫描一次
保护策略：      立即终止+防御计数
防御名单：      包括但不限于：
                 * jfglzs.exe
                 * zmserv.exe
                 * GATESRV.exe
                 * ProcHelper64.exe
```

### 💣 破坏性模式

```python
def terminate_and_replace():
    # 攻击链：
    1. 终止目标进程及其父进程
    2. 定位进程所在路径
    3. 删除原程序文件
    4. 生成无效EXE文件（MZ头+填充数据）
    5. 设置文件为只读属性（0444）
```

---

## 🛠️ 安装与使用

### 环境要求

- Windows 7/10/11 (x64推荐)
- Python 3.6+ (仅开发环境需要)
- 管理员权限（建议右键以管理员身份运行）

### 快速启动

```bash
# 克隆仓库
git clone https://github.com/qqhkx/JailbreakLab.git

# 运行程序
python main.py
```

---

## 🕹️ 使用说明

### 命令列表

| 命令    | 功能描述               | 示例输入            |
| ------- | ---------------------- | ------------------- |
| status  | 查看防御统计报表       | > status            |
| break   | 激活破坏模式（不可逆） | > break → 输入y确认 |
| install | 重新安装依赖库         | > install           |
| exit    | 安全退出程序           | > exit              |

### 操作示例

```text
命令输入 [help显示菜单] > break
确认执行不可逆操作？(y/N) > y
[!] 开始破坏操作...
[!] 发现目标进程 jfglzs.exe (PID: 3848)
[+] 进程已终止，等待清理...
[+] 已创建防复活文件: C:\Program Files\LabControl\jfglzs.exe
```

---

## ⚠️ 法律与安全声明

### 使用须知

- 本工具仅供技术研究和合法场景使用
- 禁止用于教学机构的教学管理系统破解
- 使用者需遵守所在地计算机使用相关法律

### 风险声明

```diff
- 可能触发杀毒软件误报（建议添加白名单）
- 破坏模式下相关软件将永久失效
- 不恰当使用可能造成系统异常
+ 采用非持久化设计，重启恢复修改
```

### 许可证

[GPL-3.0 License](LICENSE)

---

## 🌐 技术支持

| 类型       | 说明                                             |
| ---------- | ------------------------------------------------ |
| 个人主页   | [https://qqhkx.com](https://qqhkx.com)           |
| 问题反馈   | QQ：1816078482                                   |
| 开发者博客 | [https://blog.qqhkx.com](https://blog.qqhkx.com) |

---

> 📢 本工具尊重学校规，旨在提升学生对系统控制技术的理解。使用前请确认您有合法权限操作目标设备。
