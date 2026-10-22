# Emby + MetaTube Manager

一个用于在 Windows 上安装和管理 Emby + MetaTube 的小工具。🎬

使用 Emby 便携版、MetaTube 原生后端和 NSSM Windows 服务，媒体文件可以继续放在 NAS 上，通过 SMB 共享读取。无需 Docker 或 WSL。

## ✨ 它会做什么

- 从官方 GitHub Releases 获取 Emby、MetaTube 后端和 Emby 插件的最新稳定版。
- 下载优先尝试本地代理，失败后直连；复用缓存，发布资源提供 SHA-256 时进行校验。
- 将两个程序注册为延迟自动启动的 Windows 服务。
- 提供启动服务、打开 Emby 网页、查看状态、诊断、备份、升级和代理切换入口。
- 检测到旧安装时询问是否强制安装，确认后先停服备份，再替换程序并修复服务配置。
- 启动后检查服务状态和本地 HTTP 响应，检查失败会显示错误。

## 🧰 环境要求

- Windows x64，Windows PowerShell 5.1 或更新版本。
- 目标电脑有可写的本地磁盘；安装时可以选择部署目录，支持含空格的路径。
- 能访问 GitHub、7-Zip 和 NSSM 官方下载地址。
- 安装、启动服务、备份、升级及修改代理时需要管理员权限，入口会请求提权。

## 🚀 快速开始

将本目录完整复制到准备运行媒体服务的 Windows 电脑，然后双击：

```text
Start.cmd
```

首次使用选择 `4 安装/强制安装`。

安装前会提示部署目录，例如输入 `E:\Media Stack`。回车使用默认值：有 D 盘时为 `D:\MediaStack`，没有 D 盘时为系统盘下的 `MediaStack`；后续安装默认使用记住的目录。也可以通过参数指定，跳过目录询问：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Install.ps1 -InstallDir "E:\Media Stack"
```

目录需为本地绝对路径，不能是磁盘根目录、Windows / Program Files 目录或包含安装脚本的管理目录。安装脚本可放在部署目录以外，也可放在部署目录的 `Scripts` 子目录。当前两个服务名固定，选择新位置不会自动迁移已有安装，也不能同时部署第二套同名服务。

安装完成后打开：

```text
Emby：http://127.0.0.1:8096
MetaTube：http://127.0.0.1:8080/
```

在 Emby 页面完成初始化，需要时手动输入 Premiere Key，并将 MetaTube 插件的后端地址设为 `http://127.0.0.1:8080`。MetaTube 根地址显示 JSON 属于正常情况。

之后日常使用选择 `1 启动服务`，再选择 `2 打开 Emby 网页`；也可以直接双击 `Start-Services.cmd`。服务已运行时不会重复重启，关闭启动窗口也不会停止 Windows 服务。

安装后管理脚本会复制到所选目录的 `Scripts` 子目录，以后可以从该目录操作。更新工具时将本目录内容复制进去即可，无需为了更新启动脚本重新安装媒体服务。

安装位置保存到工具目录和部署目录 `Scripts` 中的 `mediastack-settings.json`，只有路径信息。后续启动、诊断、备份、升级和代理设置统一使用该位置；部署目录内的管理脚本优先识别自身的父目录。配置文件在目标机运行安装时生成，不需要手动创建。

## 🌸 常用入口

| 文件 | 用途 |
| :--- | :--- |
| `Start.cmd` | 中文统一菜单，包含日常启动和维护操作。 |
| `Start-Services.cmd` | 启动已有的 MetaTube、Emby 服务，并检查 HTTP 就绪。 |
| `Start-Install.cmd` | 首次安装，或确认后强制安装。 |
| `Start-Test.cmd` | 检查服务、端口和关键文件，默认不访问外网。 |
| `Start-Backup.cmd` | 停服备份数据库与配置，再恢复原先运行中的服务。 |
| `Start-Update.cmd` | 获取最新稳定版，备份数据并保留旧程序后升级。 |
| `Start-Proxy.cmd` | 查询或切换服务代理，默认查询状态。 |

也可以在 PowerShell 中使用统一入口：

```powershell
# 启动服务
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\MediaStack.ps1 -Action StartServices

# 查看服务和 HTTP 状态
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\MediaStack.ps1 -Action ServiceStatus
```

## 📝 代理设置

默认代理为 `http://127.0.0.1:7897`，需要 HTTP 或 Mixed 监听端口。

部署之后也能修改：在 `Start.cmd` 中选择 `9 设置/启用代理`，输入新的 HTTP(S) 代理地址；回车保留当前地址。地址保存到部署目录的 `proxy-settings.json`，之后切换模式会继续使用它。

```powershell
.\Start-Proxy.cmd Status  # 查看代理状态
.\Start-Proxy.cmd Proxy   # 使用代理
.\Start-Proxy.cmd Direct  # 移除服务专属代理配置
.\Start-Proxy.cmd Auto    # 根据当次代理端口探测结果选择
```

也可以在管理员 PowerShell 中直接设置地址：

```powershell
.\Set-Proxy.ps1 -Mode Proxy -ProxyUrl "http://127.0.0.1:7890"
```

这会同时修改 Emby 和 MetaTube 的服务代理，保留其他服务环境变量和已有绕过地址，并默认重启两个服务。不支持在地址中保存账号密码；需要稍后再重启时可加 `-NoRestart`。下载代理仍使用安装脚本原来的配置，与这里的运行期代理地址分别管理。

代理只配置到 Emby 和 MetaTube 服务，不修改 Windows 全局代理；本地回环地址绕过代理。变更后默认重启两个服务。`Auto` 只探测一次，不会在运行过程中自动切换网络；应用和插件是否实际遵循代理，还需要通过刮削验证。

## 📦 数据与重装

程序、数据、下载缓存和备份分别位于所选部署目录内的独立目录。Emby 数据位于 `Emby\programdata`，MetaTube 数据位于 `MetaTube\data`，请保留这些目录。

已有安装再次运行安装入口时，会提示：

```text
检测到已有安装，是否强制安装？[y/N]
```

只有输入 `y` 或 `Y` 才继续。强制安装会先准备新程序，再停服备份并逐文件校验；备份成功后替换程序、修复服务启动配置，保留数据库、用户配置、服务账户和已有服务环境。恢复材料存放在 `Backups\reinstall-*`。

备份位于同一块磁盘，建议另存到其他设备。目前不提供自动回滚；若版本变更导致数据库迁移，恢复时需要成套恢复匹配的程序、插件和数据。

## ⚠️ 使用前的小提醒

- 最新稳定版组合仍需验证插件兼容性；服务和 HTTP 就绪不等于刮削、SMB、Premiere 或硬件转码已经验收。
- NAS 媒体库使用 `\\NAS-IP\共享名\目录`，服务账户需要对应的读取权限；不要依赖当前登录用户的映射盘符。
- 如果启动后立即退出，检查 `Logs`、`Emby\programdata\logs` 和 Windows 事件日志。智能应用控制可能拦截依赖 DLL；脚本不会更改系统防护设置。
- 启动服务前先退出手动运行的测试实例，避免两个实例同时访问数据库。
- Premiere Key 和 SMB 密码应在目标机界面中配置，不要写进脚本或提交到仓库；备份也可能包含敏感信息。
- 本仓库不捆绑第三方安装包，Emby、MetaTube、NSSM 和 7-Zip 遵循各自许可证。

更多手动排障步骤见 [OPERATIONS.md](./OPERATIONS.md)。该文件保留原始部署手册，其中 `D:\MediaStack` 为示例路径，使用时替换为所选部署目录；历史版本与现场记录以当前脚本为准。
