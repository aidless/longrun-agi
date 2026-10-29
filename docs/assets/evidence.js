window.LONGRUN_EVIDENCE = Object.freeze({
  release: "v0.1.0",
  commit: "d06edd189b8082cc72fbe9887e7f20e1b739b1df",
  tests: 190,
  portfolioChecks: "83/83",
  artifactVersions: "38/38",
  modelGate: "HOLD",
  testSplit: "sealed-not-accessed",
  packages: [
    {id: "P1", kind: "weak", zh: "验证器缺口", en: "Verifier-Gap RL", statusZh: "符号探针", statusEn: "Symbolic probe", metric: "OOD 0.5233", limitZh: "无真实 RL 训练", limitEn: "No real RL training"},
    {id: "P2", kind: "verified", zh: "故障恢复", en: "FailRecover", statusZh: "CPU 基座", statusEn: "CPU substrate", metric: "5/5 replan", limitZh: "不是生产韧性", limitEn: "Not production resilience"},
    {id: "P3", kind: "verified", zh: "可溯源记忆", en: "ProvMem", statusZh: "CPU 基座", statusEn: "CPU substrate", metric: "poison 0.0", limitZh: "无外部记忆基准", limitEn: "No external memory benchmark"},
    {id: "P4", kind: "negative", zh: "世界模型", en: "World Model", statusZh: "负结果", statusEn: "Negative result", metric: "OOD AUROC 0.5", limitZh: "仅符号环境", limitEn: "Symbolic environment only"},
    {id: "P5", kind: "verified", zh: "证据门", en: "Evidence Gate", statusZh: "CPU 基座", statusEn: "CPU substrate", metric: "FD 60→0", limitZh: "无法发现未声明混杂", limitEn: "Cannot detect undeclared confounding"},
    {id: "P6", kind: "weak", zh: "目标漂移", en: "Goal Drift", statusZh: "弱证据", statusEn: "Weak evidence", metric: "AUROC 0.8295", limitZh: "提前预警率为 0", limitEn: "Early warning rate is 0"},
    {id: "P7", kind: "verified", zh: "CLEAR 基准", en: "CLEAR-Bench", statusZh: "冻结协议", statusEn: "Frozen protocol", metric: "300 tasks", limitZh: "脚本策略不是模型行为", limitEn: "Scripted policy is not model behavior"},
    {id: "P8", kind: "weak", zh: "算力控制", en: "Compute Control", statusZh: "弱证据", statusEn: "Weak evidence", metric: "0 deadline miss", limitZh: "无真实 token 成本", limitEn: "No real token costs"}
  ],
  boundaries: {
    zh: ["没有模型级评测", "没有外部基准成绩", "没有生产级韧性结论", "没有新颖性或 AGI 进展结论"],
    en: ["No model-level evaluation", "No external benchmark result", "No production resilience claim", "No novelty or AGI progress claim"]
  }
});
