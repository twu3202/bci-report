# Multi-Task BCI Data Structure README

This dataset includes raw, preprocessed, and epoched EEG recordings for multi-task brain-computer interface (BCI) experiments. The dataset covers three paradigms: Motor Imagery (MI), Imagined Speech (IS), and Steady-State Visual Evoked Potentials (SSVEP).

## Folder Structure

The data is organized by subject. Please note that **raw** and **processed** data are provided as compressed archives (`.zip`), while **epoched** data and **questionnaire** results are uncompressed folders.

```text
root/
├── raw.zip                      # Unprocessed .fif files (compressed)
├── processed.zip                # Preprocessed .fif files (compressed)
├── epoched/                     # Pickled files: task- and block-based MNE Epochs objects
├── questionnaires/              # Survey templates and aggregated results
│   ├── interview.docx           # Template: Post-experiment subjective feedback
│   ├── questions.docx           # Template: Demographics \& pre-experiment state
│   └── questionnaire\_results.xlsx # Aggregated results for all subjects
└── summary\_trial\_counts.csv     # Summary of the number of trials per class per subject
```

## 1\. Raw Data (`raw.zip`)

**Location:** `raw/{subject\_id}/{subject\_id}\_raw.fif`
**Format:** MNE .fif

* **Description:** Unprocessed EEG data, with artifact labels cleaned and task/rest annotations present.
* **Supplementary Files:**

  * `{subject\_id}\_ssvep\_phase.csv`: Contains the phase of each SSVEP trial.

* **Subject Specific Notes:**

  * **Sub0 and Sub1:** Completed 30 test blocks instead of the standard 20.
  * **Sub13:** Contains more training trials for MI and IS due to accidental actual speech/movement in early blocks. It is recommended to simply use the last 60 trials for analysis.

## 2\. Preprocessed Data (`processed.zip`)

**Location:** `processed/{subject\_id}/{subject\_id}\_preprocessed.fif`
**Format:** MNE .fif

**Processing Pipeline:**

* **Notch filter:** 50/100/150/200 Hz (remove line noise).
* **Bandpass filter:** Typically 0.5–100 Hz.
* **ICA:** Independent Component Analysis to remove eye/other artifacts.
* **Downsampling:** Downsampled to 200 Hz.

**Supplementary Files:** `ica\_excluded\_components.png` (Visualizes the removed eye-artifact components).

## 3\. Epoched Data (`epoched/`)

**Location:** `epoched/{subject\_id}/epochs.pkl`
**Format:** Python pickle containing a dictionary (`dict`) of MNE Epochs objects and arrays.

### Dictionary Structure

The `epochs.pkl` file contains the following keys:

* **SSVEP:**

  * **Training:** `"ssvep-1"`, `"ssvep-2"`, `"ssvep-3"`, `"ssvep-4"`, `"ssvep-na"`.
  * **Testing:** `"ssvep-t1"`, `"ssvep-t2"`, `"ssvep-t3"`, `"ssvep-t4"`.

* **Motor Imagery (MI):**

  * **Training:** `"mi-1"` (Thumb), `"mi-2"` (Index), `"mi-3"` (Point), `"mi-na"`.
  * **Testing:** `"mi-t1"`, `"mi-t2"`, `"mi-t3"`.

* **Imagined Speech (IS):**

  * **Training:** `"is-1"` (Next), `"is-2"` (Back), `"is-3"` (Select), `"is-na"`.
  * **Testing:** `"is-t1"`, `"is-t2"`, `"is-t3"`.

* **Artifacts:** `"blink-1"`, `"blink-2"`, `"jaw"`, `"breath"`, `"rhand"`.
* **Continuous Test Data:**

  * `"test\_block"`: A tuple `(test\_eeg\_blocks, test\_state\_blocks)` containing entire test blocks for sequence decoding.
  * `test\_state\_blocks`: Integer array where **0 = rest** and other integers map to tasks (see Section 5 below).

## 4\. Questionnaires \& Metadata

This dataset includes the original survey templates and a consolidated Excel file of subject responses.

### A. Pre-Experiment (`questions.docx`)

**Purpose:** Collects demographics and physiological state before the session.

* **Demographics:** Biological gender, Age, and Language proficiency (daily usage/proficiency order).
* **Physiological State:**

  * Consumption of coffee, tea, or energy drinks (within 3 hours).
  * Sleep quality (previous night) and current sleepiness.

* **Exclusions:** Personal financial information (bank account number, name) and student ID numbers used for compensation are **excluded** from the open dataset.

### B. Post-Experiment (`interview.docx`)

**Purpose:** Collects subjective feedback on the BCI paradigms.

* **Subjective State:** Self-reported Physical and Mental state (rated 1–5).
* **Task Assessment:** For each paradigm (Motor Imagery, Imagined Speech, SSVEP), subjects rated:

  * Ease of performance.
  * Comfort.
  * Difficulty focusing.
  * Perceived missed trials.

* **Preference:** Subjects ranked the three paradigms based on their willingness to use them in the future.

### C. Aggregated Results (`questionnaire\_results.xlsx`)

**Content:** A compiled Excel file containing the anonymized responses for all subjects.

---

## 5\. Event Mapping

### Annotation Labels

The following string annotations are used in the `.fif` files and `epochs.pkl` keys to mark events:

* **SSVEP:** `ssvep-1` (8Hz), `ssvep-2` (9.2Hz), `ssvep-3` (10.4Hz), `ssvep-4` (11.6Hz).
* **Motor Imagery (MI):** `mi-1` (Thumb), `mi-2` (Index), `mi-3` (Point).
* **Imagined Speech (IS):** `is-1` (Next), `is-2` (Back), `is-3` (Select).
* **Artifacts:** `blink-1` (Once), `blink-2` (Twice), `jaw`, `breath`, `rhand`.
* **Markers:** `b-start`, `b-end`, `rest`.

### Test Block Integer Map

For the continuous `test\_state\_blocks` arrays inside `epochs.pkl` (under the key `"test\_block"`), the following integer mapping is used:

```python
event\_int\_map = {
    "ssvep-t1": 1,
    "ssvep-t2": 2,
    "ssvep-t3": 3,
    "ssvep-t4": 4,
    "mi-t1":    5,
    "mi-t2":    6,
    "mi-t3":    7,
    "is-t1":    8,
    "is-t2":    9,
    "is-t3":    10
}
# 0 indicates "rest"
```

## How To Use

Look at the data\_loading\_example.ipynb for examples

