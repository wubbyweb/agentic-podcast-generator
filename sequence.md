``` mermaid
graph TD
    A[Perplexity Research] --> B[MasterAgent]
    B --> C{Parallel Execution}
    C --> D[PostGenerator]
    C --> E[VoiceDialogGenerator]
    C --> F[KeywordGenerator]
    D --> G[Collect Results]
    E --> G
    F --> G
```