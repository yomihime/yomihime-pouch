# yomihime-pouch

如月怜的赛博小收纳包，放着随手做的小工具、脚本和 AI 技能。🎀

> 💡 **说明**：
> - 这里面的工具大多是如月小姐摸鱼时突发奇想写的 `.bat` / `.cmd` / `.ps1` / `.py` 脚本。
> - 点击对应名称进入子文件夹查看详细用法。
> - 欢迎提 Issue 告诉我你的想法，或者 Fork 回去自己玩 ✨

## 🌷 收纳目录

### 小工具

| 名称 | 用途 | 文档 |
| :--- | :--- | :--- |
| 📊 **Git Commit Counter** | 统计 Git 仓库中个人的历史代码提交行数。 | [查看文档](./tools/git-commit-counter/) |
| 🐱 **NapCat Portable Installer** | 使用系统 QQ 部署可移动的 NapCat Shell 目录。 | [查看文档](./tools/napcat-portable-installer/) |
| 🎬 **Emby + MetaTube Manager** | Windows 原生 Emby + MetaTube 安装、启动、备份、升级与诊断。 | [查看文档](./tools/emby-metatube-manager/) |

### AI 技能

| 名称 | 用途 | 文档 |
| :--- | :--- | :--- |
| 🧭 **Interactive Planning Doc** | 把交互式讨论整理成可执行计划文档。 | [查看文档](./skills/interactive-planning-doc/) |
| 🧵 **Auto Style String Resources** | 审计、归类并分批风格化程序字串和 UI 文案。 | [查看文档](./skills/auto-style-string-resources/) |
| 🏗️ **Development Pipeline** | 需求切片、顺序轮次与轮内并行，检查点验收和实时观察网页。 | [查看文档](./skills/development-pipeline/) |
| 🛠️ **Multi-agent Engineering** | 按任务选择模型，协调小切片实现、独立审查与验证。 | [查看文档](./skills/multi-agent-engineering/) |
| 🗃️ **Project Memory** | 完整读取本地当前状态快照，改写前归档历史，用短入口恢复工作。 | [查看文档](./skills/project-memory/) |
| 🎨 **UI Design** | 提取既有界面设计规范，并设计和验证一致的界面。 | [查看文档](./skills/ui-design/) |
| 🧭 **yomihime init** | 检查技能可用性与版本，安全整理项目工作区。 | [查看文档](./skills/yomihime-init/) |

## 🗂️ 目录结构

```text
yomihime-pouch/
├── tools/
│   ├── git-commit-counter/
│   ├── napcat-portable-installer/
│   └── emby-metatube-manager/
├── skills/
│   ├── auto-style-string-resources/
│   ├── development-pipeline/
│   ├── interactive-planning-doc/
│   ├── multi-agent-engineering/
│   ├── yomihime-init/
│   ├── project-memory/
│   └── ui-design/
├── README.md
└── LICENSE
```

## 📜 许可证

除另有说明外，本仓库使用 [MIT License](./LICENSE)。`skills/ui-design/` 单独使用 [Apache-2.0](./skills/ui-design/LICENSE)；其链接的第三方资源适用各自的许可。
