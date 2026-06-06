# 贡献说明

感谢你为 NetWorkspace 做贡献。

## 基本原则

1. 主系统保持稳定，个人实验不要直接污染核心结构。
2. 产品文档、设计说明、需求讨论默认使用中文。
3. 标识符、目录名、API 路径、数据库字段等技术标识保留英文。
4. 所有重要变更都应可追溯、可解释、可回滚。

## 开发流程

1. 从 `develop` 或 `main` 拉取最新代码。
2. 创建功能分支：
   - `feature/*`
   - `docs/*`
   - `agent/*`
3. 完成开发与自测。
4. 提交 Pull Request。

## 提交信息规范

建议使用 Conventional Commits：

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `test:`
- `chore:`

示例：

```text
feat: add intelligent site onboarding draft schema
docs: refine NetWorkspace PRD in Chinese
```

## Pull Request 要求

每个 PR 至少说明：

1. 改动目标
2. 改动范围
3. 风险点
4. 测试情况
5. 是否涉及数据库、模板、API 或 Agent 行为变化

## 不建议直接提交的内容

- 本地临时脚本
- 含个人隐私的路径或环境信息
- 未经确认的密钥、账号、token
- 与当前目标无关的大量历史材料
