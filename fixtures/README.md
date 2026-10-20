# Self-test fixtures

These projects are here so `.github/workflows/self-test.yml` can run the reusable workflows. They are not libraries to import from other repositories.

- `python-app` is fully covered and is called with a coverage threshold of 80.
- `python-low-cov` leaves one function untested and is called with the threshold left off.
- `node-npm` and `node-pnpm` exercise the two package managers.
