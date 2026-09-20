"""Create an explicit website bridge only from independently reviewed local runs."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def approved(p):
    a=read(p/'independent-audit.json')
    assert a['passed'] and not a['errors'], 'Independent audit must pass'

def main():
    p=ROOT/'experiments/expanded_mvp_v1/outputs/run-20260910-mps-v1'
    approved(p);s=read(p/'summary.json')
    extra=dict(auditPassed=True,idleRows=[],tracks=[],datasets=[],idleExtension=dict(
        elapsed=s['elapsed_seconds'],peakGb=s['process_peak_rss_bytes']/1e9,
        protocolId='ds005342-sitting-cue-gated-expanded-mvp-v1',auditSha=sha(p/'independent-audit.json')))
    for r in s['aggregate']:
        fs=[f for f in s['results'] if f['model']==r['model']]
        fm=r['model']=='CBraMod'
        seconds=sum(sum(f['model_metadata'].get(k,0) for k in (['feature_extraction_seconds','head_fit_predict_seconds'] if fm else ['training_seconds','inference_seconds'])) for f in fs)
        extra['idleRows'].append(dict(id=r['model'].lower(),name=r['model'],family='foundation' if fm else 'small',
            parameters=4883800 if fm else 274552,channels=17,mode='Frozen encoder + linear head' if fm else 'Scratch · 20 epochs',
            x=100*r['idle_false_trigger_trials']/r['idle_trials'],y=100*r['mi_detected_trials']/r['mi_trials'],
            xDetail=f"{r['idle_false_trigger_trials']} / {r['idle_trials']} idle trials",yDetail=f"{r['mi_detected_trials']} / {r['mi_trials']} command trials",
            abstain=r['degenerate_all_reject_subjects'],seconds=seconds,subjects=4,
            protocolId=extra['idleExtension']['protocolId'],auditSha=extra['idleExtension']['auditSha'],
            note=('Exact audited 17-channel input windows; scale microvolts / 100 and resample each completed window to 200 Hz. Average across time patches; preserve 17 × 200 features. Train-only StandardScaler and logistic regression (C=0.1). Pretraining overlap is not forensically certified.' if fm else 'Same four-subject windows as the original idle run. Train-only channel normalization; fixed 20 epochs of AdamW, learning rate 0.001, seed 20260910. No test-driven checkpoint selection.'),
            subjectResults=[dict(subject=f['subject'],recall=f['mi_detection_fraction']*100,falseRate=f['idle_false_trigger_fraction']*100,threshold=f['threshold'],abstain=f['degenerate_all_reject']) for f in fs]))
    q=ROOT/'experiments/low_channel_mvp_v1/outputs/run-20260910-mps-v1'
    if (q/'independent-audit.json').exists():
        approved(q);b=read(q/'summary.json');runtime=read(q/'runtime.json');rows=[]
        for key,a in b['aggregate'].items():
            r=a['all_test_trials'];iv=r['balanced_accuracy_descriptive_bootstrap_percentiles']
            rows.append(dict(id=key,name='EEGNet' if key=='eegnet' else 'CSP+LDA',family='small' if key=='eegnet' else 'classical',
                parameters=2146 if key=='eegnet' else None,channels=3,mode='Scratch · 20 epochs' if key=='eegnet' else 'Supervised fit',
                x=r['subject_mean_cohen_kappa'],y=100*r['subject_mean_balanced_accuracy'],xDetail='Cohen’s κ',yDetail='Mean over 9 subjects',
                interval=[100*iv['2.5'],100*iv['97.5']],abstain=None,subjects=9,subjectResults=[],
                seconds=sum(sum(f.get(k,0) for k in ['fit_predict_seconds','training_seconds','inference_seconds']) for f in runtime['per_fit'] if f['model']==key),
                note=f"Three native bipolar EEG channels, with EOG excluded. Two-class chance level: 50%. All trials retained. Using unchanged predictions on artifact-free test trials gives {100*a['artifact_free_sensitivity']['subject_mean_balanced_accuracy']:.2f}% subject-mean balanced accuracy; this is a prespecified sensitivity analysis."))
        extra['tracks'].append(dict(id='low-channel',title='Low-channel MI',short='Transfer across sessions',dataset='BNCI2014-004',
            subtitle='Three bipolar channels · within-person session transfer',type='accuracy',subjects=9,observations='6,520 trials · 2,840 held-out test trials',
            exposure='5 sessions per person · 4-second windows',status='Research preview',xLabel='Cohen’s κ',yLabel='Balanced accuracy',
            limitation='Within-person session transfer, not unseen-user transfer. Three subject-specific bipolar channels and feedback-conditioned sessions limit generalization; offline filtering is not streaming.',
            protocol=['For each of nine people, train on sessions 01T, 02T and 03T; test on 04E and 05E. No test-driven tuning or checkpoint selection.',
                'Use the three native bipolar EEG signals, exclude three EOG signals and apply no rereferencing. Do not treat these signals as standard monopolar electrode inputs to a foundation model.',
                'Offline fourth-order 4–40 Hz zero-phase filtering per session. Extract cue-relative 0–4 seconds, corresponding to 3–7 seconds after trial start.',
                'Retain all 6,520 labeled trials; 3,680 train and 2,840 test. Artifact-free sensitivity uses the same predictions without refitting.',
                'CSP with 3 components and regularization 0.1; LDA with automatic shrinkage. EEGNet uses 20 fixed AdamW epochs, learning rate 0.001 and train-only channel normalization.',
                'Two-class chance accuracy: 50%. Mean metrics weight each person equally. Intervals use 10,000 subject-bootstrap draws and are descriptive.',
                'Training sessions 01T/02T have no feedback; 03T and both test sessions have feedback. This acquisition difference remains part of the experiment.'],
            protocolId=b['protocol_id'],version='Official BNCI MAT snapshot / 2026-09-10',elapsed=runtime['wall_seconds'],
            peakGb=max(f['memory_after']['max_rss_bytes'] for f in runtime['per_fit'])/1e9,auditSha=sha(q/'independent-audit.json'),
            source='https://bnci-horizon-2020.eu/database/data-sets',rows=rows))
        extra['datasets'].append(dict(name='BNCI2014-004',task='Two-class motor imagery',subjects=9,channels=3,size='456 MiB',
            status='Downloaded · evaluated',detail='All 18 official MAT files parsed: 6,520 trials across 45 sessions. Native bipolar EEG; evaluated on held-out sessions with two baselines.',
            source='https://bnci-horizon-2020.eu/database/data-sets',license='CC BY-ND 4.0',evaluated=True))
    out=ROOT/'experiments/expanded_mvp_v1/mvp-reviewed-export.json'
    out.write_text(json.dumps(extra,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print({'idle_additions':len(extra['idleRows']),'extra_tracks':len(extra['tracks'])})

if __name__=='__main__':main()
