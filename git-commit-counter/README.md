# Git Commit Counter

一只小小的 Git 提交统计器 📊

用来看看如月小姐，或者任何指定作者，在一个 Git 仓库里留下了多少代码痕迹。

---

## ✨ 它会统计什么？

- 提交次数
- 新增行数、删除行数、总变更行数
- 最近 30 天的每日统计
- 最近 12 周的每周统计
- 全部历史的月度、季度、年度统计

统计数据来自 `git log --numstat`，适合用来粗略回顾自己的摸鱼成果和爆肝痕迹。

---

## 🧰 环境要求

- Windows
- 已安装 Git，并且可以在命令行里执行 `git`
- PowerShell 可用

---

## 🚀 快速开始

把 `counter.cmd` 放到想统计的 Git 仓库里，然后双击运行。

也可以在终端中执行：

```powershell
.\counter.cmd
```

如果没有传入 `-Author`，脚本会自动读取当前仓库的 `git config user.name`，拿它当作作者名。

---

## 🌸 常用姿势

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

---

## 📝 参数说明

| 参数 | 说明 |
| :--- | :--- |
| `-Author` | 要统计的 Git 作者名。不填时使用 `git config user.name`。 |
| `-Since` | 起始时间，传给 `git log --since`，比如 `2025-01-01`。 |
| `-Until` | 结束时间，传给 `git log --until`，比如 `2025-12-31`。 |
| `-Branch` | 只统计指定分支。 |
| `-AllBranches` | 统计所有分支。优先级高于 `-Branch`。 |

---

## 📦 输出内容

运行后会在终端里看到：

- 仓库名、分支、作者、时间范围
- 总提交数，以及最早/最晚提交日期
- Daily / Weekly / Monthly / Quarterly / Yearly 统计表
- 每个周期里的提交数、新增行数、删除行数、总变更行数

---

> 💡 **小提醒**：
> - 这个工具统计的是 Git 历史里的行数变化，适合拿来回顾，不适合当作精确工作量证明。
> - 二进制文件不会像普通文本文件一样产生新增/删除行数。
> - `counter.cmd` 会先切换到自己所在的目录再运行，所以建议把它放进要统计的仓库目录里。
> - `-Author` 要和提交历史中的作者名匹配，不然可能会找不到对应提交。
