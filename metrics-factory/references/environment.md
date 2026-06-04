# MetricsFactory Environment

Use a project-local runtime for repeatable metric jobs. The skill can use an existing environment if it passes `check_runtime.py`, or create one with `setup_runtime.py`.

## Python

- Minimum: Python 3.10.
- Recommended: Python 3.11 or 3.12.
- The Python executable and native wheels must use the same CPU architecture.
- Do not assume `.venv`, Conda, Homebrew, pyenv, or a user-specific path exists.

## Dependency Ranges

Recommended runtime packages:

```text
numpy>=1.26,<2.1
pandas>=2.2,<3.1
scipy>=1.11
numba>=0.60
pyarrow>=15
python-dateutil>=2.8
tqdm>=4.60
psutil>=5.9
```

`psutil` is optional for calculation but recommended because worker planning uses available-memory checks.

## Runtime Check

Run:

```bash
python <skill-dir>/scripts/check_runtime.py --project-root <project-root>
```

The script exits `0` when the active Python can run MetricsFactory, and `2` when blockers exist. It prints JSON with dependency versions, import errors, and suggested next commands.

## Automatic Setup

Run:

```bash
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root>
```

Default behavior:

- creates `<project-root>/.metricsfactory-venv`;
- installs dependencies inside that venv only;
- runs `check_runtime.py` with the venv Python.

Optional arguments:

```bash
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root> --python /path/to/python
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root> --venv .custom-venv
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root> --index-url https://example/simple
python <skill-dir>/scripts/setup_runtime.py --project-root <project-root> --no-install
```

Do not use automatic setup to install packages into system Python or global user site-packages.

## Using The Created Runtime

macOS/Linux:

```bash
<project-root>/.metricsfactory-venv/bin/python <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --dry-run
```

Windows:

```bash
<project-root>/.metricsfactory-venv/Scripts/python.exe <skill-dir>/scripts/run_metrics_job.py --project-root <project-root> --request job.json --dry-run
```
