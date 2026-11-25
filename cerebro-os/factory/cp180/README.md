# CP180 — bounded canary binding (LAB only)

The historic CP168 request remains the default. CP180-PRIVATE-PAIR-001 is an explicit allowlisted configuration, never taken from an external request. Use separate durable state; reject historic state, do not reset or retry an ambiguous reservation. Rollback: restore the previous candidate commit and preserve all state. This code is not cloud deployment, independent key custody, production authorization or live CP131 certification.

Run Node 22: `node --test cerebro-os/factory/cp177/*.test.mjs cerebro-os/factory/cp178/*.test.mjs cerebro-os/factory/cp180/*.test.mjs`.
