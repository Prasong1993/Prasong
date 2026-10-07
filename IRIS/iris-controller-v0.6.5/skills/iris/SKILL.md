---
name: iris
description: Operate IRIS with evidence-first five-step gated execution and persistent error/checkpoint/audit records via MCP tools.
---
# IRIS — Evidence-First Five-Step Controller
Use the MCP tools; never simulate execution. If runtime is unavailable report RUNTIME_UNPROVEN.
For each step: CHECK → DO → VERIFY. Never advance until the current step is PASSED.
Five steps: 1 แนวคิด 2 ออกแบบ 3 ทำงานจริง 4 ส่งผล 5 ตรวจสอบบนพื้นที่ ChatGPT.
Delivery requires all five latest steps PASSED, final_verify VERIFIED, and work status DELIVERED.
Required tools: health, create_work, run_step, final_verify, get_work_status, add_evidence, list_evidence.
Failures must remain in errors, checkpoints and audit records.
