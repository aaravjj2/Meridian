# Milestone Manifest

## Objective
Truth-tightening audit pass to align code, docs, validation gates, and deployment narrative.

## Scope
- Repository truth-tightening alignment pass.

## Metadata
- Generated at (UTC): 2026-04-04T19-43-57Z
- Git SHA: 7b7f2cc88fe6cf27b006cba139ecb3ebcf29a1a7
- Git branch: main
- Git dirty: False
- Harness summary: artifacts/harness/2026-04-04T19-42-45Z/summary.json

## Exact Commands Run
```bash
npm run tsc
npm run vitest -- --reporter=json --outputFile /home/aarav/Aarav/Meridian/artifacts/harness/2026-04-04T19-42-45Z/vitest-report.json
/home/aarav/Aarav/Meridian/.venv/bin/python -m pytest -q --junitxml /home/aarav/Aarav/Meridian/artifacts/harness/2026-04-04T19-42-45Z/pytest-report.xml
npm run playwright -- --reporter=json
```

## Exact Results
- all_green: True
- test_layers_green: True
- typescript: exit=0, passed=None, failed=0, skipped=0, retries=0
- frontend_unit: exit=0, passed=12, failed=0, skipped=0, retries=0
- backend_unit: exit=0, passed=51, failed=0, skipped=0, retries=0
- e2e: exit=0, passed=6, failed=0, skipped=0, retries=0
- determinism_signature_sha256: 8c70dc657ec11b8a88859ffb44280f5d0462ead5950c59e61a9fb50270dee4fc

## Root Causes If Fixes Were Needed
- None in this run.

## File Inventory
- README.md (380 bytes)
- TOUR.webm (180617 bytes)
- deployment/ci.yml (797 bytes)
- deployment/vercel.json (398 bytes)
- manifest.json (15070 bytes)
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
- test-results/e2e.log (14203 bytes)
- test-results/frontend_unit.log (622 bytes)
- test-results/harness-summary.json (2727 bytes)
- test-results/playwright/.last-run.json (45 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/test-finished-1.png (286554 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/trace.zip (643374 bytes)
- test-results/playwright/test_methodology-methodology-page-renders/video.webm (48436 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/test-finished-1.png (39415 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/trace.zip (326669 bytes)
- test-results/playwright/test_regime-regime-strip-renders-all-dimensions/video.webm (60632 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/test-finished-1.png (71459 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/trace.zip (3381477 bytes)
- test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/video.webm (369876 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/test-finished-1.png (199876 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/trace.zip (810135 bytes)
- test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/video.webm (88043 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/test-finished-1.png (39398 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/trace.zip (350141 bytes)
- test-results/playwright/test_smoke-smoke-homepage-chrome-renders/video.webm (60174 bytes)
- test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/test-finished-1.png (52673 bytes)
- test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/trace.zip (5396289 bytes)
- test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/video.webm (594288 bytes)
- test-results/typescript.log (126 bytes)

## Known Limitations
- Deployment reachability is not actively probed by this script.

## Current Deployment Status
Vercel config present; frontend rewrite target configured via MERIDIAN_API_BASE_URL=https://meridian-api.railway.app.

## SHA256 Checksums
| File | SHA256 | Size (bytes) |
|---|---|---:|
| README.md | 1053ac86e34c092db51e4f347cc03f041aa5ef1f865fe5c7a06721199d6a4403 | 380 |
| TOUR.webm | 3cd944f5c4941200432c7c971099d8e3bc06dfc86943aa0d3bd3b088d59379ff | 180617 |
| deployment/ci.yml | 558604a54fb0eb4e4af61028bf43712e258460eded58a3d26d293e321e289a94 | 797 |
| deployment/vercel.json | 9b5e79d0c68b91c7c37351be091f0c0614f5be110ae3a724aa41cf1d60644dd6 | 398 |
| manifest.json | 77c1335fbbdbae8aff5e34e19bce0a9a5077b0a1c59d67c712583dd97d75006a | 15070 |
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
| test-results/backend_unit.log | d7fecd335baf00ee89ed5803a9e896147db1d704d131cb263f11198a30bb4cce | 298 |
| test-results/e2e.log | a849079692ce7ef9f3be4e2d4e15cbe194153cf464280d0a1366335a371468ae | 14203 |
| test-results/frontend_unit.log | e8370f7aa68a892d51a45cc7763bf18e90ca4ee52e19959949abe27b301500ef | 622 |
| test-results/harness-summary.json | ef050389c71966b7e5b7807da9df9c81410810362629e5d75533fa947d6355e0 | 2727 |
| test-results/playwright/.last-run.json | 91d1c43004802cd49950d78eb11c8fa7d05da8ffffe219a8b13b2f561bc00903 | 45 |
| test-results/playwright/test_methodology-methodology-page-renders/test-finished-1.png | 22554ebe54a8f6d532110cca18660301b077cdffb3c7d800fc402110a76690d6 | 286554 |
| test-results/playwright/test_methodology-methodology-page-renders/trace.zip | c4b6fd558df3ed45934e41c8f021b079754545f05029e263c534d0813e9f3df2 | 643374 |
| test-results/playwright/test_methodology-methodology-page-renders/video.webm | 32718998a391490011e229a0ca264ff43c2b8b5308ea150ff7f5cf923df553c9 | 48436 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/test-finished-1.png | f732ce7fd11dd03319cc28f358d53e2ca830035ff537efbb1805fbacccc1b3cf | 39415 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/trace.zip | ecccacc1a2adac317a2bded96d04955e6d054172730db256d201b750685147f4 | 326669 |
| test-results/playwright/test_regime-regime-strip-renders-all-dimensions/video.webm | d6d2deebb3d34b08f387b40b43c28a662031b7d26d684eca84e8d0085f54f235 | 60632 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/test-finished-1.png | 2e87fd62305849286572e4adca7686343ec3e0d5edbc16deba89aaa3acd4e4d6 | 71459 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/trace.zip | 54cae1fe4ab2e7685dc2ec392b998bfa011a1e25f9846ab787668b5c58dacc12 | 3381477 |
| test-results/playwright/test_research_flow-research-flow-query-to-complete-brief/video.webm | 387055cb2e0b4267fd9578aa36afb0642fdae3ac2a677beee92510e21e020360 | 369876 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/test-finished-1.png | 7fc866c74ebeca97486511e66e835214152a5a18e828bc69be4a2ca93090b3e9 | 199876 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/trace.zip | f3275bd12f27f1b3191d5fccb07b5599458dd6da1b231e2d7cb617031bb79de2 | 810135 |
| test-results/playwright/test_screener-screener-loads-sorts-filters-opens-drawer/video.webm | 6ed29dd29196a0c639dca282fc6570b3ce833c77002c4535f63349d912bdd9c5 | 88043 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/test-finished-1.png | 9810c1c3c851733ab856dd68dd7a70257b5f45713b3ac65798af418429f6a6d0 | 39398 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/trace.zip | 4e563843d5ccedd4c9d915a10328d45c583187388611ae01ed290d518f7e65e0 | 350141 |
| test-results/playwright/test_smoke-smoke-homepage-chrome-renders/video.webm | 05872cd8859709efadebc1d1d3165641a9d304df89aec4009a7943e0b0bf7b6d | 60174 |
| test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/test-finished-1.png | 334351b0e02af0d75f9f6416cc4285d9ce5e282a13c1c615b8bdeea2b290259a | 52673 |
| test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/trace.zip | 4af73dd32eaad863137b7ed00e9ac63e0c776f9bf36cdb5400d39d5f27dbc1fa | 5396289 |
| test-results/playwright/test_workspace_persistence-9f535-tegrity-export-and-continue/video.webm | b050ed6c59a3dcac0d9714ad6fd69f6ed2338d1588b8d087d4914b14222dff9d | 594288 |
| test-results/typescript.log | a2e5b34914a7ba10ef8ca37852de53a05b8ac0a735506d4e55af30b3a30eba4e | 126 |
