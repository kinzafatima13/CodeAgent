# CodeAgent

A coding agent that takes architecture documentation + UML diagrams and generates a runnable project.

It uses the DeepSeek API (tool calling) and comes with both a simple Windows GUI and a CLI.

## What it does

You give it two markdown files:
- `Architecture_Documentation.md`
- `Architecture_View.md` (contains PlantUML diagrams)

The agent reads them, plans the work, writes the source code, tests, Dockerfile, README, etc. into an output folder.

Sample input included in `tests/fixtures/` is the **Space Fractions** educational game.

## Quick start (from source)

```bash
pip install -r requirements.txt
python app.py
```

Or use the CLI:

```bash
python -m code_agent.cli \
  --doc Architecture_Documentation.md \
  --views Architecture_View.md \
  --out generated \
  --api-key sk-...
```

You can also set the `DEEPSEEK_API_KEY` environment variable instead of passing `--api-key`.

### GUI usage

1. Run `python app.py` (or the built `.exe`)
2. Paste your DeepSeek API key
3. Select the two input `.md` files and an output directory
4. (Optional) enable "Allow agent to run tests" — this is **off by default** for safety
5. Click Run

## Building the Windows exe

On Windows with Python 3.10+:

```bat
build_exe.bat
```

This produces `dist\CodeAgent.exe` using PyInstaller.

There is also a GitHub Actions workflow (`.github/workflows/build-windows.yml`) that builds the exe on a Windows runner.

## Project layout

```
code_agent/
  agent.py       # main agent loop
  tools.py       # file + command tools (sandboxed)
  llm.py         # DeepSeek client
  prompts.py     # system prompt
  preprocess.py  # parses the architecture docs + PlantUML
  gui.py         # simple tkinter GUI
  cli.py         # command-line interface
  runner.py      # shared run logic
  config.py      # settings
tests/           # unit tests
docs/
  SECURITY_QA.md # security notes and test coverage
```

## How the agent works

1. Preprocess the two markdown files into structured JSON
2. Send a system prompt + the structured input to DeepSeek
3. Agent loop: model calls tools → host executes them → results go back
4. Tools available: list/read/write/edit files, run limited commands, todo list, finish
5. Everything is restricted to the output directory
6. Command execution is opt-in and heavily restricted (no shell, allow-list only)

## Tests

```bash
python -m unittest discover -s tests
# or
pytest
```

## Notes / limitations

- The agent tries to produce a working project, but quality still depends on the model. Always check the output.
- Running generated tests requires Node/Python on the machine and the opt-in checkbox.
- The sample architecture document has a few inconsistencies (documented in the agent’s assumptions file when it runs).

## License

Personal / course project.
