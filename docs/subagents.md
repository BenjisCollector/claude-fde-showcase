# Sub-Agents and Orchestration

A sub-agent is a scoped worker that handles one kind of task well. An
orchestrator is the coordinator that receives an incoming request, decides which
sub-agent should handle it, dispatches the work, and aggregates the results.

This division of labour matters in production. A single monolithic prompt that
tries to do everything tends to be brittle and hard to evaluate. Splitting the
work into specialised sub-agents gives you smaller, testable units, clearer
failure boundaries, and the ability to swap one worker's implementation without
touching the others.

Routing can be explicit (the caller names the task kind) or inferred (the
orchestrator classifies the request first). Either way, the orchestrator owns
error handling: an unknown task kind should fail loudly rather than silently
returning nothing. A Forward Deployed Engineer scales this pattern by starting
with deterministic stub workers, proving the routing and aggregation, and then
replacing individual workers with Claude-backed implementations one at a time.
