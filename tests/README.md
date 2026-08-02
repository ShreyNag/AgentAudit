# Cross-cutting end-to-end tests

Top-level end-to-end scenario tests (launch benchmark -> execute -> persist trace -> evaluate ->
store scores -> retrieve report -> replay -> export) per PROJECT_SPEC_2 §124. Per-module unit
and integration tests live under `backend/tests/unit` and `backend/tests/integration`, mirroring
`backend/app/`. Frontend component/e2e tests live under `frontend/src/**/__tests__` and
`frontend/e2e/`.
