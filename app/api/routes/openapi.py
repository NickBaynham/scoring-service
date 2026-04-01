"""OpenAPI customization hooks and static metadata references."""

OPENAPI_TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Liveness and readiness probes.",
    },
    {
        "name": "Scoring jobs",
        "description": "Submit asynchronous credibility scoring jobs and poll status.",
    },
    {
        "name": "Documents",
        "description": "Register documents and retrieve aggregated scores.",
    },
]

CONTACT = {
    "name": "VerifiedSignal Platform",
    "email": "platform@example.com",
    "url": "https://example.com/support",
}
