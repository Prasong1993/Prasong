# IRIS Controller 0.6.2

Evidence-first five-step execution controller.

## Five steps
1. แนวคิด
2. ออกแบบ
3. ทำงานจริง
4. ส่งผล
5. ตรวจสอบบนพื้นที่ ChatGPT

Each step uses CHECK → DO → VERIFY. Failure is retained with error/checkpoint, corrected/retried, and verified again. Delivery requires all five steps PASS and final verification VERIFIED.

## Runtime
Python / FastAPI / SQLite. The controller preserves evidence, errors, checkpoints, audit records and verifications.

## API
GET /, GET /health, GET /structure, POST /work, GET /work/{id}, POST /work/{id}/step/{1..5}, POST /work/{id}/verify, GET/POST /evidence.

The runtime proves controller behavior in its execution environment only; external production compatibility requires target-specific evidence.
