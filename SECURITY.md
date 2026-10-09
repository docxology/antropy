# Security

Report suspected vulnerabilities privately to daniel@activeinference.institute,
including affected version, reproducible input and expected impact. Avoid posting
sensitive data in public issues. There is no guaranteed response service level.

The CLI accepts finite numeric NPY/CSV files. NPY loading disables pickle.
Configuration uses JSON and research plans use YAML safe loading; unknown keys
fail. Numerical template and comparison budgets reject excessive work, although
files are loaded into memory before those limits apply. Run untrusted large data
with operating-system resource controls. The package performs no network access.
