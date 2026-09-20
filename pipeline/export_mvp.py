"""Export audited experiment previews. No literature scores, raw EEG or weights."""
from __future__ import annotations
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from mvp_english import english_payload

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def read(path): return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+"\n")


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def family(name):
    if name in ("CSP+LDA", "CSP＋LDA"): return "classical"
    if name in ("EEGNet", "ShallowFBCSPNet", "Deep4Net"): return "small"
    return "foundation"


def main():
    idle = ROOT / "experiments/idle_replay_v1"
    run = idle / "outputs/run-20260910-mps-v1"
    a = read(run / "independent-audit.json")
    assert a["passed"] and not a["errors"]
    summary = read(run / "summary.json")
    registry = read(idle / "model_assets/candidate-registry.json")
    parameters = {m["name"]: m["parameters"] for m in registry["models"]}
    rows = []
    for r in summary["aggregate"]:
        name = r["model"]
        rows.append(dict(id=name.lower().replace("+", "-"), name=name,
            family=family(name), parameters=parameters.get(name), channels=17,
            mode="冻结编码器 + 线性头" if family(name)=="foundation" else "从头训练 20 轮" if family(name)=="small" else "监督训练",
            x=100*r["idle_false_trigger_trials"]/r["idle_trials"],
            y=100*r["mi_detected_trials"]/r["mi_trials"],
            xDetail=f'{r["idle_false_trigger_trials"]} / {r["idle_trials"]} 个闲置试次',
            yDetail=f'{r["mi_detected_trials"]} / {r["mi_trials"]} 个指令试次',
            abstain=r["degenerate_all_reject_subjects"], seconds=r["fit_and_predict_seconds"],
            subjects=4, note="按固定校准规则选阈值；每人 60 个训练试次、30 个校准试次。",
            subjectResults=[dict(subject=f["subject"],recall=f["mi_detection_fraction"]*100,
                falseRate=f["idle_false_trigger_fraction"]*100,threshold=f["threshold"],
                abstain=f["degenerate_all_reject"]) for f in summary["results"] if f["model"]==name]))
    tracks = [dict(id="idle", title="闲置与指令", short="误触发 × 检出", dataset="ds005342",
        subtitle="坐姿运动想象 · 提示试次内回放", type="tradeoff", subjects=4,
        observations="60 个闲置 / 60 个指令试次", exposure="180 秒测试闲置",
        status="研究预览", xLabel="闲置误触发率", yLabel="3 秒内指令检出率",
        limitation="每个提示试次重新开始检测；仅 3 分钟测试闲置，不能外推为自然环境每小时误触发率。",
        protocol=["同一受试者前两段训练，第三段只选阈值，最后一段留作测试。",
                  "任务零点使用类别事件 1/2；2 秒历史窗口，在 2.0、2.5、3.0 秒决策。",
                  "连续两次越过阈值才触发；阈值仅在校准集选择，允许全拒识。",
                  "17 导、250 Hz 原始数据，单向 4–40 Hz 滤波；没有未来样本或测试集归一化。",
                  "原实验反馈、视觉提示和短校准数据均可能影响结果；不是自然连续闲置测试。"],
        protocolId="ds005342-sitting-cue-gated-pilot-v1", version="1.0.3",
        elapsed=summary["elapsed_seconds"], peakGb=summary["process_peak_rss_bytes"]/1e9,
        auditSha=sha(run/"independent-audit.json"), source="https://openneuro.org/datasets/ds005342/versions/1.0.3", rows=rows)]
    bnci = ROOT / "experiments/bnci_mi_v1/outputs/run-20260909-mps-v1"
    verification = read(bnci / "verification.json")
    assert verification["status"] == "verified_experimental_run"
    b=read(bnci/"summary.json")
    brows=[]
    for r in b["models"]:
        name="LaBraM" if r["model"]=="labram-base" else r["model_name"]
        brows.append(dict(id=r["model"], name=name, family=family(name),parameters=parameters.get(name),channels=22,
            mode="冻结编码器 + 线性头" if family(name)=="foundation" else "监督训练",
            x=r["mean_subject_cohen_kappa"],y=100*r["mean_subject_balanced_accuracy"],
            xDetail="Cohen’s κ", yDetail="9 人均值", abstain=None,
            seconds=r["total_model_seconds"],subjects=9,
            interval=[100*v for v in r["descriptive_subject_bootstrap_95_interval"]],
            note="四分类机会水平 25%；同一个人的两个 session 始终同组。LaBraM 使用 200 维全局池化，与闲置轨道不同。",subjectResults=[]))
    tracks.append(dict(id="transfer",title="跨人运动想象",short="跨受试者迁移",dataset="BNCI2014-001",
        subtitle="四分类运动想象 · 留一受试者",type="accuracy",subjects=9,observations="5,184 个试次 / 9 折",
        exposure="22 导 · 4 秒窗口",status="研究预览",xLabel="Cohen’s κ",yLabel="Balanced accuracy",
        limitation="单一数据集、固定配置的跨人实验。区间为按受试者重采样的描述性 95% 区间，不代表多任务通用能力。",
        protocol=["每折 8 人训练、1 人测试，覆盖 9 名受试者；同一人的两个 session 不跨组。",
                  "保留全部试次及伪迹标记；22 个 EEG 通道，4 秒窗口，离线 4–40 Hz 零相位滤波。",
                  "基础模型冻结、训练集内标准化与线性分类器；传统方法仅在训练折拟合。",
                  "这是一项离线迁移实验，不能与因果闲置回放拼接成综合分。"],
        protocolId=b["protocol_id"],version="BNCI 官方 MAT 快照 / 2026-09-09", elapsed=b["total_wall_seconds"],
        peakGb=b["process_peak_rss_bytes_cumulative_macos"]/1e9, auditSha=sha(bnci/"audit-report.json"),
        source="https://bnci-horizon-2020.eu/database/data-sets",rows=brows))
    model_rows=[]
    for m in registry["models"]:
        e=m["evidence"]
        url=e.get("source_url") or e.get("source_repository")
        if not url: url={"LaBraM":"https://github.com/935963004/LaBraM","EEGPT":"https://github.com/BINE022/EEGPT","CSP+LDA":"https://mne.tools/stable/generated/mne.decoding.CSP.html"}.get(m["name"])
        scored=any(m["name"]==r["name"] for t in tracks for r in t["rows"])
        state="已评分" if scored else "通道待适配" if m["current_dataset_status"]=="adapter_required" else "权重待授权" if m["current_dataset_status"]=="blocked" else "运行检查通过"
        note="固定配置已进入本站研究预览。" if scored else "已加载并完成前向检查，尚无本站任务成绩。"
        if m["name"]=="BIOT":note="预训练双极导联与当前单极脑电不直接对应；适配配置单独评测。"
        if m["name"]=="REVE Base":note="源码与位置表可访问；本体权重需要在官方页面接受访问协议。"
        model_rows.append(dict(name=m["name"],family=family(m["name"]),parameters=m["parameters"],status=state,
            note=note,url=url,license=e.get("source_license") or e.get("license") or {"LaBraM":"MIT","EEGPT":"Apache-2.0","CSP+LDA":"BSD"}.get(m["name"],"见来源")))
    datasets=[dict(name="ds005342",task="闲置 / 运动想象",subjects=32,channels=17,size="2.03 GiB",status="已下载 · 全量读取通过",
        detail="本轮评分 4 人；其余文件已准备。sub-022 事件缺失，固定划分评分需排除或另行核查。",source="https://openneuro.org/datasets/ds005342/versions/1.0.3",license="CC0",evaluated=True),
        dict(name="BNCI2014-001",task="四分类运动想象",subjects=9,channels=22,size="744 MiB",status="已下载 · 已评测",
        detail="18 个 MAT，9 人、5,184 个试次；9 折留一受试者测试。",source="https://bnci-horizon-2020.eu/database/data-sets",license="CC BY-ND 4.0",evaluated=True)]
    # Optional reviewed additions are appended only once their independent audits exist.
    additions=ROOT/"experiments/expanded_mvp_v1/mvp-reviewed-export.json"
    if additions.exists():
        extra=read(additions); assert extra["auditPassed"] is True
        tracks[0]["rows"].extend(extra.get("idleRows",[]))
        if "idleExtension" in extra:
            ext=extra["idleExtension"]
            tracks[0]["elapsed"]+=ext["elapsed"]
            tracks[0]["peakGb"]=max(tracks[0]["peakGb"],ext["peakGb"])
            tracks[0]["extensionProtocol"]=ext
        tracks.extend(extra.get("tracks",[]));datasets.extend(extra.get("datasets",[]))
        for m in model_rows:
            if any(m["name"]==r["name"] for t in tracks for r in t["rows"]):m["status"]="已评分";m["note"]="固定配置已进入本站研究预览；请查看输入通道与训练方式。"
    news_path=ROOT/"research/MVP新闻与候选扩展.json"
    news=[]
    if news_path.exists():
        n=read(news_path)
        for item in n.get("news",[]):
            if item.get("reviewed") is True:news.append(item)
    payload=dict(generatedAt=datetime.now(timezone.utc).isoformat(),tracks=tracks,models=model_rows,datasets=datasets,news=news,
                 evidencePolicy="仅展示本站已执行、完成程序复核的研究预览。不计算跨任务综合分；未审核论文数字不进入结果表。")
    payload=english_payload(payload,ROOT)
    write(SITE/"src/data/mvp.json",payload)
    write(SITE/"public/data/experiments.json",payload)
    for t in tracks:
        stream=io.StringIO();writer=csv.writer(stream)
        writer.writerow(["protocol_id","dataset","model","training_mode","channels","subjects",t["yLabel"],t["xLabel"],"computation_seconds","status"])
        for r in t["rows"]:writer.writerow([t["protocolId"],t["dataset"],r["name"],r["mode"],r["channels"],r["subjects"],r["y"],r["x"],r["seconds"],"research_preview"])
        (SITE/"public/data"/f'{t["id"]}-results.csv').write_text("\ufeff"+stream.getvalue())
        write(SITE/"public/data"/f'{t["id"]}-protocol.json',{k:v for k,v in t.items() if k!="rows"})
    print(json.dumps({"tracks":len(tracks),"configurations":sum(len(t["rows"]) for t in tracks),"models":len(model_rows),"news":len(news)}))


if __name__=="__main__":main()
