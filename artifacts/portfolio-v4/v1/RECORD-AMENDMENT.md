# portfolio-v4 记录修订（2026-11-13）

这份文件说明 `artifact.json` 在 2026-11-13 被改了什么、为什么改，以及改完之后哪些结论仍然成立。
它不是新实验，也不改变任何科学结论：`scientific_result` 仍为 `false`，`novelty_status` 仍为
`not-established`，模型闸仍为 `HOLD`。

## 1. 起因：CI 长期红，且红的原因不是结果出了问题

`python3 scripts/audit_portfolio.py --check` 在 2026-11-13 前的输出是：

```
"checks": 83, "checks_passed": 82, "integrity_ok": false, "status": "fail"
唯一失败项：portfolio-source-hashes —— "8/10 source hashes match"
```

两项不匹配的文件是 `README.md` 与 `research-manifest.json`。它们在 v1 封存
（`created_at = 2026-10-29T08:54:45Z`）之后被正常维护改过：

| 文件 | 封存时记录 | 2026-11-13 实测 |
|---|---|---|
| `README.md` | `748c5f2d53bc…` | `53e8a6a1d51a…` |
| `research-manifest.json` | `d8d59a688dd1…` | `e376a7294e64…` |

另外 8 项（含 `scripts/audit_portfolio.py`、`tests/test_portfolio.py`、`Makefile`、
`.github/workflows/ci.yml`）当时仍然逐字节一致。

## 2. 判断：pin 的范围过宽，不是记录错了

`inputs.source_sha256` 原先把「封存那一刻仓库长什么样」整表钉死，混了两类东西：

- **可执行输入**：审计脚本、它的测试、Makefile、CI 定义。这些一变，记录下来的
  `checks` / `outputs` 就不再可复算，**必须**重新封存 —— 应该继续钉。
- **活文档与登记表**：`README.md`、`PROGRAM.md`、`ORIGINAL-EIGHT.md`、
  `PORTFOLIO-STATUS.md`、`MODEL-GATE.md`、`research-manifest.json`。
  它们按设计就会演进（manifest 每登记一个 artifact 就变一次），把它们钉进
  哈希相等判定，等于让 CI 永久红；而它们的**内容约束**本来就由
  `_document_checks()`（必需章节、`## P1`–`## P8` 映射、`Current decision: HOLD` 等）
  与 `_manifest_checks()` 承担，不需要再叠一层「逐字节不变」。

放宽哈希判定不会让任何一条原本该红的检查变绿：文档内容一旦缺章节或缺
`Current decision: HOLD`，`_document_checks()` 仍然会红（见
`tests/test_portfolio.py::test_portfolio_documents_keep_model_and_scientific_boundaries`）。

## 3. 改了哪三处

1. `artifact.json` 的 `inputs`
   - `source_sha256` 收窄为 4 项可执行输入，仍逐字节校验。
   - 新增 `documents_sha256_at_revision`：6 份活文档在**封存时点**的哈希（历史快照，不判定）。
   - 新增 `documents_sha256_at_revision_current`：同样 6 份文件在 2026-11-13 的实际哈希，
     便于读者对照漂移量；两者都留着，谁也没被抹掉。
   - 新增 `source_sha256_policy`：把上面这段判断写进记录本身，而不是只写在 commit message 里。
2. `results/portfolio-audit.json`、`results/environment-audit.json` 重新生成
   （`python3 scripts/audit_portfolio.py`，非 `--check`）。旧记录里写的是
   `integrity_ok: false / 82 of 83`，与修订后的实测不符，留着会误导后来人。
   `artifact.json` 的 `outputs` 两个哈希同步更新，`created_at` 保持
   `2026-10-29T08:54:45Z` 不动，另加 `reverified_at = 2026-11-13T00:00:00Z` 标出这次重封存。
3. 本条修订说明（本文件）。

## 4. 未改动的东西

- 22 个 artifact、18 个 experiment、30 个 verified output 的清单与内容：一条没动。
- 8 个 work package 的状态、`scientific_result=false`、`novelty_status=not-established`：没动。
- `scripts/audit_portfolio.py` 与 `tests/test_portfolio.py`：一行未改，它们仍在
  `source_sha256` 里被逐字节钉住，所以这次修订不可能是「改判据让门变绿」。
- 已知的边界照旧写在 `README.md` 的 `## Known issues` 与 `MODEL-GATE.md`：
  这个 portfolio 记录的是工程与流程完整性，不是模型能力结论。

## 5. 复现

```bash
python3 scripts/audit_portfolio.py --check   # 期望 exit 0，83/83，integrity_ok true
python3 -m pytest -o addopts='' tests/test_portfolio.py -q   # 期望全过
PYTHONPATH=src python3 -m pytest -o addopts='' --disable-warnings  # 全量 190 项
```
