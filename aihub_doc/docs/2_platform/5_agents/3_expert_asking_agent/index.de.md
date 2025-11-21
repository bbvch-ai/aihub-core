---
title: Experte befragt Agenten
source_sha: 666416619d0a5599108200349ba605a7daf2d2be989e2b247b77f66fba389265
---

# Experte befragt Agenten

Wenn ein RAG-Agent eine Frage aus seiner Wissensdatenbank nicht beantworten kann, kann er die Anfrage an menschliche
Experten eskalieren. Die Expertenagenten implementieren diesen Eskalations-Workflow durch zwei spezialisierte Agenten,
die zusammenarbeiten.

## Architektur des Agentenpaars

Das System verwendet zwei Agenten:

Der Expert Grounded Agent interagiert mit Benutzern. Er durchsucht seine Wissensdatenbank nach Antworten. Wenn die
Informationen unzureichend sind, informiert er den Benutzer und bittet um Erlaubnis, die Frage an einen menschlichen
Experten zu eskalieren.

Der Expert Asking Agent verwaltet den Konsultationsprozess. Er stellt Fragen über Slack an Experten, erfasst deren
Antworten und speichert die Antworten in der Wissensdatenbank für zukünftige Anfragen.

## Workflow

```mermaid
sequenceDiagram
    participant User
    participant GroundedAgent as Expert Grounded Agent
    participant KnowledgeBase as Knowledge Base
    participant AskingAgent as Expert Asking Agent
    participant Slack
    participant HumanExpert as Human Expert

    User->>+GroundedAgent: Stellt eine komplexe Frage
    GroundedAgent->>+KnowledgeBase: Sucht nach relevantem Kontext
    KnowledgeBase-->>-GroundedAgent: Gibt unzureichenden/keinen Kontext zurück
    
    GroundedAgent-->>User: „Ich weiß es nicht. Darf ich einen Experten fragen?"
    User->>+GroundedAgent: „Ja, bitte."
    
    GroundedAgent->>+AskingAgent: Delegiert Frage (Agent-in-the-Loop)
    Note right of AskingAgent: Verwaltet die menschliche Interaktion
    
    AskingAgent->>+Slack: Stellt Frage im Expertenkanal
    Slack->>+HumanExpert: Benachrichtigt Experten über die Frage
    
    HumanExpert->>+Slack: Gibt Antwort im Thread
    Slack-->>-AskingAgent: Leitet Expertenantwort weiter
    
    Note over AskingAgent: Bewertet die Antwort auf Vollständigkeit.<br/>(Optional: Stellt bei Bedarf Folgefragen)

    AskingAgent->>+KnowledgeBase: Speichert die Expertenantwort als neues<br/>Wissensfragment für zukünftige Nutzung
    KnowledgeBase-->>-AskingAgent: Bestätigt, dass Wissen gespeichert ist
    
    AskingAgent-->>-GroundedAgent: Gibt die finale, verifizierte Antwort zurück
    GroundedAgent-->>-User: Liefert die Expertenantwort an den Benutzer
```

Das Sequenzdiagramm zeigt den vollständigen Konsultations-Workflow.

Der Benutzer stellt dem Expert Grounded Agent eine Frage. Der Agent durchsucht die Wissensdatenbank. Wenn die Suche
unzureichende Informationen liefert, informiert der Agent den Benutzer und bittet um Erlaubnis, einen Experten zu
konsultieren.

Mit Zustimmung des Benutzers delegiert der Grounded Agent an den Expert Asking Agent unter Verwendung des
Agent-in-the-Loop-Musters. Der Asking Agent stellt die Frage in einem konfigurierten Slack-Kanal und benachrichtigt den
benannten Experten.

Der Experte gibt eine Antwort im Slack-Thread. Der Asking Agent kann die Vollständigkeit der Antwort bewerten und bei
Bedarf Folgefragen stellen. Sobald er zufrieden ist, speichert er die Antwort in der Wissensdatenbank und gibt die
Antwort an den Grounded Agent zurück, der sie dem Benutzer übermittelt.

Zukünftige Anfragen zum gleichen Thema rufen die gespeicherte Expertenantwort aus der Wissensdatenbank ab, ohne eine
weitere Konsultation zu erfordern.

## Wissenserfassung

Jede Expertenkonsultation erweitert die Wissensdatenbank. Experten beantworten Fragen einmal, und ihre Antworten werden
für alle Benutzer durchsuchbar. Dies wandelt implizites Wissen in dokumentierte Informationen um, ohne dass Experten
zusätzliche Tools über ihren bestehenden Slack-Workspace hinaus verwenden müssen.

Der Asking Agent kann unvollständige Antworten erkennen und Folgefragen generieren, um sicherzustellen, dass das
erfasste Wissen für zukünftige Abfragen umfassend genug ist.
