# Emby + MetaTube Manager · Windows 原生部署与操作手册

> 当前工具支持安装时选择目录；下文 `D:\MediaStack` 均为旧手册示例，实际操作请替换为所选目录。目录选择与日常入口以 [README.md](./README.md) 为准。

> **目标 / 任务定义**：在 i5-1235U / 40 GB RAM 的 Windows x64 小主机上，安装并维护 **Emby Server Portable + MetaTube Windows 后端 + Emby 专用 MetaTube 插件**，固定根目录 `D:\MediaStack\`，群晖 Synology 只负责 SMB 媒体文件存储。**不用 Docker、WSL2 或 VM。** 用户接受重新创建 Emby 媒体库，不要求复制旧群晖的 Emby 数据库，但已有 **Emby Premiere Key** 必须保留使用权；不应在任何日志、脚本、对话中暴露 Key。
>
> **面向 AI Agent**：若部署中途遇到问题，请先读全文，按「检查 → 备份 → 最小修改 → 重试 → 验证」进行。未经用户确认，不要删除旧群晖的数据、Emby 套件、Premiere Key，不要格式化分区、开放公网端口、关闭 Windows Defender，也不要把 Key / SMB 密码写入文件或输出。


## 修订记录与失败重试（2026-10-23）

**v2.1 修复：MetaTube v1.4.0 Windows 解压后的文件名不匹配。**
官方 `metatube-server-windows-amd64.zip` 中的可执行文件叫
`metatube-server-windows-amd64.exe`，不是 `metatube-server.exe`。
`Install.ps1` 和 `Update.ps1` 现根据官方已验证 ZIP 资源名称推导可执行文件名，
复制安装后仍统一存储成 `D:\MediaStack\MetaTube\bin\metatube-server.exe`，
因此服务路径无需修改。

**若已经在 Step 3/5 看到 `Expected exactly one metatube-server.exe ... got 0`：**

1. 关闭失败的安装窗口；不要删除 `D:\MediaStack`。
2. 在原安装器目录用此 v2.1 包的文件替换旧脚本，然后再次运行 `Start-Install.cmd`。
3. 脚本会沿用已通过校验的 `D:\MediaStack\Downloads` 缓存，不用重下全部发布包。
4. 在这个错误点尚未开始注册 Windows 服务；旧的 `Staging\initial-*` 可以保留以供排障。
5. **不要执行 `Start-Update.cmd`**，新装还没完成。
6. 如新报错涉及已存在的 `Emby\system` 或服务，请先检查现场，勿清空数据。

**兼容性提醒：** MetaTube 当前 Emby 插件的项目文档标注支持 Emby `4.9.x`，
其 `Release.Emby` 构建引用 `MediaBrowser.Server.Core 4.9.1.80`；
本安装器默认选 Emby 最新正式版（可能是 `4.10.x`），
二者搭配尚未在目标机器上验证。安装完成后要特别检查
Emby 是否实际加载 `MetaTube.dll`、识别页面和刮削；
不要为绕过兼容性错误盲目降级 Emby 或覆盖数据库。
如不兼容，请先采集 Emby 日志，选择经过验证的匹配版本后再操作。

## 0. 用户已经明确的约束

- OS：Windows x64（Windows PowerShell 5.1+），机器 CPU Intel Core i5-1235U / Iris Xe、内存 40 GB。
- **安装目标 `D:\MediaStack\`，必须存在 D: 盘**。所有运行程序、持久化数据和管理脚本尽可能收在这里，方便完整迁移与升级。
- 优先 Windows 原生 Emby Portable + Windows 原生 MetaTube Server，使用 NSSM 注册成 Windows 服务。
- **网络代理默认 `http://127.0.0.1:7897`**。假定端口是可供 HTTP 客户端使用的 **HTTP / Mixed** 代理监听口；若实际是 SOCKS-only，请先确认客户端配置，不要乱改端口或将 SOCKS 当 HTTP 用。
- 下载安装时尝试代理，连接/请求失败则**显式直连**；可不使用代理时也能安装（前提是直连有网络）。
- 运行期 **Emby 与 MetaTube 的网络元数据抓取优先使用本地代理**。代理只给这两个服务进程配置，不修改 Windows 的 WinHTTP / 系统代理、浏览器代理、NAS 或其他应用。
- `localhost/127.0.0.1/::1` 对应 Emby ↔ MetaTube 本地通信，**必须绕过代理**。
- 安装后的手动工作：Emby 首次向导、输入 Premiere Key、设置群晖 NAS SMB 账号和媒体库、实际刮削/转码验证。

## 1. 最快安装步骤

1. 将 ZIP 解压到 Windows 本地目录，例如 `D:\MediaStack-Installer\`（**不要**把安装器文件直接散放到 `D:\MediaStack\Emby\system`）。
2. 确保 `D:` 可读写；以管理员运行 `Start-Install.cmd`。入口会先用本机 PowerShell Parser 对所有 `.ps1` 做**无网络、无修改的语法预检**，再检查 8096、8080 端口，拉取官方最新 **稳定版**，下载 7-Zip `7zr.exe` 和 NSSM，然后安装三个组件。
3. 开启或确认代理客户端在该小主机上监听 **127.0.0.1:7897**。不需要为安装而修改 Windows 系统代理。脚本下载优先代理、失败直连。
4. 打开 `http://localhost:8096`；完成 Emby 初始化，进入 **Emby Premiere** 手动输入原先群晖使用的相同 Key；**不需要在群晖解绑，不必迁移旧 Key 文件**。确认授权有效后再切换旧服务。
5. Emby 的 MetaTube 插件中把后端地址设为 `http://127.0.0.1:8080`；为要刮削的媒体库选择 MetaTube 元数据和图片提供者（设置依版本可能略有区别）。
6. 在 `services.msc` 中为 `MediaStackEmby` 配置具有 NAS SMB 访问权限的专用服务账户；群晖 SMB 给该账户**只读**授权。媒体库使用 `\\NAS-IP\Media\Movies` 等 UNC 路径，**不要使用 Z: 映射盘符**。
7. 依「第 8 节 验收标准」检查 Proxy、服务、NAS、Premiere、媒体搜索、图片与 QSV。验收完成后才停止旧群晖 Emby 套件。运行一次 `Start-Backup.cmd` 并把快照再复制到群晖或其他设备。

> 安装器默认把 `HTTP_PROXY` 和 `HTTPS_PROXY` 写入 **两个服务的 NSSM `AppEnvironmentExtra`**，是**持久配置**：哪怕安装当时 7897 没监听，之后代理起来也可被服务请求使用（部分应用会对 HTTP Client 的配置做缓存，必要时重启服务）。**只影响之后启动的进程，不追溯已经发起的请求。**

## 2. 系统架构、目录与服务

```text
Synology NAS: \\NAS-IP\Media\...   只读 SMB 媒体文件
     ↑↓ SMB / LAN (无需代理)
Windows i5-1235U (D:\MediaStack)
 ├── MediaStackEmby     -> Emby\system\EmbyServer.exe -service   :8096
 │    └── programdata\plugins\MetaTube.dll -> http://127.0.0.1:8080
 └── MediaStackMetaTube -> MetaTube\bin\metatube-server.exe     :8080
      └── data\metatube.db (SQLite)
上述两进程 → HTTP_PROXY + HTTPS_PROXY → 127.0.0.1:7897 → 互联网元数据源
下载脚本     → 若代理可连接则先走 7897，失败重试 DIRECT
```

```text
D:\MediaStack\
├─ Emby\system\                 Emby Portable 程序（升级只替换这一层）
├─ Emby\programdata\            数据库、配置、插件、元数据、授权信息（重要！）
├─ Emby\transcoding\            建议在 Emby 管理页指定为本地转码临时目录
├─ MetaTube\bin\                metatube-server.exe
├─ MetaTube\data\               metatube.db（持久化数据）
├─ Scripts\                     管理脚本和使用说明（安装后自动复制）
├─ Tools\                       nssm.exe、7zr.exe（不要移走 NSSM）
├─ Downloads\                   原始官方发布包（方便审计/重装）
├─ Logs\                        NSSM 标准输出、标准错误
├─ Staging\                     临时解压
├─ Previous\                    升级前程序版本
├─ Backups\                     停服务快照（还应复制到异机）
├─ versions.json                实际安装的三个组件版本
└─ proxy-settings.json          当前服务代理策略，无凭证
```

- 服务名：`MediaStackEmby`、`MediaStackMetaTube`；默认 **延迟自动启动**。
- 默认端口：Emby TCP 8096 仅局域网放行；MetaTube TCP 8080 阻止远端入站，保留回环访问。不得将 8080 暴露到公网。
- 非管理员用户可以使用 Emby 网页管理，但安装、升级、修改 NSSM 服务环境、服务账号需管理员权限。
- Emby 使用便携结构：`Emby\system` 与 `Emby\programdata` 同级。请实际通过 **Emby 后台 → Get Server Info** 确认数据路径位于 `D:\MediaStack\Emby\programdata`。**若不是，停止升级/迁移操作，先解决实际数据位置。**

## 3. 代理策略（尤其重要）

### 3.1 下载安装：自动尝试代理，然后直连

`Common.ps1` 中 `Invoke-Fetch` 是唯一下载和 GitHub API 读取入口：

1. 检查 `127.0.0.1:7897` TCP 监听。
2. 端口可用：**代理请求 → 若 HTTP、TLS、超时等失败，删除临时文件 → 显式 DIRECT 重新下载**。
3. 端口不可用：直接 DIRECT 下载。
4. 下载成功后检查大小；如 GitHub Release API 提供 sha256 digest，则进行 SHA256 验证。安装器不执行来自不明镜像的 EXE。
5. 该策略也应用在 `Start-Update.cmd` 的版本查询与下载流程。

**注意**：TCP 端口开放并不能证明代理节点可以访问目标刮削网站；脚本下载通并不能证明 MetaTube 刮削一定通。若某些网站区域封锁，请验证代理出口和目标站访问情况。

### 3.2 刮削服务：进程级持久代理

默认两服务写入 NSSM `AppEnvironmentExtra`，并使用：

```text
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
NO_PROXY=localhost,127.0.0.1,::1
```

MetaTube 官方支持环境变量代理（要求同时设置 HTTP_PROXY + HTTPS_PROXY）。对于 Emby，.NET 默认 HTTP 客户端通常支持这些变量；**Emby 某些插件/请求可能使用自定义 HTTP 处理器而不遵循变量，必须真实测刮削行为**。

- `HTTP_PROXY`/`HTTPS_PROXY` 的代理 URL 以 `http://` 开头是正确的：**HTTPS 请求经 HTTP CONNECT 隧道代理**，并非强制明文访问目标站。
- `NO_PROXY` 避免 Emby 插件请求 `http://127.0.0.1:8080` 被错误代理；SMB 协议不通过 HTTP 代理。
- **运行中的代理掉线不会自动逐请求直连回退**。服务默认保持代理配置，因此掉线时远程刮削可能失败；本地播放不应被此项代理环境直接影响。
- 如果代理关闭但想立即刮削，请使用 `Set-Proxy.ps1 -Mode Direct`（会重启两个服务）；代理回来再切回 `-Mode Proxy`。
- `-Mode Auto` **只在运行命令当时**探测一次代理 TCP 状态并设置持久服务配置，**不是守护进程或实时故障切换**。
- `Direct` 会清理服务独立设置，但如果 Windows 本机配置了全局代理，Emby/.NET 仍可能继承系统用户的代理配置。切换后要重新验证。

**在管理员 PowerShell 执行：**

```powershell
cd D:\MediaStack\Scripts
.\Set-Proxy.ps1 -Mode Status    # 只读查询，打印 NSSM 环境变量
.\Set-Proxy.ps1 -Mode Proxy     # 强制走 7897，持久生效，重启两个服务
.\Set-Proxy.ps1 -Mode Direct    # 移除两服务自己的环境变量，重启
.\Set-Proxy.ps1 -Mode Auto      # 一次性探测 7897，择一应用，重启
.\Test-MediaStack.ps1           # 只读诊断 + 下载网络测试
```

也可以运行 `Start-Proxy.cmd Proxy`、`Start-Proxy.cmd Status`、`Start-Test.cmd`。

若代理只有 SOCKS5 而不提供 HTTP/Mixed 监听，不要假定上述 HTTP URL 可用；请先在本机代理客户端开启 HTTP 或 Mixed 入口并让它绑定 `127.0.0.1:7897`。**不要为解决刮削而放行公网代理。**

## 4. 脚本清单与幂等边界

| 入口 | 动作 | 数据风险 |
|---|---|---|
| `Start-Install.cmd` / `Install.ps1` | 初装：官方 Release 获取、安装程序、插件、两个服务、代理环境、防火墙 | **拒绝覆盖已安装**，但中途失败可能留下部分文件/服务 |
| `Start-Backup.cmd` / `Backup.ps1` | 停止运行中的服务，复制 Emby `programdata` 与 MetaTube `data` 后恢复原状态 | 不覆盖原数据；会短暂停服 |
| `Start-Update.cmd` / `Update.ps1` | 拉取新稳定版，备份数据，保存旧二进制，替换并启动 | 更改数据库 schema 可能不可逆；升级前必须备份 |
| `Set-Proxy.ps1` | 设置/移除两个 NSSM 服务的持久环境变量 | 默认会重启两个服务，**不中断媒体数据** |
| `Test-MediaStack.ps1` | 网络、端口、服务、文件存在性等检查 | 只读，不修改配置或备份 |
| `Check-Syntax.ps1` | Windows PowerShell 5.1 原生解析所有脚本，发现语法错误则拒绝安装 | 只读、离线、无需管理员权限 |
| `Common.ps1` | 公用的网络、校验、服务与代理工具函数 | 不应单独作为主入口执行 |

各脚本均用 Windows PowerShell 5.1 设计，需管理员权限；安装流程会把 `.ps1`、`.cmd`、`.md` 拷贝进 `D:\MediaStack\Scripts`，之后**只用该目录维护**。安装 ZIP 解压目录不必长期保留，但建议额外存档发布时使用的 ZIP。

## 5. Premiere 从群晖到 Windows

1. 在原群晖 Emby 检查 Premiere 许可；从原始购买邮件或官方找回流程取得原 Key。
2. 在新 Emby 管理控制台手动输入**相同** Key，保证新 Emby 联网后完成激活，并确认显示有效 Premiere。
3. 确认 Intel Quick Sync 硬件转码可使用、4K/HEVC 等实测通过；硬件转码和 HDR Tone Mapping 等需按 Premiere 可用权限和实际媒体格式确认。
4. 只有新机经过完整验收后，才在群晖停用旧套件。
5. Premiere 总设备限制受 Key 的计划与设备额度约束；不是把购买绑定到群晖 CPU 上，也不是复制 `programdata` 才能迁走。

**安全原则：禁止**将 Premiere Key 硬编码进脚本、提交 GitHub、打印到日志或发给 AI Agent；人工在网页输入。备份 Emby `programdata` 可能包含许可和其他隐私数据，需限制访问。

来源：https://emby.media/support/articles/Premiere-Multiple-Servers.html

## 6. NAS / SMB 账户与 Windows 服务

- 建议在群晖新建专用只读 SMB 账号，权限只涵盖指定媒体共享。
- Windows 服务默认 LocalSystem，**不应假定**其能使用当前登录用户的 SMB 凭据。运行 `services.msc` → `MediaStackEmby` → 属性 → 登录，切换为专用本地账户；需要「作为服务登录」权限、`D:\MediaStack\Emby` 的必要写权限和群晖 SMB 读取权限。
- Windows 资源管理器能打开 SMB 共享 ≠ Windows 服务账户也能访问。排障要使用运行服务的同一安全上下文验证。
- 媒体路径采用 `\\NAS-IP\Media\Movies`，不要用 `Z:` 等映射盘；对路径的写入权限应尽量关闭，元数据存到 Emby 本地数据库/目录。
- 共享名称或路径改动会影响媒体库；未来迁移 Windows 主机时保持相同 UNC 更容易复原。

## 7. AI Agent 排障流程（必须遵循）

**0）先收集状态，不要第一时间重装。**

```powershell
Get-Service MediaStackEmby,MediaStackMetaTube -ErrorAction SilentlyContinue
Get-CimInstance Win32_Service -Filter "Name='MediaStackEmby' OR Name='MediaStackMetaTube'" |
  Select-Object Name,State,StartName,PathName
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object LocalPort -in 7897,8080,8096 |
  Select-Object LocalAddress,LocalPort,OwningProcess
Get-Content 'D:\MediaStack\versions.json' -ErrorAction SilentlyContinue
Get-Content 'D:\MediaStack\proxy-settings.json' -ErrorAction SilentlyContinue
& 'D:\MediaStack\Scripts\Test-MediaStack.ps1'
```

以上诊断不会展示 Premiere Key；如需收集日志，**先检查并遮盖 URL token、Key、用户名、文件名中敏感信息**，不要把整套 `programdata` 发给第三方。

**1）安装下载失败：**看 `HTTP [Proxy]` 和 `HTTP [Direct]` 两次尝试的日志。先测试 `7897` 监听，再检查代理客户端是否允许本机 HTTP/Mixed；检查 GitHub 访问、DNS、TLS、防火墙和 Release API 限流。切勿为绕过 TLS 校验设置全局忽略证书错误；有必要时手工预先下载**官方文件**放在 `Downloads` 目录。

**2）服务无法启动：**检查 NSSM 固定路径是否存在、`AppDirectory`、`AppParameters`、exe 是否存在，查看 `D:\MediaStack\Logs\MediaStack*.stderr.log`、Windows 事件查看器和 Emby `programdata\logs`。登录错误 1069 通常优先检查服务账号密码/「作为服务登录」权限，1053 要结合日志分析。不要在服务运行时覆写 exe 和数据库。

**3）代理可用但刮削失败：**先运行 `Set-Proxy.ps1 -Mode Status`，检查**两个服务**的 `AppEnvironmentExtra` 包含 HTTP_PROXY、HTTPS_PROXY、NO_PROXY；代理监听不代表远端出口可达。看 MetaTube 后端日志及 Emby 插件/服务器日志。测试 Emby 的手动识别、元数据更新、图片能否加载。若 `127.0.0.1:8080` 插件后端无法访问，优先检查回环/NO_PROXY/防火墙，不要强迫 localhost 走代理。MetaTube 的某些 Emby 图像问题与 HTTP 后端有关，按官方 FAQ 再考虑 HTTPS 反向代理，**不要预装不必要组件**。

**4）NAS 能在资源管理器打开，但 Emby 扫描空白：**检查 `MediaStackEmby` 的 `StartName`、UNC、Synology SMB ACL、NTFS 本地权限；不要以能访问映射盘 Z: 作为通过标准。

**5）Premiere 有效但转码退化：**检查 Emby 控制台硬件加速选项、实际转码流日志、Intel GPU 驱动、D3D11、HDR tone mapping、字幕烧录与电源模式。不要承诺一个固定的 4K 并发数量。

**6）升级失败或插件不兼容：**确认 `Backups\snapshot-*` 存在且完整，服务停止后才能恢复。恢复要成套处理 **程序版本 + Emby programdata + MetaTube data + MetaTube.dll**；切不可仅换回旧 exe 而继续用被升级的新数据库。保存失败现场日志后再调整。

**7）安装中断留下部分状态：**`Install.ps1` 拒绝对已经存在的 `system`/服务直接重装。先确认哪些程序与数据实际已创建，备份存在的状态，谨慎补足缺项或清理中途 staging。**不得直接删除整个 `D:\MediaStack`**，因为安装过程中可能已产生人工输入的有效用户/授权和数据库。

## 8. 验收标准 / Definition of Done

- [ ] `EmbyServer.exe` 在 `D:\MediaStack\Emby\system`，两个 NSSM 服务为 Running 且延迟自动启动。
- [ ] Emby 页面 `http://localhost:8096` 能登录；服务数据目录核实为 `D:\MediaStack\Emby\programdata`。
- [ ] MetaTube 后端 `127.0.0.1:8080` 在本机可连接，`metatube.db` 有持久文件；Emby 识别 MetaTube 插件。
- [ ] `Set-Proxy.ps1 -Mode Status` 表明两服务的 HTTP_PROXY/HTTPS_PROXY/NO_PROXY 均正确；重启后仍有效。
- [ ] 实际刮削 1～3 个媒体条目：标题、演员、海报、背景图至少抽样成功，相关代理客户端网络记录能够看到预期外网连接。
- [ ] 群晖 UNC 媒体库路径可被 Emby **服务账号**读取并索引；媒体源不被自动写坏。
- [ ] Premiere 状态有效；至少一段需要转码的媒体确认实际使用 QSV/D3D11（按硬件/驱动支持范围）。
- [ ] `Start-Backup.cmd` 成功；备份目录里有 Emby programdata 和 MetaTube data，并将备份复制出 D 盘。
- [ ] 对比原群晖 Emby 完成切换，旧系统先停用，未被删除。

如果任何一条未完成，请明确标注 **已完成 / 待人工输入 / 未验证 / 失败原因**，不要谎称“全部部署成功”。

## 9. 版本与官方依据

所有程序动态选取官方 GitHub 的 `releases/latest`，不在脚本里写死具体版本：

- Emby 官方 Releases：https://github.com/MediaBrowser/Emby.Releases/releases
- Emby Windows Portable：https://emby.media/windows-server.html
- MetaTube 后端：https://github.com/metatube-community/metatube-server-releases/releases
- MetaTube Emby 插件：https://github.com/metatube-community/jellyfin-plugin-metatube/releases
- MetaTube 后端部署：https://metatube-community.github.io/wiki/server-deployment/
- MetaTube **代理配置**（必读）：https://metatube-community.github.io/wiki/proxy-configuration/
- NSSM 服务管理：https://nssm.cc/usage
- Emby Windows 服务：https://emby.media/support/articles/Running-Emby-Server-as-a-Windows-Service.html
- .NET HTTP 代理机制：https://learn.microsoft.com/dotnet/api/system.net.http.httpclient.defaultproxy

**尚未进行真实 Windows 验证**：当前版本为离线修改与静态检查，未在用户的小主机上实际注册服务、下载软件、刮削或访问群晖。请 AI Agent 按第 8 节采集真实验收结果；不要把静态检查当作运行通过。
