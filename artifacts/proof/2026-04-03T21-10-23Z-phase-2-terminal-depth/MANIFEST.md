# Milestone Manifest

## Objective
Phase 2 terminal depth pass: improve follow-up context, source lineage/previews, trace readability, and brief consistency while preserving demo determinism.

## Scope
- Session-aware follow-up continuity for the main research terminal loop.
- Richer source lineage and preview metadata in brief outputs and UI.
- Trace readability improvements with grouped progression and clearer labels.
- Consistent brief structure across macro outlook, event probability, and ticker-plus-macro query classes.
- Deterministic demo behavior maintained and validated by repeatability checks.

## Metadata
- Generated at (UTC): 2026-04-03T21-10-23Z
- Git SHA: 22e359bbdb8c9c5a86348a2dab4e84a95bb69171
- Git branch: main
- Git dirty: True
- Harness summary: artifacts/harness/2026-04-03T21-09-40Z/summary.json

## Git Dirty Files
- M apps/api/routers/research.py
- M apps/web/app/page.tsx
- M apps/web/components/Terminal/QueryInput.tsx
- M apps/web/components/Terminal/ResearchPanel.tsx
- M apps/web/components/Terminal/TracePanel.tsx
- M apps/web/components/Terminal/types.ts
- M apps/web/styles/globals.css
- M docs/API.md
- M src/meridian/agent/react.py
- M src/meridian/normalisation/schemas.py
- M tests/e2e/test_research_flow.spec.ts
- M tests/unit/api/test_research.py
- M tests/unit/web/ResearchPanel.test.tsx
- M tests/unit/web/TracePanel.test.tsx
- ?? tests/unit/web/QueryInput.test.tsx

## Exact Commands Run
```bash
npm run tsc
npm run vitest -- --reporter=json --outputFile /home/aarav/Aarav/Meridian/artifacts/harness/2026-04-03T21-09-40Z/vitest-report.json
/home/aarav/Aarav/Meridian/.venv/bin/python -m pytest -q --junitxml /home/aarav/Aarav/Meridian/artifacts/harness/2026-04-03T21-09-40Z/pytest-report.xml
npm run playwright -- --reporter=json
npm run test:unit
pytest -q
npm run playwright
```

## Exact Results
- all_green: True
- test_layers_green: True
- typescript: exit=0, passed=None, failed=0, skipped=0, retries=0
- frontend_unit: exit=0, passed=8, failed=0, skipped=0, retries=0
- backend_unit: exit=0, passed=46, failed=0, skipped=0, retries=0
- e2e: exit=0, passed=5, failed=0, skipped=0, retries=0
- determinism_signature_sha256: 70d151599442930905b8dce3f15fedbb6cdf373b1e6e0558089d1a1070d63528

## Root Causes If Fixes Were Needed
- Fixed a frontend unit assertion mismatch after introducing session-id hint truncation.

## File Inventory
- README.md (378 bytes)
- TOUR.webm (180617 bytes)
- deployment/ci.yml (797 bytes)
- deployment/vercel.json (398 bytes)
- manifest.json (15781 bytes)
- playwright-report/data/106dc73d8c507aa2eab7cdd7dd76d8dd5232557d.zip (762342 bytes)
- playwright-report/data/29d2ba9f54f2e2957b256cce7298b0975ffa93ad.png (473633 bytes)
- playwright-report/data/2e544fb192f5629d39e0ac7f41d526f251e1b2e3.png (502485 bytes)
- playwright-report/data/32ea812c57b380fa897c75719ecbb4d674d76a33.zip (489422 bytes)
- playwright-report/data/40933a6049e11ccc33daa81cd41d88e690ded530.zip (786414 bytes)
- playwright-report/data/468c269e869242dd86229bc38349b54af4a42e87.zip (821203 bytes)
- playwright-report/data/5133f00e240bbf4542bfeca2d8aba0a31e630fa9.webm (190301 bytes)
- playwright-report/data/6f0a5669844a20a26497f21f24c9c129abe8cf1e.md (9123 bytes)
- playwright-report/data/8a4e10dbe116f66c5819b664306b9ac4e08b6ee2.webm (190301 bytes)
- playwright-report/data/8d168966cd8234f141b0c75a22572bf5fe872e4e.webm (182578 bytes)
- playwright-report/data/95133217455737c4829298026a3ad9075aba0093.md (5349 bytes)
- playwright-report/data/9e275ce899bcccb018372a6f3201ee1f857a9631.md (8936 bytes)
- playwright-report/data/a8c8fcb3a3b75adf8217f4d76cf8f5e960c0cc13.webm (190301 bytes)
- playwright-report/data/b141ed025fa861c09ddb2feac7ab1f0420a0e5d8.webm (75178 bytes)
- playwright-report/data/ce6c9b4aae997bd7ba549650aa838a49de0843d6.png (381809 bytes)
- playwright-report/data/d1ea46426c9b7557fc20c43160aeb3a11979aa1b.md (9826 bytes)
- playwright-report/data/d6e93bf46697914aa09d4138550c2c19053084c1.zip (821414 bytes)
- playwright-report/data/dd60b081e081eb4c864a2a52f8228802b072ac83.md (2883 bytes)
- playwright-report/index.html (535260 bytes)
- playwright-report/trace/assets/codeMirrorModule-DS0FLvoc.js (313023 bytes)
- playwright-report/trace/assets/defaultSettingsView-GTWI-W_B.js (643623 bytes)
- playwright-report/trace/codeMirrorModule.DYBRYzYX.css (6421 bytes)
- playwright-report/trace/codicon.DCmgc-ay.ttf (80340 bytes)
- playwright-report/trace/defaultSettingsView.B4dS75f0.css (110544 bytes)
- playwright-report/trace/index.C5466mMT.js (6509 bytes)
- playwright-report/trace/index.CzXZzn5A.css (2111 bytes)
- playwright-report/trace/index.html (2283 bytes)
- playwright-report/trace/manifest.webmanifest (429 bytes)
- playwright-report/trace/playwright-logo.svg (5033 bytes)
- playwright-report/trace/snapshot.html (935 bytes)
- playwright-report/trace/sw.bundle.js (95084 bytes)
- playwright-report/trace/uiMode.Btcz36p_.css (60239 bytes)
- playwright-report/trace/uiMode.Vipi55dB.js (38156 bytes)
- playwright-report/trace/uiMode.html (647 bytes)
- playwright-report/trace/xtermModule.DYP7pi_n.css (4150 bytes)
- screenshots/homepage.png (54743 bytes)
- screenshots/methodology.png (451548 bytes)
- screenshots/screener.png (364280 bytes)
- test-results/backend_unit.log (298 bytes)
- test-results/e2e.log (12039 bytes)
- test-results/frontend_unit.log (622 bytes)
- test-results/harness-summary.json (2724 bytes)
- test-results/playwright/.last-run.json (45 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/test-finished-1.png (286572 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/trace.zip (642487 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/video.webm (48036 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/test-finished-1.png (22576 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/trace.zip (235287 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/video.webm (28872 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/test-finished-1.png (85206 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/trace.zip (2118590 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/video.webm (242116 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/test-finished-1.png (199546 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/trace.zip (824667 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/video.webm (103596 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/test-finished-1.png (22574 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/trace.zip (242913 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/video.webm (25500 bytes)
- test-results/typescript.log (125 bytes)

## Known Limitations
- Session context is in-memory and scoped to the running API process (no durable persistence yet).

## Current Deployment Status
Vercel config present; frontend rewrite target configured via MERIDIAN_API_BASE_URL=https://meridian-api.railway.app.

## SHA256 Checksums
| File | SHA256 | Size (bytes) |
|---|---|---:|
| README.md | 02e13bf2b26256f4772e2ed0fcb5c4a1af301dcd56e6f17a4f868f9ba0e625b8 | 378 |
| TOUR.webm | 3cd944f5c4941200432c7c971099d8e3bc06dfc86943aa0d3bd3b088d59379ff | 180617 |
| deployment/ci.yml | 558604a54fb0eb4e4af61028bf43712e258460eded58a3d26d293e321e289a94 | 797 |
| deployment/vercel.json | 9b5e79d0c68b91c7c37351be091f0c0614f5be110ae3a724aa41cf1d60644dd6 | 398 |
| manifest.json | 5e893772e00c59d1c814fea5ef3c5a61c8841bc145e7d3216ef977d77eee457c | 15781 |
| playwright-report/data/106dc73d8c507aa2eab7cdd7dd76d8dd5232557d.zip | 5dcc71ef6a70343c4dd9f74bc71a988abde617bc4187ae043d655cf17743275d | 762342 |
| playwright-report/data/29d2ba9f54f2e2957b256cce7298b0975ffa93ad.png | a59eae04a773e31ca6a385271b0f19c4887ef99dda3a1909f01bd495a557614e | 473633 |
| playwright-report/data/2e544fb192f5629d39e0ac7f41d526f251e1b2e3.png | 80acc2d27bb309e860a5fb30fd53183657d712ff4e431cad5b923f5c7f6d41f9 | 502485 |
| playwright-report/data/32ea812c57b380fa897c75719ecbb4d674d76a33.zip | 6e04d05a0d17d434cc36730aaeb1bdf6b89173d18879b6b49716395a43051b5e | 489422 |
| playwright-report/data/40933a6049e11ccc33daa81cd41d88e690ded530.zip | f9a3b315e19c29af404604318d4591caf043014a291b24d5b4f098d9b9560586 | 786414 |
| playwright-report/data/468c269e869242dd86229bc38349b54af4a42e87.zip | 69d482429cbe9bb40570c5757e1f96864c8f1598d87a2f8934d2e635a2d7b37e | 821203 |
| playwright-report/data/5133f00e240bbf4542bfeca2d8aba0a31e630fa9.webm | 957f9194c55d1b72210c19976d519bda3f3a46fb9c938c6971a3d6761ea23477 | 190301 |
| playwright-report/data/6f0a5669844a20a26497f21f24c9c129abe8cf1e.md | 5c23e016ee60cb9b325c82fd96f1e886f00301bf94ef99eeb4dfbf98867bad19 | 9123 |
| playwright-report/data/8a4e10dbe116f66c5819b664306b9ac4e08b6ee2.webm | 633a0d877858fbaad125e1f6b7c9de6f21eafd5b0c41112d8ab00920ad36cdc4 | 190301 |
| playwright-report/data/8d168966cd8234f141b0c75a22572bf5fe872e4e.webm | 1f505cb8f5b459643ff8494dfab333b3d6504f534876247b4989bf30afc32905 | 182578 |
| playwright-report/data/95133217455737c4829298026a3ad9075aba0093.md | f9ca0e97a5f02a9bb3ec5928cc7d5bce0373af9625974d6e7d6c651b5a5cfff6 | 5349 |
| playwright-report/data/9e275ce899bcccb018372a6f3201ee1f857a9631.md | d19a08dc338de3cc614f7e7d8042a14c505638d983cbbdbb11f180d8590dc82a | 8936 |
| playwright-report/data/a8c8fcb3a3b75adf8217f4d76cf8f5e960c0cc13.webm | c12c025cd670db5158124fc625e5fe2d500f0adf261198876f7f9ac3e4cc884a | 190301 |
| playwright-report/data/b141ed025fa861c09ddb2feac7ab1f0420a0e5d8.webm | 1204f6ab9904601a186d73d5015516e8168f3af4f26e0edf70dd7f728819242f | 75178 |
| playwright-report/data/ce6c9b4aae997bd7ba549650aa838a49de0843d6.png | af5b7745f9d6b3925295016a60d794ce82dc116ea4d02c3ff84762be7dd0263d | 381809 |
| playwright-report/data/d1ea46426c9b7557fc20c43160aeb3a11979aa1b.md | 93d49ea57b92cf6e69eafb5ef9aa8e16fcc1adca3c1e631fce379995919ed382 | 9826 |
| playwright-report/data/d6e93bf46697914aa09d4138550c2c19053084c1.zip | 671b19d606f4b930cceb14568ef127ae495f3cf1971bda1d288111db3b45bae6 | 821414 |
| playwright-report/data/dd60b081e081eb4c864a2a52f8228802b072ac83.md | e959b8e7f20c3a7a5c9108942b30e69e63a148e78f592f47bb2473514213f1a0 | 2883 |
| playwright-report/index.html | f611736c1de1d832442bf2ddbec33b9c5694f303c010ebdd2829de597cb458b5 | 535260 |
| playwright-report/trace/assets/codeMirrorModule-DS0FLvoc.js | dd5360bef14066001507518e8c2f6b3e525ac1cc41fa7fdf23c34e96f4efadb1 | 313023 |
| playwright-report/trace/assets/defaultSettingsView-GTWI-W_B.js | 9c48649a4dfc1ba799a687c4ac96a6a9ada57696116044c227c67c51ebbfdce7 | 643623 |
| playwright-report/trace/codeMirrorModule.DYBRYzYX.css | 70bf421a13e87857ca684bfa2cc55f06d7c5a50f71253a3ff1d74769b14a957e | 6421 |
| playwright-report/trace/codicon.DCmgc-ay.ttf | 0f1d5219934e96e83b8db162d60b4d8c09b5de1e7d38031cbafe4a3c0f2889c9 | 80340 |
| playwright-report/trace/defaultSettingsView.B4dS75f0.css | 844a328b121a95937eec1893b391d5a3473194568dc585ba927f16c8ed0f90c8 | 110544 |
| playwright-report/trace/index.C5466mMT.js | 452eab81f93a4001fee058fa2cd1d4e245eed3d28bfe10f7296a6c099ce8d64f | 6509 |
| playwright-report/trace/index.CzXZzn5A.css | 4ec2a3d49db259ce9025cb4fa48d73b1afd58215e567eef3b4a4cbf76c1674d9 | 2111 |
| playwright-report/trace/index.html | 4c31886e6b746d02ab0ee0f5f5b8524d855573d6fdc99bf1a280db90a51e0987 | 2283 |
| playwright-report/trace/manifest.webmanifest | d8540500603a32a39fe7e5a0375dc0f9ebafd11118e06a846db7efc608223ab9 | 429 |
| playwright-report/trace/playwright-logo.svg | 6b0a4367bdeab10995bc239278f04c68c10e48adbec15e799e01909a0d66dcb9 | 5033 |
| playwright-report/trace/snapshot.html | e192546675329f804bb9d4afbd96f7a1368e53cc42a05f0cc4a57949df7bc245 | 935 |
| playwright-report/trace/sw.bundle.js | c76aa023df69a0835d12bfae95dddf91c5c90e4e87791d64f41aa051f394d678 | 95084 |
| playwright-report/trace/uiMode.Btcz36p_.css | bfe8330cc78eeb1b1c4d8983aab7068d725526e407903ee19e515996250cb221 | 60239 |
| playwright-report/trace/uiMode.Vipi55dB.js | fb1005d82811458ffd6ae041d79cc7ebabcb6073f7fe03b5f7694c093433ba7b | 38156 |
| playwright-report/trace/uiMode.html | 6cb988cb543334e85350fea36b4ccecae80e76294e0f6c326d7067a1cfa7aaaa | 647 |
| playwright-report/trace/xtermModule.DYP7pi_n.css | 7c5a01f382f76539fc9b4db6b18e18a7035741845fd14968c5cdc0a7e373d817 | 4150 |
| screenshots/homepage.png | 9d137e29c24d51567e1f47c0a77449ca28698463e9d218c9c843d7a490c50169 | 54743 |
| screenshots/methodology.png | b590174b6666c0c6a1e68742cca57d6842fa7ccc5d30c523f46b4f944d658609 | 451548 |
| screenshots/screener.png | 3dd69f3e6b6e4980dc060123ebf4eea44790453abea2866229491c248ad16d4c | 364280 |
| test-results/backend_unit.log | b7ff2dbf4d15b77657fc24ca33e03545520b7654a6ca30cb0c94a28571d0daf7 | 298 |
| test-results/e2e.log | 70138d1ba0a69a9eb40c145a02dda3b1b728b0d70a5d6f3795c8265d7e6fb36f | 12039 |
| test-results/frontend_unit.log | 88d2876bde0581485354109990ce6a08df0aa0d35000cdb1fb162f4ed88c3295 | 622 |
| test-results/harness-summary.json | a7cd55bdaab8af6c532a58c1cd3e9f9eea9a2fcd9e80df155766f19ec9c5a5d9 | 2724 |
| test-results/playwright/.last-run.json | 91d1c43004802cd49950d78eb11c8fa7d05da8ffffe219a8b13b2f561bc00903 | 45 |
| test-results/playwright/test_methodology-methodology-page-renders/test-finished-1.png | 022e6676920508f7c3f565f9e166d31fddb52c73e93bc473e801d1e59e2e3ff8 | 286572 |
| test-results/playwright/test_methodology-methodology-page-renders/trace.zip | df4c99afdaccb949953fa1ed1c8a7c2d47cee329ca96ef8b841c1d1408f9ba51 | 642487 |
| test-results/playwright/test_methodology-methodology-page-renders/video.webm | 87b29373cbff81080f776fc06dc2a52723bb56fa6b79d79a1b9b2a337f531b95 | 48036 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/test-finished-1.png | 250bd3d3ab1da4f694eff8fa4431d302541ef5169eb97158dd62e4f8c8fcc251 | 22576 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/trace.zip | eaa96569182da2cf1a27131d587b47fcdf898c7164a4f1bd9c93fd9c3c0e0937 | 235287 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/video.webm | f067a80eb89df5bb4a2199af0e51e8ed8f2e5690d323c47a53bf0e81cb7e936e | 28872 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/test-finished-1.png | 9d70086be07c3753ef57d7bef549eb74cbc23bb1562d1511df4e484050d6332f | 85206 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/trace.zip | e1adf4d9def796798ce32ac83c8e9e0311cd1f8c15785bc4b62c6509da1e5579 | 2118590 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/video.webm | b99a1f67eb9b81ad9a12b80280a454ad9212a95426419e9cd2bef0becc1ff2b5 | 242116 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/test-finished-1.png | 0cdfda147f77baee4a93a3c2a080d0ec34e889e88b9c51218df2fb08d476ea0b | 199546 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/trace.zip | 35af35c4afa69069ea55f18d17736e529c593c966820fb7f406fe41e88829706 | 824667 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/video.webm | 34b4affd0486364f81edbb72985940e15bd231f1a788c6591154ad5eacf293b6 | 103596 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/test-finished-1.png | 4cf5e7d99643f4f4539f33af42672656981db0ab33b84f9772f0da5522bb07d6 | 22574 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/trace.zip | 25f801f326ba6a0f553a1bae94a19c9e0d8444754c3d791ffd72979351aad5bd | 242913 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/video.webm | 746f59a500e7cde235dee97f2566392ddc49033868dfd2d2e86238e35341eaad | 25500 |
| test-results/typescript.log | df7488501d881e195eefa67f34b067f2ec603307d342f9ac57063a1be9542311 | 125 |
