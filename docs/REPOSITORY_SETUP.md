# 仓库配置说明

## 本地仓库原则

本项目必须使用独立的 Git 仓库，不与旧项目的混杂开发历史共享。

推荐仓库名：

`net-workspace`

## GitHub 创建方式

### 方案 A：通过 GitHub 网页创建

1. 打开 GitHub。
2. 点击 `New repository`。
3. 仓库名填写：`net-workspace`
4. 描述建议填写：`AI-native recruitment intelligence workspace with crawler, templates, agents, and personal workspaces.`
5. 除非你明确想公开，否则建议先选 `Private`。
6. 不要在 GitHub 上额外初始化 README、`.gitignore` 或 license，因为本地已经存在。
7. 创建仓库。

### 方案 B：通过 GitHub CLI 创建

如果已经安装并登录 `gh`：

```bash
gh repo create net-workspace --private --source=. --remote=origin --push
```

## 远程仓库创建后的本地命令

在项目根目录执行：

```bash
git remote add origin https://github.com/Crescent-Starling/net-workspace.git
git branch -M main
git add .
git commit -m "chore: initialize clean project skeleton"
git push -u origin main
```

## 推荐分支策略

- `main`: stable release branch
- `develop`: integration branch
- `feature/*`: regular features
- `docs/*`: documentation work
- `agent/*`: experimental AI or workflow branches

## 提交信息规范

建议使用 Conventional Commits：

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `test:`
- `chore:`
