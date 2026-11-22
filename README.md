# Unit 19 — SOC Alert Management Backend

## Deliverables

- `report/Unit19_DSA_SOC_Alerts_Technical_Report.docx` — editable technical report.
- `report/Unit19_DSA_SOC_Alerts_Technical_Report.pdf` — matching PDF export.
- `slides/Unit19_DSA_SOC_Alerts_Presentation.pptx` — 14-slide presentation with speaker notes.

## Requirements and evidence

- `docs/requirements-checklist.md` — full brief and Pearson Pass/Merit/Distinction criteria checklist.
- `docs/project-plan.md` — project workflow.
- `src/soc_alerts/` — executable Python implementation.
- `tests/` — pytest tests written before implementation.
- `benchmarks/benchmark.py` — reproducible timing and memory measurements.
- `results/` — raw benchmark JSON/CSV, demo output, RED/GREEN TDD logs, compile and verification logs.
- `diagrams/` — seven high-resolution PNG and SVG figures plus their source script.
- `appendices/` — source-code copies and appendix indexes.
- `screenshots/` — rendered PDF pages and slide previews used for visual QA.

## Run the code

From the project root:

```bash
PYTHONPATH=src python3 -m soc_alerts.demo
```

## Run tests

```bash
python3 -m pip install pytest
PYTHONPATH=src pytest -q
```

## Re-run benchmarks and figures

```bash
python3 benchmarks/benchmark.py
MPLBACKEND=Agg python3 diagrams/create_figures.py
```

## Rebuild Word/PDF and slides

The project includes the generation scripts in `docs/`. They use `python-docx`, `reportlab`, `python-pptx`, `matplotlib` and Pillow. A project-local `.deps/` folder contains the presentation/PDF library dependencies used in the VPS build; it is not required to run the alert backend or tests.

```bash
PYTHONPATH=.deps python3 docs/build_report.py
PYTHONPATH=.deps python3 docs/build_presentation.py
```

## Environment and verification

The backend was verified on the VPS (Python 3.12.3) and independently in the local container (Python 3.13.5). The VPS full test suite passed three consecutive runs (24 tests each); the local suite passed two consecutive runs (24 tests each). Compilation and demo execution passed in both environments. The 14-slide deck has speaker notes on every slide; the report and slides were rendered and visually reviewed. See `results/verification-summary.txt` and `results/local-test-log.txt`.

## Before submission

Replace these placeholders in the report and presentation:

- `[INSERT STUDENT NAME]`
- `[INSERT STUDENT ID]`
- `[INSERT TUTOR NAME]`
- `[INSERT ASSIGNMENT TITLE]`

The report's stated main-body word count is 5,149 words for sections 1–7, including headings, prose and table text; code extracts, references, cover, executive summary and appendices are excluded. Confirm the counting convention with your tutor if they require code extracts to be included.

Verification caveat: the initial TDD RED run failed at pytest collection because the production modules did not yet exist (import errors), rather than producing assertion-level failures. Command logs are included, but terminal-window screenshots were not captured; the screenshots folder contains rendered report and slide previews.
