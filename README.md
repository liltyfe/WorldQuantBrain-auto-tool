# WorldQuant Brain Python Toolkit

Lightweight Python scripts for fetching data fields, generating alpha expressions,
running simulations, and submitting selected alphas to WorldQuant Brain.

## What This Repo Contains

This project is script-first (interactive CLI style), centered on:

- `findalpha_mold/python_script/getdata.py` - fetch data fields to CSV
- `findalpha_mold/python_script/generate_alphas.py` - generate alphas from one template
- `findalpha_mold/python_script/generate_alphas_batch.py` - batch generation from JSON config
- `findalpha_mold/python_script/simulateAlpha.py` - run alpha simulations and save results
- `findalpha_mold/python_script/submitAlpha.py` - submit selected alphas
- `findalpha_mold/python_script/inspect_alpha_packet.py` - inspect exported HAR/JSON packets and list available fields

## Repository Layout

```text
findalpha_mold/
  Data/                       # input data field CSV files
  alpha_configs/              # batch generation configs
  alpha_expressions/          # generated alpha expression files (runtime output)
  alpha_log/                  # simulation logs (runtime output)
  alpha_result/               # simulation/submission outputs (runtime output)
  python_script/              # core scripts
```

## Requirements

- Python 3.10+ (3.11+ recommended)
- Packages:
  - `requests`
  - `pandas`

Install:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install requests pandas
```

Optional dev tools:

```bash
python -m pip install pytest ruff
```

## Credentials Setup

Create `findalpha_mold/python_script/brain_credentials.json`.

Supported formats:

```json
["API_KEY", "API_SECRET"]
```

or

```json
{
  "API_KEY": "your_api_key",
  "API_SECRET": "your_api_secret"
}
```

Do not commit this file.

## Typical Workflow

Run scripts from `findalpha_mold/python_script/`.

### 1) Fetch data fields

```bash
python getdata.py
```

Prompts guide dataset id and field type; output CSV lands in `findalpha_mold/Data/`.

### 2) Generate alpha expressions

Single-template mode:

```bash
python generate_alphas.py
```

Batch config mode:

```bash
python generate_alphas_batch.py
```

### 3) Simulate generated alphas

```bash
python simulateAlpha.py
```

Outputs include:

- `saved_alphas.jsonl`
- `elite_alphas.jsonl` (filtered high-quality alphas)
- `alphas_detailed.csv`
- daily log file in `findalpha_mold/alpha_log/`

### 4) Submit selected elite alphas

```bash
python submitAlpha.py
```

### 5) Inspect exported platform packets

If you do not have official API access but can log in from a browser, export a `HAR`
file from the DevTools `Network` panel and inspect it offline:

```bash
python inspect_alpha_packet.py --input ../Data/sample.har
```

Outputs include:

- `raw_responses/`
- `field_inventory.csv`
- `field_summary.csv`
- `response_index.json`

## Validation Commands

Build/smoke check:

```bash
python -m compileall findalpha_mold/python_script
```

Lint (if ruff installed):

```bash
ruff check findalpha_mold/python_script
ruff format --check findalpha_mold/python_script
```

Tests (if/when added):

```bash
python -m pytest
python -m pytest path/to/test_file.py
python -m pytest path/to/test_file.py::test_name
python -m pytest path/to/test_file.py::TestClass::test_method
```

## Notes

- API calls can be rate-limited; scripts handle retry headers where implemented.
- Session refresh is built into scripts that run for longer periods.
- Generated runtime data folders are git-ignored by default.

## Troubleshooting

- Login fails: verify `brain_credentials.json` path and JSON format.
- Missing data columns: ensure CSV contains expected columns (for example `id`).
- No alphas to submit: confirm `elite_alphas.jsonl` exists and includes records.

## Safety

- Never commit API keys, secrets, or raw sensitive responses.
- Review alpha performance metrics before submission.

## License

For learning and research use.
