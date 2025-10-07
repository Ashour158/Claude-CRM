# Merge Readiness & Completion Checklist – PR #39 (Hardening & ML Expansion)

Status: MERGED (sha: bb98501344447854e09d623afae6b5fc232ad479)
Date: 2025-10-07

## Owners
| Domain | Owner | Slack / Contact |
|--------|-------|-----------------|
| Backend | @Ashour158 | N/A |
| Security | @Ashour158 | N/A |
| Data / ML | @Ashour158 | N/A |
| Observability | @Ashour158 | N/A |
| Product | @Ashour158 | N/A |

## 1. Scope Recap
Included:
- WASM sandbox scaffolding & feature flag (FF_PLUGIN_WASM)
- Event schema enforcement escalation (warn|block)
- Policy bundle signing + verification (optional enforcement)
- pgvector column & index preparation (Lead, Deal)
- Lead scoring pipeline & SHAP cache scaffolds
- Expanded test suite skeletons
- Metrics for sandbox, model training, SHAP cache, policy verification

Out of Scope (Still Pending):
- True secure WASM runtime isolation (real engine + syscall gating)
- Full LightGBM + SHAP dependencies in production image
- Continuous scheduling of model retraining & feature drift monitoring
- Multi-object embedding beyond Lead & Deal

## 2. Verification Steps
(Completed or to verify; check each)
- [ ] Applied migrations cleanly on staging DB
- [ ] Verified pgvector extension exists (`CREATE EXTENSION IF NOT EXISTS vector`)
- [ ] Ran `train_lead_model --org-id <org> --version v1 --dry-run`
- [ ] Trained model and stored artifact
- [ ] Promoted a policy bundle both unsigned (warn) and signed (enforced)
- [ ] Executed privacy simulation for sample subject
- [ ] Event schema invalid payload returns 400 in block mode
- [ ] Backfilled embeddings: `backfill_lead_embeddings`
- [ ] SHAP cache warm attempt (hit/miss metrics increment)
- [ ] Observed new Prometheus metric families present
- [ ] Logs include `X-Correlation-ID` field

## 3. Risk Areas & Mitigations
| Area | Risk | Mitigation |
|------|------|------------|
| WASM Sandbox | Placeholder may mislead security assumptions | Default flag off; document limitations |
| ML Models | Library absence triggers stub path | CI check for real deps; feature flag gating |
| pgvector Index | Performance if lists param mis-sized | Make lists configurable; monitor kNN latency |
| Policy Signing | Key mismatch causes false negative | Key fingerprint log & verify command |
| Event Enforcement | Unexpected production blocking | Phased rollout warn → sample → block |

## 4. Immediate Follow-ups
1. Implement real WASM isolation (timeline below)
2. Add model artifact integrity hash & reproducibility metadata
3. Add vector health dashboard to Grafana
4. Expand integration tests for cross-feature flows

## 5. Exit Criteria (to mark hardened)
| Feature | Criteria |
|---------|----------|
| Sandbox | Real runtime + denial tests (network/file) pass |
| Signing | CI auto-sign test; invalid signature blocked |
| Vector | p95 semantic search < 300ms @ baseline dataset |
| Lead Model | AUC > baseline by +5%; SHAP latency p95 < 80ms |
| Event Enforcement | 0 critical blocks over 7-day ramp |

## 6. Commands Reference
```
python manage.py migrate
python manage.py train_lead_model --org-id 1 --version v1
python manage.py refresh_shap_cache --org-id 1 --model-id <id> --limit 200
python manage.py sign_policy_bundle --bundle-id 5 --key-path ./keys/policy_signing.pem
python manage.py promote_policy_bundle --bundle-id 5 --stage prod
python manage.py check_vector_index --entity Lead
```

## 7. Open Questions
- Per-tenant vs global signature enforcement?
- Progressive sampling ramp tool needed?

---