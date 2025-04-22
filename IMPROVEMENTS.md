1. Date/Rollover logic

   * Issue: Current JSONL approach never rotates files; all data grows unbounded.

   * Improvement: Enable daily JSON rotation or partition by date subdirectories. Add a cleanup/archival job for old data.

2. Storage problems

   * Issue: In‑memory UPC_SEEN set and JSONL store will become a bottleneck at scale. Also, using `hostPath` is not ideal.

   * Improvement: Migrate storage to a real database (e.g. PostgreSQL) and switch from `hostPath` to `PersistentVolumeClaim`.

3. Observability

   * Issue: Only basic logging in place. No structured logs or metrics.

   * Improvement: Integrate Prometheus metrics (e.g. request count, parse errors, duplicates), add health checks (liveness/readiness) for Kubernetes. Use ELK to centralize logs.

4. Test coverage

   * Issue: Unit tests cover only validators; no integration tests.

   * Improvement: Add end-to-end tests spinning up both server & client in a test container. Expand test coverage to scraper logic.

5. Hardcoded values

   * Issue: Values like `GRPC_PORT` are hardcoded in the `ConfigMap` and in the deployment file. This makes it difficult to manage environment-specific configurations.

   * Improvement: Convert Kubernetes manifests into a Helm chart and use `values.yaml` for better reusability and parameterization.

