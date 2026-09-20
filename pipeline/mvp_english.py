"""English public-facing copy; numeric experiment data remains unchanged."""
import re
import json

def english_payload(payload, root):
    tracks=payload["tracks"]
    idle=tracks[0]
    idle.update(title="Idle & command",short="False activation × detection",subtitle="Seated motor imagery · cue-gated replay",
        observations="60 idle / 60 command test trials",exposure="180 seconds of test idle",status="Research preview",
        xLabel="Idle false activation",yLabel="Command detection ≤3s",
        limitation="Detection resets at each cue. Only three minutes of test idle are observed; these results cannot estimate natural, always-on false activations per hour.",
        protocol=["For each subject, the first two blocks train the model, the third selects the threshold, and the final block is held out for testing.",
        "Class events 1/2 define task onset. Two-second history windows produce decisions at 2.0, 2.5 and 3.0 seconds.",
        "Two consecutive threshold crossings trigger one command. Thresholds use calibration data only and may reject every command.",
        "17 channels at 250 Hz; one-way 4–40 Hz filtering. Normalization uses training data only; no future samples enter a decision window.",
        "Visual cues, original feedback and short calibration exposure can influence results. This is not a natural continuous-idle test."])
    for t in tracks:
        for r in t["rows"]:
            r["mode"]={"冻结编码器 + 线性头":"Frozen encoder + linear head","从头训练 20 轮":"Scratch · 20 epochs","监督训练":"Supervised fit"}.get(r["mode"],r["mode"])
    for r in idle["rows"]:
        r["xDetail"]=r["xDetail"].replace(" 个闲置试次"," idle trials")
        r["yDetail"]=r["yDetail"].replace(" 个指令试次"," command trials")
        if re.search(r"[\u4e00-\u9fff]",r["note"]):
            r["note"]="Fixed calibration rule; 60 training trials and 30 calibration trials per subject. Test subjects are sub-001 through sub-004."
    transfer=tracks[1]
    transfer.update(title="Cross-subject MI",short="Transfer to a new person",subtitle="Four-class motor imagery · leave one subject out",
        observations="5,184 trials / 9 folds",exposure="22 channels · 4-second windows",status="Research preview",
        xLabel="Cohen’s κ",yLabel="Balanced accuracy",version="Official BNCI MAT snapshot / 2026-09-09",
        limitation="A fixed configuration on one dataset. Intervals are descriptive 95% subject-bootstrap intervals, not evidence of general multi-task capability.",
        protocol=["Train on eight subjects and test on the ninth, across all nine folds. Both sessions of one person stay in the same group.",
        "All trials, including artifact-marked trials, are retained. Use 22 EEG channels, four-second windows and offline 4–40 Hz zero-phase filtering.",
        "Foundation encoders are frozen; scaling and the linear classifier are fitted on training subjects only. Classical methods use the same training split.",
        "Four classes imply 25% chance accuracy. This offline transfer experiment is not pooled into a universal score with causal idle replay."])
    for r in transfer["rows"]:
        r["yDetail"]="Mean over 9 subjects"
        r["note"]="Four-class chance level: 25%. Both sessions of a person remain together. LaBraM uses 200-dimensional global pooling here, unlike the idle track."
    for m in payload["models"]:
        m["status"]={"已评分":"Evaluated","通道待适配":"Adapter needed","权重待授权":"Access gated","运行检查通过":"Forward pass checked"}.get(m["status"],m["status"])
        m["note"]="A fixed configuration has been evaluated. See each task for channels and training mode." if m["status"]=="Evaluated" else "Loaded successfully and passed a forward check. No task score is shown yet."
        if m["name"]=="BIOT":m["note"]="Pretrained bipolar tokens do not directly match the unipolar recordings. A separately validated adapter is required."
        if m["name"]=="REVE Base":m["note"]="Code and electrode positions are accessible. Base weights require accepting the official access agreement; they have not been downloaded."
        m["license"]=str(m["license"]).replace("见来源","See source").replace("代码","Code").replace("权重","weights")
    payload["datasets"][0].update(task="Idle / motor imagery",status="Downloaded · all files parsed",
        detail="32 subjects prepared; four evaluated. Subject 022 has missing events and needs separate review before applying this fixed split.")
    payload["datasets"][1].update(task="Four-class motor imagery",status="Downloaded · evaluated",
        detail="18 MAT files, nine subjects and 5,184 trials. Evaluated with nine leave-one-subject-out folds.")
    extras=root/"research/mvp-english-resources.json"
    if extras.exists():
        resources=json.loads(extras.read_text())
        existing={m["name"] for m in payload["models"]}
        for m in resources["models"]:
            if m["name"] in existing:continue
            m["family"]="foundation" if "foundation" in m["family"] else "small"
            m["note"]=m["status"]+" "+m["note"]
            m["status"]="Access unverified" if m["name"]=="CSBrain" else "Research candidate"
            payload["models"].append(m)
        names={d["name"] for d in payload["datasets"]}
        payload["datasets"].extend(d for d in resources["datasets"] if d["name"] not in names)
        payload["news"]=[n for n in resources["news"] if n.get("reviewed") is True]
    else:
        payload["news"]=[]
    payload["evidencePolicy"]="Only locally executed experiments with completed programmatic review appear in results. There is no cross-task overall score; unreviewed literature numbers never enter these tables."
    def check(v):
        if isinstance(v,str):assert not re.search(r"[\u4e00-\u9fff]",v),v
        elif isinstance(v,dict):
            for a in v.values():check(a)
        elif isinstance(v,list):
            for a in v:check(a)
    check(payload)
    return payload
