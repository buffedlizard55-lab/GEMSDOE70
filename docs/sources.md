# Verified Sources, Checksums & Provenance Ledger (`GEMSDOE70`)

Every dataset file, vendored code module, cross-repository GeoTIFF, peer-reviewed geoscience reference, and public agency source used in `GEMSDOE70` is catalogued below with its exact verification method and honest session reachability status.

---

## 1. Locally Verified Checksummed Inputs & Shared Code (`100%` SHA-256 Verified on Disk)

| Artifact / Source ID | Local Path / Upstream Origin | Verified Checksum / Scope | Verification Status |
|---|---|---|---|
| **Competition Reference Grid (`sample_submission.tif`)** | `data/sample_submission.tif` & `data/bridge/sample_submission.tif` | `SHA256: b4853eb6b7638eb37dc5cc2b10862b9efda749e7be62d2fb104120001e3159b1` · `EPSG:32611`, `3730×3292`, `5,167,373` finite footprint cells | **VERIFIED ON DISK (`100%` bit-exact)** |
| **Public Mapped Fault Catalogue (`existing_faults.tif`)** | `data/existing_faults.tif` & `data/bridge/existing_faults.tif` | `SHA256: d5ec20d7160fb3b18a2125413283123b120e37bf6acfe072a1ca5299546722df` · `60,988` positive fault pixels | **VERIFIED ON DISK (`100%` bit-exact)** |
| **19-Band Geophysical & DEM Stack (`training_features.tif` + `.xml`)** | Restored via `scripts/restore_data.py` from `codeload.github.com` mirror pins (`evidence/data_receipt.json`) | `16 / 16` files verified against pinned `SHA-256` digests (`DEM 10m`, `LiDAR 1m coverage/derivs`, `CBA gravity`, `RTP mag`, `MT conductivity`, `GPS strain`, `heatflow`) | **VERIFIED ON DISK (`16 / 16` SHA-256 match)** |
| **USGS SGMC Bedrock Geology Contacts (`DS-1052`) & GDR-1391 Thermal Tables** | `data/` (`evidence/data_receipt.json`) | Verified local vector/raster layers (`thermal springs`, `2m temperature probes`, `paleo-geothermal sinter/travertine`, `SGMC fault/lithologic contacts`) | **VERIFIED ON DISK (`SHA-256` match)** |
| **Shared Evaluation & Packaging Template (`vendor/gems57`)** | `buffedlizard55-lab/57GEMSDOE` @ commit `3202471` (`registry/template_pin.json`) | `evaluate_holdout.py`, `holdout.py`, `submission_writer.py`, `uniqueness.py`, `emit.py`, `grid.py` (`8/8` files byte-pinned) | **VERIFIED ON DISK (`8 / 8` SHA-256 & git-blob match)** |
| **Live Organization Registry Scan (`84` Repos, `931` Unique Rasters)** | `.cache/live_registry_index.json` + `.cache/registry_rasters/*.tif` + `evidence/full_931_registry_audit_rows.json.gz` | `84 / 84` accessible `buffedlizard55-lab` repositories scanned via `codeload.github.com`; all `931` unique GeoTIFFs downloaded & SHA-256 verified (`0` errors) | **VERIFIED ON DISK (`931 / 931` SHA-256 match)** |
| **Pre-Registration Hypothesis Lock (`docs/hypotheses.md`)** | `docs/hypotheses.md` (`evidence/experiment_manifest.json`) | `SHA256: 6b9a85b5a0309a6d1aab0f03ed69ee21755ee9943bece89b9b842693c2f6aa65` | **VERIFIED ON DISK (`100%` immutable hash)** |
| **Promoted Candidate Bundle (`H70-3`)** | `docs/downloads/gemsdoe70-h70-3-dual-expert-submodular-20261020T223000Z.{tif,zip,json}` | `.tif SHA256: e035d29e3c4e8a0dabd807b6bedfc9373216fa03f523b441cba5113420864650` · `.zip SHA256: fbc36dd38ec3c88a8bc7697217348efcb75e91451260c5dbecf7d0233a95f595` | **VERIFIED ON DISK (`PASS` all validator gates)** |

---

## 2. External Agency Portals & Scientific Literature References

> **Outbound Sandbox Scope Disclosure (`IR-70-SANDBOX-NETWORK-SCOPE`):** This execution environment permits outbound HTTPS strictly to `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, and `files.pythonhosted.org`. External non-GitHub URLs below are cited accurately for provenance and human follow-up; we explicitly do **not** claim live HTTP retrieval of blocked non-GitHub domains inside this sandbox.

| Domain / Reference | Canonical URL / Citation | Role in `GEMSDOE70` | Session Network Status |
|---|---|---|---|
| **DrivenData DOE GEMS Competition Overview** | `https://www.drivendata.org/competitions/306/competition-doe-gems/` | Official competition rules, weekly slot policy, upload portal | Outbound firewall-restricted in sandbox; check rules before uploading |
| **DrivenData Problem Description & Metric Spec** | `https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/` | `EPSG:32611` grid spec & `DTI(alpha=0.2, beta=0.8, 300 m)` metric definition (mirrored in `evidence/official-reference-excerpts.txt`) | Mirrored excerpt verified locally; live domain firewall-restricted |
| **USGS GeoDAWN Great Basin Potential-Field Compilation** | `https://www.sciencebase.gov/catalog/` (mirrored report text in `evidence/mirrored_geodawn_report.txt`) | Provenance for aeromagnetic RTP, isostatic residual gravity, upward continuation & vertical derivative bands | Mirrored report text verified locally |
| **DOE Geothermal Data Repository (`GDR-1391` INGENIOUS)** | `https://gdr.openei.org/submissions/1391` | Great Basin play-fairway 2m temperature probes, thermal springs, paleo-sinter/travertine, Quaternary fault attributes | Local checksummed mirrors verified in `data/` |
| **USGS SGMC State Geologic Map Compilation (`DS-1052`)** | `https://pubs.usgs.gov/ds/1052/` | Pre-Quaternary bedrock fault traces & lithologic contacts for reactivation scoring | Local checksummed mirror verified in `data/` |
| **Gallardo & Meju (2003, *Geophysics* 68(3))** | `t(x) = grad(f_1) × grad(f_2)` structural cross-gradient joint inversion | Theoretical foundation for our 3-pair gravity × magnetic × MT structural cross-gradient alignment features | Peer-reviewed geophysical method |
| **Archibald, Boschetti & Holden (1999, *Geophysics* 64(1))** | Multi-scale upward-continuation horizontal gradient "geophysical worms" | Theoretical foundation for basement fault dip & depth persistence features (`worm_mag`, `worm_grav`) | Peer-reviewed geophysical method |
| **Perron & Royden (2013, *ESPL* 38(6))** | Integral drainage divide $\chi$ and normalized steepness $k_{sn}$ analysis | Theoretical foundation for transient footwall uplift / range-interior fault knickzone features | Peer-reviewed tectonic geomorphology method |
