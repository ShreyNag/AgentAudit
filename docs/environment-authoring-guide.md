# Adding a New Benchmark Environment

Per PROJECT_SPEC_1 §107, adding an environment should require only a new environment directory,
new task definitions, and new tools -- no changes to the Runner, Evaluators, Dashboard, or
database schema.

## Steps

1. Create `backend/app/environments/<name>/` with:
   - `state.py` -- plain dataclasses holding the environment's deterministic, seeded in-memory
     state (see `banking/state.py` for the reference shape).
   - `environment.py` -- a `BaseEnvironment` subclass (`app/environments/base.py`) implementing
     `initialize/reset/observe/validate_action/step/is_complete/export_state/cleanup`. `step()`
     should dispatch to one private method per action, keyed by a dict (see
     `banking/environment.py`).
   - `seed_task.py` -- one `SEED_TASK` dict matching the `Task` schema
     (`app/benchmark/models.py`), including non-empty `ground_truth`.
   - `__init__.py` -- exposes `TOOLSET` and a `register()` function that registers the
     environment factory on `environment_registry` and its metadata on `benchmark_registry`.
2. Register the new package in `backend/app/environments/__init__.py`.
3. Create matching tools in `backend/app/tools/implementations/<name>_tools.py`: one
   `EnvironmentActionTool` subclass per environment action, and a `register()` function that
   adds them to `tool_registry`. Import and call it from
   `backend/app/tools/implementations/__init__.py`.
4. Add tests mirroring `backend/tests/unit/environments/test_travel_environment.py` and
   `backend/tests/unit/environments/test_all_environments.py` (the latter is parametrized across
   every environment automatically once yours is added to `ALL_ENVIRONMENT_CLASSES`).

If you name your package after a Python standard-library module (as `email` is), suffix it
(`email_env`) to avoid shadowing the stdlib module, and keep the *registered* environment name
(used everywhere else) the plain, spec-literal one.
