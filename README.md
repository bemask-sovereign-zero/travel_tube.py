# 🛸 BEMASK // ALPHA TRAVEL TUBE (Sector 12)
**High-Speed Cash Drawer, Multi-POS & Fiscal RT Reconciliation Engine in Volatile RAM**

![Architecture](https://img.shields.io/badge/Architecture-Zero--Trust%20RAM--Only-10B981?style=for-the-badge)
![Ecosystem](https://img.shields.io/badge/BEMASK-Moonbase%20A.L.P.H.A.%20Sector%2012-F59E0B?style=for-the-badge)
![Stack](https://img.shields.io/badge/Python-Streamlit%20%7C%20Pandas%20%7C%20NumPy-38BDF8?style=for-the-badge)

---

## 🎯 Executive Overview
**Alpha Travel Tube** is a standalone, high-speed financial and fiscal reconciliation pod designed for hospitality, retail, and high-frequency cash businesses within the **BEMASK Sovereign Zero / Moonbase A.L.P.H.A.** ecosystem.

Operating strictly in **Volatile RAM (0 Bytes written to server disk)**, Travel Tube bridges the operational gap between physical cash drawers, multi-POS terminal histories, and official Telematic Cash Registers (*Registratore Telematico - RT*), protecting small business owners from accounting discrepancies and two-stage audit mismatches.

---

## ⚡ Core Capabilities (The 4 Operational Modules)

### 1. 🛡️ Real-Time Cash Drawer & Multi-POS Shield
* **Morning Float Calibration:** Tracks primary and secondary cash floats (*Fondo Cassa*) against live physical cash counts.
* **Two-Stage Audit Defense:** Calculates the exact theoretical cash balance down to the cent at any minute of the shift:
  $$\text{Expected Cash} = \text{Morning Float} + \text{RT Cash Sales} - \text{Documented Cash Outflows}$$
* **Multi-POS vs. Fiscal RT Collision Detector:** Cross-references cumulative transactions across **POS 1, POS 2, and Satispay/Apps** against Electronic RT totals, immediately flagging unprinted fiscal receipts or tender-type misclassifications before the end-of-day Z-closure.
* **Morning Restocking Verdict:** Computes the exact banknote amount to withdraw or replenish before opening the next morning.

### 2. 🧠 Semantic Merchandising Engine (`A–O` Parallel Ledger)
* **Automated Supplier Code & Synonym Mapping:** Translates heterogeneous supplier descriptions, abbreviations, and delivery note (*DDT*) codes into a standardized 13-bucket parallel accounting matrix (`[A]` through `[O]`).
* **Self-Learning Keyword Dictionary:** Automatically routes items (e.g., *Coffee Beans, Spirits/Beverages, Fresh Dairy, Ice/Consumables, Staff Advances, Owner Withdrawals*) and allows real-time custom keyword expansion.

### 3. ⚡ 3-Second Instant Cash Vouchers
* **One-Thumb Petty Cash Logging:** Instant timestamped justification for unreceipted cash outflows (supplier cash-on-delivery, staff advances, owner withdrawals, change adjustments) to keep the physical drawer permanently aligned.

### 4. 🖨️ Audit Defense Statement & JSON Bridge
* **Instant `.TXT` Reconciliation Report:** Generates a chronological, timestamped cash reconciliation statement ready for immediate inspection.
* **Universal `.JSON` Bridge:** Exports and imports encrypted session ledgers compatible with the **Alpha Main Mission** command hub.

---

## 🔒 Zero-Trust Volatile RAM Architecture
* **No Persistent Cloud Database:** All financial figures, receipt scans, and cash reconciliations exist exclusively in volatile session memory (`st.session_state`).
* **Local Sovereignty:** Data is saved solely to the owner's local device via `.JSON` or `.TXT` checkpoints and is permanently purged upon session termination.

---

## 🚀 Quick Deployment

### Requirements
```text
streamlit
pandas
numpy
