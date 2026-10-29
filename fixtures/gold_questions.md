# Gold questions (synthetic fixtures)

Fictional data from `make_fixtures.py`. A pass means the answer has the expected content AND
cites turn IDs that exist and say what's claimed. The work-machine POC needs its own 5,
written from meetings you already know the answers to.

Source IDs: `2026-09-08-chatbot-requirements-sync` (REQ), `2026-09-15-kt-customer-bi-pipeline` (KT),
`2026-09-22-chatbot-sprint-review` (REV), `2026-10-06-data-platform-standup` (STD).

## 1. What did John Doe say the chatbot's features and integrations should be, and did any of it change?
- Features: order status (REQ#t002), invoice history (REQ#t003), human handoff (REQ#t004).
- Integrations: lives in Teams, opens ServiceNow tickets on handoff (REQ#t006).
- Salesforce: excluded from v1 on 9/8 (REQ#t008), **reversed** on 9/22 to route handoffs to the account manager (REV#t003, REV#t004). Demo stays on the 30th without Salesforce (REV#t009). ServiceNow unchanged (REV#t011).
- Must surface the reversal, not pick one version silently.

## 2. Where is customer BI calculated, and what calls it or depends on it?
- `Reporting.usp_CalcCustomerBI` (KT#t002); reads Sales.Invoices/InvoiceLines/Customers, writes `Reporting.CustomerBISnapshot`.
- Called by `Reporting.usp_RefreshBIDaily`, nightly SQL Agent job at 2 AM (KT#t004).
- Downstream: `Reporting.vw_CustomerBI` reads the snapshot (KT#t006); `Integration.usp_ExportBIFeed` reads the view via **dynamic SQL** (KT#t008), flagged dynamic in the KB edges.
- The chatbot does NOT depend on it; it reads Sales.Invoices directly (STD#t004).

## 3. Why was the BI calculation moved out of the view?
- The view timed out as invoice volume grew, back in 2024 (KT#t006).

## 4. What action items exist, and who owns them?
- Marcus Lee: chatbot demo by September 30 (REQ#t012).
- Marcus Lee: Salesforce scoping doc by October 3 (REV#t007).
- Sam Rivera: flag the export feed's missing owner (KT#t011).
- Lena Ortiz: write up how the export feed works by October 17 (STD#t007).

## 5. Who owns the BI export feed?
- Unknown as of 9/15: previous owner Dave left (KT#t010).
- Lena Ortiz took ownership on 10/6 (STD#t007). The answer must give both, dated.
