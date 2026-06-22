# Model Context Protocol (MCP)

The Model Context Protocol is an open standard that lets applications expose
tools, resources, and prompts to large language model clients in a uniform way.
A server advertises a set of capabilities; a client (for example Claude Desktop
or a custom agent) discovers them at runtime and calls them on demand.

An MCP server typically communicates over stdio or HTTP. Each tool has a name,
a JSON schema for its arguments, and a handler. Because the contract is
declarative, the same server can be reused across many different clients without
any client-side changes.

For a Forward Deployed Engineer, MCP is the integration seam: it is how you
connect a customer's private systems (a search index, a database, an internal
API) to Claude without leaking credentials into prompts or hard-coding logic
into the model. You ship the server, the customer keeps their data, and Claude
gets typed, auditable access to exactly the capabilities you chose to expose.
