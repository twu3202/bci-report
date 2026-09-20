"""Legacy literature scoring experiment; retained for provenance, not export.

The trusted pipeline does not call this module's ``compute`` function. Default
leaderboard output is built by ``leaderboard.build_verified_leaderboard`` from
strictly comparable first-party runs.

思路（与 LMArena 的数学同源，但"投票者"换成客观基准任务）：
  * 每个基准任务 t 取其 primary_metric；凡在 t 上有可用分数的模型两两配对，
    分数高者记一场胜利（差值落在两者标准差合成的容差内记为平局，各得 0.5）。
  * 把所有任务上的对决汇总，用 Bradley–Terry 模型（MM 算法，Hunter 2004）拟合模型强度，
    带一个很小的对称先验（每对已对决的模型之间各加 PRIOR 场平局）避免完全分离时发散。
  * 评分标尺沿用 Elo 习惯：rating = 1000 + 400·log10(strength)，并把均值平移到 1000。
  * 置信区间：对"任务"做自举（有放回重抽任务集合）N_BOOT 次，取 2.5/97.5 百分位。
    以任务为重抽单位，因为一个任务上的所有配对不是独立证据。
  * 次指标 mean_norm：每个任务内 min–max 归一化后的分数在该模型所有任务上取均值。

一个模型在某任务上的"可用分数"按证据等级挑选：
  verified（本站实测） > reproduced（第三方复现） > reported/same_paper（原论文自报）
  > reported/reproduced_by_source_paper（他人论文重跑） > reported/cited（转引）。
同一等级有多条时取均值。全部候选都会原样保留在导出数据里供页面展示。
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field

TIER_RANK = {"verified": 0, "reproduced": 1, "reported": 2}
RUNBY_RANK = {"same_paper": 0, "reproduced_by_source_paper": 1, "cited_from_original": 2, "": 3}
PRIOR = 0.05          # 每对模型之间的先验平局数（对称，不改变均衡点）
N_BOOT = 1000
SCALE, BASE, INIT = 400.0, 10.0, 1000.0


@dataclass
class Result:
    model: str
    benchmark: str
    metric: str
    value: float
    std: float | None
    tier: str
    run_by: str
    source_title: str = ""
    source_url: str = ""
    table_ref: str = ""
    notes: str = ""


@dataclass
class TaskScores:
    """一个任务上每个模型的"代表分"及其来源等级。"""
    benchmark: str
    metric: str
    higher_is_better: bool
    scores: dict[str, float] = field(default_factory=dict)
    stds: dict[str, float] = field(default_factory=dict)
    tiers: dict[str, str] = field(default_factory=dict)


def pick_canonical(results: list[Result], benchmarks: dict[str, dict]) -> list[TaskScores]:
    """每个 (benchmark) 上按 primary_metric 为每个模型挑一条代表分。"""
    by_task: dict[str, list[Result]] = defaultdict(list)
    for r in results:
        b = benchmarks.get(r.benchmark)
        if not b or r.metric != b["primary_metric"]:
            continue
        by_task[r.benchmark].append(r)

    out = []
    for slug, rows in by_task.items():
        b = benchmarks[slug]
        ts = TaskScores(slug, b["primary_metric"], bool(b.get("higher_is_better", True)))
        per_model: dict[str, list[Result]] = defaultdict(list)
        for r in rows:
            per_model[r.model].append(r)
        for m, rs in per_model.items():
            rs.sort(key=lambda r: (TIER_RANK.get(r.tier, 9), RUNBY_RANK.get(r.run_by, 3)))
            best_key = (TIER_RANK.get(rs[0].tier, 9), RUNBY_RANK.get(rs[0].run_by, 3))
            top = [r for r in rs if (TIER_RANK.get(r.tier, 9), RUNBY_RANK.get(r.run_by, 3)) == best_key]
            ts.scores[m] = sum(r.value for r in top) / len(top)
            stds = [r.std for r in top if r.std is not None]
            ts.stds[m] = (sum(stds) / len(stds)) if stds else 0.0
            ts.tiers[m] = rs[0].tier
        if len(ts.scores) >= 2:
            out.append(ts)
    return out


def pairwise(tasks: list[TaskScores]) -> dict[tuple[str, str], float]:
    """返回 wins[(i, j)] = i 战胜 j 的场数（平局各记 0.5）。"""
    wins: dict[tuple[str, str], float] = defaultdict(float)
    for t in tasks:
        models = sorted(t.scores)
        for a in range(len(models)):
            for b in range(a + 1, len(models)):
                i, j = models[a], models[b]
                si, sj = t.scores[i], t.scores[j]
                if not t.higher_is_better:
                    si, sj = -si, -sj
                tol = math.hypot(t.stds.get(i, 0.0), t.stds.get(j, 0.0))
                if abs(si - sj) <= tol:
                    wins[(i, j)] += 0.5
                    wins[(j, i)] += 0.5
                elif si > sj:
                    wins[(i, j)] += 1.0
                else:
                    wins[(j, i)] += 1.0
    return wins


def bradley_terry(wins: dict[tuple[str, str], float], models: list[str],
                  iters: int = 500, tol: float = 1e-9) -> dict[str, float]:
    """Hunter (2004) MM 算法；返回 Elo 标尺评分，均值平移到 INIT。"""
    if not models:
        return {}
    w = defaultdict(float)
    for (i, j), v in wins.items():
        w[(i, j)] += v
    # 对称先验：每对有过对决的模型各加 PRIOR 场平局
    pairs = {tuple(sorted(k)) for k in wins}
    for i, j in pairs:
        w[(i, j)] += PRIOR
        w[(j, i)] += PRIOR
    total_w = {m: sum(v for (i, _), v in w.items() if i == m) for m in models}
    p = {m: 1.0 for m in models}
    for _ in range(iters):
        new = {}
        for i in models:
            denom = 0.0
            for j in models:
                if i == j:
                    continue
                n_ij = w.get((i, j), 0.0) + w.get((j, i), 0.0)
                if n_ij:
                    denom += n_ij / (p[i] + p[j])
            new[i] = total_w[i] / denom if denom else p[i]
        # 几何均值归一，防止漂移
        g = math.exp(sum(math.log(max(v, 1e-12)) for v in new.values()) / len(new))
        new = {m: v / g for m, v in new.items()}
        delta = max(abs(new[m] - p[m]) for m in models)
        p = new
        if delta < tol:
            break
    ratings = {m: INIT + SCALE * math.log(max(p[m], 1e-12), BASE) for m in models}
    mean = sum(ratings.values()) / len(ratings)
    return {m: r - mean + INIT for m, r in ratings.items()}


def bootstrap_ci(tasks: list[TaskScores], models: list[str], n_boot: int = N_BOOT,
                 seed: int = 20260906) -> dict[str, tuple[float, float]]:
    rng = random.Random(seed)
    samples: dict[str, list[float]] = defaultdict(list)
    for _ in range(n_boot):
        draw = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        wins = pairwise(draw)
        present = sorted({m for t in draw for m in t.scores})
        r = bradley_terry(wins, present, iters=200)
        for m in present:
            samples[m].append(r[m])
    ci = {}
    for m in models:
        s = sorted(samples.get(m, []))
        if len(s) < 20:
            ci[m] = (float("nan"), float("nan"))
            continue
        lo = s[int(0.025 * (len(s) - 1))]
        hi = s[int(0.975 * (len(s) - 1))]
        ci[m] = (lo, hi)
    return ci


def mean_normalized(tasks: list[TaskScores]) -> dict[str, float]:
    acc: dict[str, list[float]] = defaultdict(list)
    for t in tasks:
        vals = list(t.scores.values())
        lo, hi = min(vals), max(vals)
        for m, v in t.scores.items():
            x = (v - lo) / (hi - lo) if hi > lo else 0.5
            if not t.higher_is_better:
                x = 1 - x
            acc[m].append(x)
    return {m: sum(v) / len(v) for m, v in acc.items()}


def compute(results: list[Result], benchmarks: dict[str, dict],
            families: dict[str, str] | None = None, with_ci: bool = True) -> dict:
    """主入口。families: benchmark_slug → task_family，用于分任务族子评分。"""
    tasks = pick_canonical(results, benchmarks)
    models = sorted({m for t in tasks for m in t.scores})
    wins = pairwise(tasks)
    rating = bradley_terry(wins, models)
    ci = bootstrap_ci(tasks, models) if with_ci and len(tasks) >= 2 else {m: (float("nan"),) * 2 for m in models}
    mnorm = mean_normalized(tasks)
    n_tasks = {m: sum(1 for t in tasks if m in t.scores) for m in models}
    best_tier = {}
    for t in tasks:
        for m, tier in t.tiers.items():
            if m not in best_tier or TIER_RANK[tier] < TIER_RANK[best_tier[m]]:
                best_tier[m] = tier

    fam_rating: dict[str, dict[str, float]] = defaultdict(dict)
    if families:
        by_fam: dict[str, list[TaskScores]] = defaultdict(list)
        for t in tasks:
            by_fam[families.get(t.benchmark, "other")].append(t)
        for fam, ts in by_fam.items():
            ms = sorted({m for t in ts for m in t.scores})
            if len(ms) >= 2:
                for m, r in bradley_terry(pairwise(ts), ms).items():
                    fam_rating[m][fam] = r

    # 头对头胜率矩阵（供页面展示）
    h2h = {}
    for (i, j), v in wins.items():
        n = v + wins.get((j, i), 0.0)
        h2h.setdefault(i, {})[j] = {"wins": round(v, 1), "n": round(n, 1)}

    rows = []
    for m in models:
        lo, hi = ci[m]
        rows.append({
            "slug": m,
            "rating": round(rating[m], 1),
            "ci_low": None if math.isnan(lo) else round(lo, 1),
            "ci_high": None if math.isnan(hi) else round(hi, 1),
            "mean_norm": round(mnorm[m], 4),
            "n_tasks": n_tasks[m],
            "best_tier": best_tier.get(m, "reported"),
            "provisional": n_tasks[m] < 2,
            "family_ratings": {k: round(v, 1) for k, v in fam_rating.get(m, {}).items()},
        })
    rows.sort(key=lambda r: -r["rating"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return {
        "models": rows,
        "tasks": [{"benchmark": t.benchmark, "metric": t.metric, "n_models": len(t.scores)} for t in tasks],
        "h2h": h2h,
        "params": {"prior": PRIOR, "n_boot": N_BOOT, "scale": SCALE, "init": INIT},
    }
