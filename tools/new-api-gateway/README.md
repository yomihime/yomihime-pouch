# New API 局域网网关

在 Windows 10/11 x64 mini PC 上运行原生 New API。代理软件只需提供一个可用的代理端口。New API 通过渠道代理访问 OpenAI，局域网客户端直连 mini PC，用各自的网关令牌调用模型。

## 首次部署

1. 把本目录复制到 mini PC 上当前用户可写的本地目录，例如 `C:\Tools\new-api-gateway`。用普通用户双击 `Start.cmd`。
2. 选 **1 下载最新版**，或双击 `Start-Install.cmd`。安装器查询上游标记的 Latest Release，优先通过本机 HTTP/Mixed 代理 `127.0.0.1:7897` 下载，失败后尝试 `7890`，最后直连。版本查询和文件下载都使用此顺序。安装器按该 Release 的 SHA256 校验后将 EXE 放入 `bin\`。[上游最新发布](https://github.com/QuantumNous/new-api/releases/latest)
3. 选 **3 本机启动**，保持窗口打开，访问 `http://127.0.0.1:3000`。完成初始化、设置管理员密码，并在系统设置关闭公开注册。
4. 在「渠道」添加 **OpenAI** 渠道，上游地址填 `https://api.openai.com`，密钥填官方 OpenAI Key，模型填该 Key 可用的模型。在渠道编辑页的代理地址栏填 `http://127.0.0.1:7890`（替换成实际端口）。若界面提供渠道设置 JSON 编辑框，在渠道设置里合并 `{"proxy":"http://127.0.0.1:7890"}`。保存后执行渠道测试。SOCKS 端口可填 `socks5h://127.0.0.1:1080`。下载代理和渠道代理分别生效。[官方渠道代理说明](https://github.com/QuantumNous/new-api/blob/main/docs/channel/other_setting.md)
5. 在「令牌」按设备创建网关令牌，设定模型范围和额度。确认所属用户有可用额度，渠道分组与令牌匹配。先在本机完成下方对话验证，再按 Ctrl+C 停止网关。
6. 在可信的 Windows **专用网络**上，右键以管理员身份运行 `Start.cmd`，选 **5 配置防火墙**。规则限定当前程序、TCP 端口和本地子网。如果 Windows 另行弹出通用放行提示，可取消该提示。随后用普通用户运行 `Start.cmd`，选 **4 局域网启动**。

### 离线安装

在联网电脑打开上面的最新发布页，下载 Windows 的 `new-api-<标签>.exe` 和同页的 `checksums-windows.txt`。保留原文件名，将两者放入同一个目录并拷到 mini PC。菜单选 **2 离线导入** 并输入 EXE 路径即可，全程使用本地文件。

## 客户端与验证

假设 mini PC 的局域网 IPv4 为 `192.168.1.50`（在 mini PC 上用 `ipconfig` 查活动网卡）。在客户端选择 OpenAI 兼容接口，Base URL 填 `http://192.168.1.50:3000/v1`，API Key 填该设备的**网关令牌**，代理留空。上游 Key 只填在 mini PC 的渠道后台。局域网模式也会开放管理页面，明文 HTTP 适用于可信内网。

在工具目录打开 PowerShell。本机可双击 `Start-Test.cmd`，也可运行第一行。局域网电脑只需复制 `Test-Gateway.ps1`，把第二行中的 IP 和模型替换为实际值。令牌在提示时输入。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-Gateway.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\Test-Gateway.ps1 -BaseUrl http://192.168.1.50:3000/v1 -Model "你的对话模型"
```

默认检查网关鉴权和模型列表。加 `-Model` 会发送一次实际的对话请求，消耗上游额度。在系统代理关闭、代理软件端口仍监听的情况下发起请求，对照代理软件的连接记录确认目的地为 `api.openai.com`，且规则选中了代理节点。本机验证也可加 `-Model`。

## 日常使用

- **启动与停止**　双击菜单或运行 `.\Start.cmd -Action Lan`，使用期间保留窗口，Ctrl+C 停止。登录自启可在 `shell:startup` 中创建指向 `"C:\Tools\new-api-gateway\Start.cmd" -Action Lan` 的快捷方式，并让代理软件随同一用户登录启动。删除快捷方式即可取消。
- **升级**　停机并备份整个工具目录后，双击 `Start-Update.cmd` 或选菜单 **6 更新最新版**。已是目标版本时跳过下载；发现新版本时，校验成功后替换 EXE，前一份保存在 `bin\new-api.previous.exe`。重新启动后检查网关。若需回退数据库迁移，请恢复同一次停机备份。离线升级可运行 `.\Start-Update.cmd -SourceFile "D:\Downloads\new-api-<标签>.exe"`。
- **修改端口**　例如 `.\Start.cmd -Action Lan -Port 3100`。用管理员终端执行 `.\Start.cmd -Action Firewall -Port 3100` 更新同一条规则，同时修改客户端地址和自启快捷方式。
- **备份与迁移**　停止网关并等待退出后，备份整个工具目录。默认 SQLite 数据库和日志在 `data\`，备份包含渠道密钥和令牌，请按密钥保管。迁移后在新位置重新配置防火墙。
- **连不上**　本机能用而局域网超时，先确认正在用局域网模式、客户端 IP 地址指向活动网卡、Windows 网络配置文件为专用。模型列表可读而对话失败，查看渠道测试和网关日志，核对代理端口、模型、分组及额度。
- **移除防火墙规则**　在管理员 PowerShell 运行 `Remove-NetFirewallRule -Name Yomihime-NewApiGateway`。
