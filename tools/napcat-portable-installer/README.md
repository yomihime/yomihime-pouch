# NapCat Portable Installer

一个用于在 Windows 上部署 NapCat Shell 的小工具。🐱

它会使用电脑里正常安装的 QQ，只把 NapCat Shell 和启动脚本放进可移动目录；不会使用 NapCat OneKey 或 `NapCatInstaller.exe`。

目前采用手动 Shell，是为了绕开 OneKey 曾出现的 QQ 下载链接失效和启动注入异常。这个版本不会永久取代上游 OneKey，只是保留一个结构简单、容易检查的部署方案。

## ✨ 它会做什么

- 查找已经安装的 QQ；找不到时，会下载并打开官方 QQ x64 安装程序。
- 按 `127.0.0.1:7890`、`127.0.0.1:7897`、直连的顺序尝试下载。
- 从 [NapCatQQ Releases](https://github.com/NapNeko/NapCatQQ/releases) 下载最新的 `NapCat.Shell.zip`。
- 生成不包含安装时绝对路径的 `start-napcat.ps1` 和 `start-napcat.cmd`。
- 安装目录非空时，会先把原目录重命名为带时间戳的备份。

## 🧰 环境要求

- Windows 10 / 11 x64
- Windows PowerShell 5.1 或更新版本
- 系统中可以使用 `curl.exe`
- 能够访问 GitHub 和腾讯 QQ 下载地址

## 🚀 快速开始

在 PowerShell 中进入本目录，然后执行：

```powershell
.\install-napcat-portable.ps1
```

默认安装到当前目录下的 `NapCat`。也可以指定其他目录：

```powershell
.\install-napcat-portable.ps1 -InstallDir "D:\NapCat"
```

保存默认 QQ 号：

```powershell
.\install-napcat-portable.ps1 -InstallDir "D:\NapCat" -QQ "123456789"
```

安装完成后运行：

```powershell
D:\NapCat\start-napcat.cmd
```

## 📝 参数说明

| 参数 | 说明 |
| :--- | :--- |
| `-InstallDir` | 部署目录，默认为当前目录下的 `NapCat`。不能是磁盘根目录、当前工作目录，也不能包含安装脚本本身。 |
| `-QQ` | 可选的默认 QQ 号，只允许数字；会写入部署目录中的 `qq.txt`。 |

## 📦 便携范围

生成的启动脚本只通过相对路径查找 NapCat Shell，所以整个部署目录可以移动。QQ 仍然是系统安装的软件，不会被复制进部署目录；换到另一台电脑后，需要先在那台电脑上安装兼容版本的 QQ。

NapCat 官方的手动 Shell 用法是：Windows 11 运行 `launcher.bat`，Windows 10 运行 `launcher-win10.bat`。这个工具会根据系统版本自动选择；如果首选文件不存在，也会尝试另一个启动器。详细说明可以看看 [NapCat Shell 官方文档](https://napneko.github.io/guide/boot/Shell)。

## 🌱 OneKey 后续计划

如果上游修复了 OneKey，之后可能会在这个目录里增加一份 OneKey 安装脚本，作为更省事的可选方案。现在这份手动 Shell 版本会继续保留，不会直接替换成 OneKey。

不过，在 OneKey 版本正式加入仓库以前，至少要认真确认这些项目：

- 上游发布说明或相关 issue 已明确说明 QQ 下载问题修复。
- 在 Windows 10 和 Windows 11 上都能完成 QQ 获取、NapCat 注入与首次启动。
- OneKey 使用的 QQ 版本与对应 NapCat 版本兼容，不会让 `packetBackend` 等能力失效。
- 下载失败时不会破坏已有目录，并且能给出可以恢复的错误信息。
- README 清楚说明 OneKey 目录能否移动、是否内置 QQ，以及它和手动 Shell 版本的区别。

想追踪前情，可以看看这些上游记录：[#1973：Windows 一键安装程序下载 QQ 返回 404](https://github.com/NapNeko/NapCatQQ/issues/1973)、[#2019：OneKey 下载与注入问题](https://github.com/NapNeko/NapCatQQ/issues/2019)。

## ⚠️ 使用前的小提醒

- 脚本会下载第三方程序，并且可能打开 QQ 安装程序；运行前请先确认来源和授权条款。
- QQ 安装包使用固定 URL 和 SHA-256 校验。版本更新时，别忘了同步维护脚本里的 URL 与哈希。
- `NapCat.Shell.zip` 使用上游 `latest` 地址，只检查压缩包格式、体积和解压后的关键文件，无法提供固定版本的哈希保证。
- 安装过程不会修改 Windows 系统代理；生成的运行脚本只会清除当前 NapCat 进程继承的代理环境变量。
- NapCat 与 QQ 都是第三方项目，本仓库不会重新分发它们的安装包。
