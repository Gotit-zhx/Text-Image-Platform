# 项目文档

项目介绍与桌面端截图见[项目首页](../README.md)。本目录保留使用者和维护者需要的公开文档，开发过程记录留在本地。

## 阅读顺序

| 文档 | 内容 |
| --- | --- |
| [快速开始](QUICK_START.md) | 安装依赖、启动服务和体验演示内容 |
| [开发与运行说明](DEVELOPMENT_GUIDE.md) | 环境变量、启动脚本、推荐训练与 CI |
| [项目概览](PROJECT_OVERVIEW.md) | 功能范围、技术架构和主要模块 |
| [详细项目说明](PROJECT_DETAILS.md) | 业务模块、数据模型及项目组织 |
| [API 契约](API_CONTRACT.md) | 接口、认证、权限、错误响应和状态规则 |
| [UI 规范](UI_SPEC.md) | 设计变量、页面布局、组件与交互约定 |
| [演示图片来源与许可](demo-media-sources.md) | 展示图片的原始来源和使用许可 |

## 目录约定

| 路径 | 用途 | 是否提交 |
| --- | --- | --- |
| `docs/*.md` | 面向使用者的指南和维护规范 | 是，过程文档除外 |
| `docs/assets/readme/` | README 中的桌面端项目截图 | 是 |
| `docs/local/` | 开发提示词、TODO、调试笔记、实施报告和验收记录 | 否 |
| `demo_assets/` | 本地展示内容使用的公开许可图片 | 是 |
| `frontend_vue/e2e/`、后端 `tests*.py` | 可重放的自动化检查源码 | 是 |
| `.run_logs/`、`test-results/`、`playwright-report/`、`coverage/` | 运行日志、测试输出和临时截图 | 否 |

新增开发过程文档统一放在 `docs/local/`，该目录可按需在本地创建，不随 Git 克隆提供。原有的 AI 开发提示词、业务 TODO、验收场景、人工验收、实施报告和就绪度审查文档仍在 `.gitignore` 中逐项排除，以兼容本地已有路径。`docs/` 下以 `_TODO.md`、`_PROMPTS.md`、`_AUDIT.md`、`_ACCEPTANCE.md` 或 `_REPORT.md` 结尾的过程文档也会被忽略。

API 契约和 UI 规范属于长期维护资料，应继续随代码更新；内部验收记录不作为公开文档的阅读依赖。界面截图保留桌面端，临时调试截图放入被忽略的运行目录。

## 提交前检查

在项目根目录执行：

```bash
git status --short
git diff --check
git diff --cached --stat
```

检查某个本地文件的忽略规则：

```bash
git check-ignore -v docs/local/notes.md
```

`.gitignore` 不会自动取消对已跟踪文件的管理。如发现已跟踪的本地过程文档，使用 `git rm --cached -- <文件路径>` 将其从索引移除并保留本地文件。不要使用 `git add -f` 将过程文档、数据库、环境密钥或用户上传内容加入提交。
