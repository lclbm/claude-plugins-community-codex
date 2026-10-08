# Codex 适配维护

- `main` 是完整上游镜像；`codex` 是默认分支，承载本适配。上游原始文件由 `html-plan/` 保留，正式适配写在 `codex/` 和 `scripts/build.py`。
- `plugins/html-plan-codex/` 和 `codex-upstream.lock.json` 由构建脚本生成。修改输入后，用 lock 中的源 commit 运行 `python3 scripts/build.py --upstream-sha <40 位 SHA>`，随后运行 `python3 tests/check.py`。
- 保留上游 runtime、参考文档和示例。修改 Codex 行为时更新 `codex/patches.json` 的精确替换；匹配失败先理解上游变化，再修改适配。失败不会发布新包。
- 验证覆盖插件重现、版本推进、语义漂移失败和旧包保留、runtime 字节一致、中文与上游样例打包。影响 runtime 时另做实际页面桌面和移动交互验收。
- 页面反馈沿用复制后粘贴到会话。会话自动回传、公开网页托管和用户机器上的自动升级不属于本适配。
- `artifacts/` 已忽略，用于打包页、测试输出和发布 ZIP；不存凭证和业务敏感数据。
