# Git Commit Counter

一个 Git 提交统计器，用来查看指定作者在仓库里留下的代码痕迹。📊

## ✨ 统计内容

- 提交次数
- 新增行数、删除行数、总变更行数
- 最近 30 天的每日统计
- 最近 12 周的每周统计
- 全部历史的月度、季度、年度统计

统计数据来自 `git log --numstat`。

## 🧰 环境要求

- Windows
- 已安装 Git，并且可以在命令行里执行 `git`
- PowerShell 可用

## 🚀 快速开始

把 `counter.cmd` 放到想统计的 Git 仓库里，然后双击运行。

也可以在终端中执行：

```powershell
.\counter.cmd
```

如果没有传入 `-Author`，脚本会自动读取当前仓库的 `git config user.name`，并把它当作作者名。

## 🌸 常用命令

统计当前 Git 用户在当前分支的提交：

```powershell
.\counter.cmd
```

指定作者：

```powershell
.\counter.cmd -Author "Your Name"
```

统计某个时间范围：

```powershell
.\counter.cmd -Author "Your Name" -Since "2025-01-01" -Until "2025-12-31"
```

统计指定分支：

```powershell
.\counter.cmd -Author "Your Name" -Branch "main"
```

统计所有分支：

```powershell
.\counter.cmd -Author "Your Name" -AllBranches
```

## 📝 参数

| 参数 | 说明 |
| :--- | :--- |
| `-Author` | 要统计的 Git 作者名。不填时使用 `git config user.name`。 |
| `-Since` | 起始时间，传给 `git log --since`，比如 `2025-01-01`。 |
| `-Until` | 结束时间，传给 `git log --until`，比如 `2025-12-31`。 |
| `-Branch` | 只统计指定分支。 |
| `-AllBranches` | 统计所有分支，优先级高于 `-Branch`。 |

## 📦 输出

- 仓库名、分支、作者、时间范围
- 总提交数，以及最早/最晚提交日期
- Daily / Weekly / Monthly / Quarterly / Yearly 统计表
- 每个周期里的提交数、新增行数、删除行数、总变更行数
