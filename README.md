# 枝江小馒头

一个使用 PyQt6 制作的 ASoul/BongoCat 风格桌面宠物应用，支持键盘动画、鼠标同步移动和多角色切换。

当前改造目标是 **VUP Pet**：保留实时键盘/鼠标交互的独立桌宠，并可通过 Codex skill `$vup-pet` 启动、停止和查询状态。

## 与 Codex Pet 的区别

- **VUP Pet**：本项目的独立 PyQt6 桌宠，负责透明置顶窗口、键盘监听、鼠标同步和角色切换。
- **VUP Pet Skill**：Codex skill，命令名为 `$vup-pet`，用于控制独立桌宠进程。
- **Codex Pet**：Codex 桌面应用官方 `/pet` 命令加载的自定义资源包，格式为 `pet.json + spritesheet.webp`。

本项目 MVP 不把实时键盘/鼠标交互塞进官方 Codex Pet 资源包；官方资源包路径只适合状态驱动的静态动画宠物。

## 功能特性

- 透明无边框窗口，置顶显示
- 键盘按下时，键盘图片向下移动并回弹
- 鼠标移动时，鼠标图片在限定范围内同步移动
- 实时按键显示：在窗口上显示当前按下的键，支持自定义位置和字体大小
- 支持多角色切换（自动识别 `img` 目录下的文件夹）
- 可拖动窗口位置
- 右键菜单支持切换角色、设置和退出
- 支持通过 `$vup-pet start|stop|status` 控制进程

## 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

`pywin32` 仅在 Windows 下安装；macOS 不需要该依赖。

## macOS 权限

全局键盘和鼠标监听依赖系统权限。macOS 首次运行时可能需要在系统设置中授予终端或 Python：

- 辅助功能权限
- 输入监控权限

缺少权限时，窗口仍可能显示，但键盘/鼠标实时动画可能无法触发。

## 运行

直接启动独立桌宠：

```bash
python3 main.py
```

通过 VUP Pet 启动器控制：

```bash
python3 vup_pet_launcher.py start
python3 vup_pet_launcher.py status
python3 vup_pet_launcher.py stop
```

启动器会使用 `${CODEX_HOME:-$HOME/.codex}/vup-pet/` 保存：

- `pid.json`：进程信息
- `state.json`：轻量 bridge 状态

## Codex Skill

仓库内提供 skill 文件：

```text
skills/vup-pet/
├── SKILL.md
└── scripts/vup_pet_launcher.py
```

在 Codex 中使用稳定 skill 调用形式：

```text
$vup-pet start
$vup-pet status
$vup-pet stop
```

该 skill 只负责启动、停止和查询独立 VUP Pet，不修改 Codex 应用本体。

## 目录结构

```text
img/
├── 角色名1/
│   ├── bgImage.png
│   ├── keyboardImage.png
│   ├── mouseImage.png
│   ├── leftClickImage.png
│   └── rightClickImage.png
├── 角色名2/
│   ├── bgImage.png
│   ├── keyboardImage.png
│   ├── mouseImage.png
│   ├── leftClickImage.png
│   └── rightClickImage.png
...
```

## 使用说明

- 左键拖动窗口可以移动位置
- 右键点击窗口打开菜单
- 在菜单中选择“切换角色”可以切换不同角色
- 在菜单中选择“设置”可以调整窗口和图层相关配置
- 按下任意键盘按键，键盘图片会向下移动并回弹
- 移动鼠标，鼠标图片会在限定范围内同步移动
- 设置会自动保存到配置文件中

## 平台说明

- macOS：默认按正常 PyQt 透明置顶窗口显示，不模拟 Windows 任务栏隐藏。
- Windows：保留隐藏任务栏、启动文件夹等 Windows 特定功能。
- 非 Windows 平台：Windows 任务栏和启动文件夹相关菜单会被隐藏或安全跳过。

## 注意事项

- 确保 `img` 目录下每个角色文件夹都包含五张图片：`bgImage.png`、`keyboardImage.png`、`mouseImage.png`、`rightClickImage.png`、`leftClickImage.png`。
- 图片建议使用透明背景的 PNG 格式。
- 如果要重新分发，请先确认 GPL-2.0 和角色素材授权风险。
