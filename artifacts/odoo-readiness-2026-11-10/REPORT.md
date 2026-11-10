# Arab Insurance Odoo.sh readiness — 10 November 2026

The required insurance addons are installed and the core ORM workflow passes. The environment is **not yet fully signed off**: the reference regulatory workbook is absent, browser verification was resource-limited, and the applied source changes have not been committed to the Odoo.sh repository.

## Confirmed target

| Item | Value |
| --- | --- |
| Branch / build | `19_10_26` / `40105896`, explicitly confirmed by the user |
| URL | https://odolution-com-arab-insurance-19-10-26-40105896.dev.odoo.com/odoo |
| Database | `odolution-com-arab-insurance-19-10-26-40105896` |
| SSH user / service user | `40105896` / `odoo` |
| Host | `sapp72` |
| Odoo | 19 Enterprise; community and Enterprise addon paths are mounted |
| Custom source | `/home/odoo/src/user` |
| Source repository | `Odolution-com/arab-insurance`, branch `19_10_26` |
| Starting commit | `ee8eb1dd137ac85fefe53fdf0ee7d8e1aaf0cfee` |
| Initial working tree | Clean |
| Odoo config | `/home/odoo/.config/odoo/odoo.conf` |
| Services | Odoo.sh socket-activated HTTP and managed cron; PostgreSQL reachable through platform connection settings |
| Remote evidence directory | `/home/odoo/tmp/operational-readiness-20261110` |

The local workspace is a different repository, `mfkcomstar/Arab-insurance`, on `main`. Its source was not overwritten with the other repository's addon tree. The readiness changes are preserved here as a patch.

The supplied DevGrid `main` filesystem/database were not accessible through the provided Odoo.sh connection. Comparison used the supplied reference module inventory, not a live diff of its 386 uncommitted/untracked entries. No commands changed the reference `main` database.

## Module operations

Initially, 110 standard modules were installed and all 39 custom addons were uninstalled. All 35 reference-installed custom addons are now installed. Odoo also installed `base_automation`; Kuwait setup added `l10n_kw` and `l10n_gcc_invoice`. Final installed count: **148**. No modules are awaiting installation, upgrade, or removal.

Installed custom addons:

```text
aib_accounting                 aib_base
aib_broker_coordination        aib_business_profile
aib_claim                      aib_collection
aib_commission                 aib_commission_engine
aib_comparison                 aib_contact_360
aib_crm                        aib_dashboard
aib_dashboard_pro              aib_direct_policy
aib_document_checklist         aib_market
aib_policy                     aib_policy_endorsement
aib_policy_worksheet_export     aib_quotation
aib_regulatory_reporting       aib_renewal
aib_reports                    aib_workflow_activity
arab_insurance_crm_documents   arab_insurance_website
contact_relationship_status    muk_web_appsbar
muk_web_chatter                muk_web_colors
muk_web_dialog                 muk_web_group
muk_web_refresh                muk_web_theme
odoo_board_management
```

All declared addon dependencies were available. Module loading and tests exercised the installed Python dependencies, including workbook libraries. No Python or system package installations were required.

The optional addons `aib_client_360_view`, `aib_ui_polish`, `home_theme`, and `sd_transport_management` remain uninstalled. No addons were uninstalled. Two unrelated platform addons, `iot_box_image` and `iot_drivers`, are marked uninstallable; neither is an insurance dependency. The difference from the reference's reported 218 installed modules is not treated as an instruction to install unrelated standard apps.

## Configuration and fixes

The user explicitly requested Kuwait/KWD setup. The company is now named Arab Insurance, country Kuwait, currency KWD, with Odoo's Kuwait chart. There were no accounting entries or policies when the unused generic chart was replaced through Odoo's chart-loading API. A pre-change account/journal JSON snapshot is retained remotely; this is not a recoverable database backup.

Configured:

- Premium Statements general journal `PREM`.
- Separate off-balance client account `990101` and insurer account `990102`.
- Commission income account `400190` and service product `AIB-COMMISSION`.
- Sales journal and Bank journal for commission invoicing and collections.
- Bank inbound manual payment method with outstanding-receipts account `100190`.
- AIB accounting integration enabled; invoice trigger set to commission receivable; automatic draft creation enabled and automatic posting disabled.
- Regulatory configuration currency KWD; enterprise brokerage workflow retained.
- Existing administrator granted Insurance Administrator access; read access and views verified as that user.

Source fixes:

1. Restore automatic commission invoicing for the configured receivable trigger and align its lifecycle with the commission engine.
2. Block collection payments without an outstanding account or a posted payment journal entry.
3. Infer CRM/Market policy source when quotation/comparison records are supplied.
4. Preserve explicit quoted/imported premium totals instead of overwriting them with regulatory subtotals.

Four affected module manifests were bumped from `19.0.1.0.0` to `19.0.1.0.1` and upgraded. Test fixtures were aligned with the existing manual RFQ composer, required quote references, receipt-amount input, payment-account requirements, automatic eligibility, and JSON string keys. No automatic external RFQ sending was introduced. New regressions check posted entries, 600/300 partial payment, full remaining settlement, and clean rejection of a missing outstanding account. No custom SQL migration was used.

`readiness-changes.patch` contains all 15 changed source/test/manifest files. `git diff --check` passed. Original versions are retained remotely under `source-before-fixes`. **These changes are applied in the current build but are uncommitted and unpushed. Commit/apply the patch to the correct Odoo.sh source branch before a rebuild, or the fixes can be lost.**

## Verification

| Check | Result |
| --- | --- |
| Initial business suite | 228 tests: 16 failures and 23 errors |
| Latest complete business suite | 230 tests: 229 passed, one legacy fixture error |
| Corrected commission suite | All 12 tests passed in the targeted rerun |
| UI backend/session targeted run | 19 of 20 passed; remaining JSON-key test corrected and passed separately |
| Previously failing named tests | All 42 have a later passing result; see `failure-resolution.json` |
| Browser HOOT test | Incomplete: container thread limit and `net::ERR_EMPTY_RESPONSE`; test process stopped |
| Actual ORM workflow | Passed and committed as labelled development test records |
| Administrator views | 22 list/form views and read access passed |
| Public website and login | HTTP 200; backend correctly redirects unauthenticated users to login |
| Expected database | Name present in returned HTML and confirmed by database query |
| PostgreSQL | Query succeeds |
| Fresh Odoo worker | Loaded all 148 modules successfully |

The completed test runs collectively cover the business suite and targeted UI backend/session checks. There was no later single combined run claiming all checks passed. Per-run summaries, every failure name, and tracebacks are in `test-history.json`.

The headless browser test exhausted the container's thread allowance. A concurrent attachment garbage-collection job recorded a lock timeout during that test. Subsequent fresh worker startup and URL checks recorded no new errors. The long development catchall address also produces reply-to-length warnings; email deliverability was not certified.

The HTTP/cron restart utility reported no active workers at the time of invocation. The following URL requests woke a fresh socket-activated HTTP worker, and cron activity is visible in runtime logs. PostgreSQL is platform managed, not a local service restarted by this task.

## Retained real smoke-test evidence

The smoke script commits only after all assertions pass. An earlier attempt failed on an incomplete test insurer contact and rolled back; it did not leave a duplicate payment. Test email created by the successful attempt was cancelled before commit.

| Record / balance | Verified value |
| --- | --- |
| Policy | `POL/2026/00372`, ID 408; insurer policy number `READINESS-20261110` |
| CRM / market / quotation / comparison IDs | 149 / 207 / 286 / 118 |
| Premium | 6,000 KWD |
| Confirmed client collection | 3,000 KWD, ID 38 |
| Client / insurer statement balances | +3,000 / -3,000 KWD on separate accounts |
| Commission | 600 KWD, ID 208 |
| Posted invoice | `INV/2026/00001`, ID 198, total 600 KWD |
| Payment | `PBNK1/2026/00001`, ID 15, amount 300 KWD |
| Payment entry | ID 199, posted |
| Invoice residual | 300 KWD, with receivable reconciliation |
| Payment operational state | `in_process`, as expected while using outstanding receipts |
| Renewal / claim / completed non-financial endorsement IDs | 44 / 53 / 58 |

The reference's `PAY00023` defect was not an existing transaction here: the target initially contained no payments or invoices. The target Bank method had the same missing-outstanding-account risk. It was configured, the collection path was guarded, and a real partial payment was verified without relying on payment status alone. The additional remaining-payment regression verified full settlement transactionally.

## Outstanding inputs and limitations

- Regulatory configuration ID 1 has **no workbook attachment**. Exports are explicitly pending in its notes. The user identified the reference workbook as `production and Collection (3).xlsx`, located at `/mnt/projects/m.faizan.khan-arab-insurance/main/production and Collection (3).xlsx`, reference attachment 3718. The user reports matching checksums; this task did not independently access either reference copy. Transfer, upload, validate sheet/insurer mappings, and confirm client approval before official use. Test-generated workbooks are not an approved replacement.
- Full browser verification remains incomplete because of the container resource limit. HTTP, session, ORM, access, and view checks passed.
- No recoverable database backup was created: `pg_dump` failed on platform-restricted `pg_settings`, and `backup.daily` was empty. A filestore archive, source originals, configuration snapshots, and module baseline exist remotely, but these do not replace a database backup. No uninstalls were performed.
- Live parity with the uncommitted DevGrid reference source cannot be established from the provided Odoo.sh access.
- Persist the source patch to the correct repository before rebuilding this Odoo.sh branch.

Final sign-off remains pending these items. The installed core insurance and accounting workflow is runnable in the current build.
