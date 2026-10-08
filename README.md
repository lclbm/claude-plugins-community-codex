# HTML Plan for Codex

基于 [Thariq Shihipar 的 html-plan](https://github.com/anthropics/claude-plugins-community/tree/main/html-plan)，把复杂方案做成一个离线可用、可逐层展开、可选择和批注的 HTML 页面。

Codex 适配默认使用简体中文，尊重用户已选择的设计或实施模式，只询问会改变方向、成本或风险的未决事项。结论关联原始出处与版本，区分提案、已实现和已验证。运行时内置按钮仍保留上游英文。

## 安装

需要 Codex 的 plugin CLI，以及用于打包 HTML 的 Node.js。

```sh
codex plugin marketplace add lclbm/claude-plugins-community-codex --ref codex
codex plugin add html-plan-codex@lclbm-visual-tools
```

在新会话中使用 `$html-plan-codex`。例如：

> $html-plan-codex 把这个跨系统方案做成中文交互页，关联代码和证据。继续完成已授权实施，不增加审批环节。

该技能名与已有的 standalone `$html-plan` 不同，两者可以分别选择。

在页面中展开结论、选择选项、评论或编辑 schema，点击 **Respond → Copy response**，把汇总粘贴到当前 Codex 会话。页面不会自动提交消息，也不会替用户执行仓库、订单或发布动作。

已安装的客户端获取新版：

```sh
codex plugin marketplace upgrade lclbm-visual-tools
codex plugin add html-plan-codex@lclbm-visual-tools
```

仓库自动更新与本机插件刷新是两个动作。本仓库不修改用户机器上的更新设置。安装与市场格式依据 [OpenAI 官方插件文档](https://developers.openai.com/plugins/build/plugins)。

## 上游更新

- `main`：原始完整仓库，用 GitHub 的 fork 同步 API 追随上游 `main`。
- `codex`：默认分支，只引入 `html-plan/` 和原始 `LICENSE`，附加 Codex 指令、包、测试和发布流程。
- GitHub Actions 每天北京时间 **05:37** 检查，也可手动运行 **Codex package**。计划运行可能延迟，不能把时刻当作更新 SLA。
- 内容或适配发生变化后，插件的独立版本 `0.1.x` 自动递增，验证通过才提交、打 tag 并发布包含 ZIP 与 SHA-256 的 GitHub Release。上游 `1.0.0` 只作来源元信息；上游未改版本但源码变化也会触发新版。无关的上游提交不会增加插件版本。
- 精确替换无法匹配、源文件缺失或检查失败时，Actions 报错，`codex` 保留上一版；完整 `main` 镜像可能已成功更新。维护者检查失败日志、修改适配，再手动重跑。每次先完成当前已验证版本的发布，再接受下一次上游更新；发布中断可以复用原 tag 和 draft 接续，不创建重复版本。
- fork 的 `main` 不存本地修改；不使用 force push。只在默认 `codex` 分支运行本发布流程，上游社区市场的维护 workflows 不导入此分支。

本流程只需仓库的 `GITHUB_TOKEN` 和 `contents: write`，不需要保存个人 token。来源 commit、原版版本和构建指纹在 `codex-upstream.lock.json` 中。遇到问题可以安装指定历史 tag，或下载对应 Release；回滚不改写历史。

## 本地维护与验证

```sh
python3 scripts/build.py --upstream-sha <codex-upstream.lock.json 中的 commit>
python3 tests/check.py
codex plugin list --marketplace lclbm-visual-tools --available --json
```

测试覆盖：生成内容重现、不重复升版、源码变化升版、上游指令漂移停止、失败保留旧包、运行时完全一致，以及中文与上游样例打包。产物在已忽略的 `artifacts/`。中文版检查页源文件是 `tests/smoke.html`。

此包只包含技能和原有 runtime，不增加服务、后台进程、MCP 或网页托管。桌面客户端的技能加载与完整实际项目流程仍需在安装后的新会话中验收；打包通过不能替代这项验证。

## 来源与许可证

原始 html-plan 作者是 **Thariq Shihipar**；Codex 指令调整与发布包装由 **lclbm** 维护。本项目是个人适配，并非 Anthropic 或 OpenAI 官方产品。

原始 runtime、references 和 examples 保持字节一致。仓库根部的 Apache-2.0 `LICENSE` 原样保留，包内也保留该文件、`NOTICE`、上游 README 及声明 MIT 的原版 plugin 元信息。两个来源声明均保留，不据此重写上游授权。
