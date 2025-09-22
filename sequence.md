``` mermaid
graph TD
    MasterAgent --> WebResearcher;
    MasterAgent --> KeywordGenerator;
    WebResearcher --> MasterAgent;
    KeywordGenerator --> MasterAgent;
    MasterAgent --> PostGenerator;
    PostGenerator --> MasterAgent;
    MasterAgent --> VoiceDialogGenerator;
    VoiceDialogGenerator --> MasterAgent;
```