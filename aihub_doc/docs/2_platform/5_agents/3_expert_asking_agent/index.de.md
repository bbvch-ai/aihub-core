---
title: Experten-Anfrage-Agent
source_sha: de4bdcf83610f7d31d003806be3215cc1dba2e4a5c42b62109074fd0fdb47511
---

# Die Experten-Agenten: Verbindung von KI und menschlichem Wissen

Was passiert, wenn eine KI die Antwort auf eine kritische Geschäftsfrage nicht kennt? In den meisten Systemen rät sie
entweder (halluziniert) oder gibt auf. Der Swiss AI Hub bietet eine leistungsstarke Alternative mit den
**Experten-Agenten** – einem spezialisierten Agentenpaar, das entwickelt wurde, um die Lücke zwischen den Fähigkeiten
der KI und dem menschlichen Fachwissen Ihrer Organisation nahtlos zu überbrücken.

Dieses innovative System stellt sicher, dass Benutzer stets präzise und vertrauenswürdige Antworten erhalten. Wenn die
KI an die Grenzen ihres Wissens stößt, versagt sie nicht; stattdessen leitet sie die Frage intelligent an einen
benannten menschlichen Experten weiter und lernt aus dessen Antwort.

## Die Herausforderung: Wenn das Wissen der KI nicht ausreicht

Eine KI ist nur so gut wie die Informationen, auf die sie zugreifen kann. Selbst mit einer umfassenden Wissensdatenbank
wird es immer neue, nuancierte oder undokumentierte Fragen geben. Hier wird das Risiko der KI-Halluzination zu einem
großen Problem für Unternehmen. Eine falsche Antwort ist oft schlimmer als gar keine Antwort.

Die Experten-Agenten wurden entwickelt, um dieses Problem zu lösen, indem sie einen zuverlässigen, auditierbaren Prozess
für die Mensch-KI-Zusammenarbeit schaffen.

## Ein Zwei-Agenten-System für nahtlose Zusammenarbeit

Die Experten-Agenten sind kein einzelner Agent, sondern ein Paar von Spezialisten, die zusammenarbeiten:

1. **Der Expert Grounded Agent**: Dies ist der Agent, mit dem Ihre Benutzer interagieren. Seine primäre Anweisung ist
   es, **niemals zu raten**. Er versucht zuerst, eine Frage mithilfe seines verfügbaren Wissens zu beantworten. Wenn er
   feststellt, dass die Informationen unzureichend sind, um eine vollständige und genaue Antwort zu geben, wird er nicht
   fortfahren. Stattdessen wird er den Benutzer transparent informieren und, mit dessen Zustimmung, die Anfrage
   eskalieren.

2. **Der Expert Asking Agent**: Dieser Agent arbeitet im Hintergrund. Sobald der Benutzer seine Zustimmung gibt, nimmt
   er die Frage auf und leitet sie an die richtigen menschlichen Experten in Ihrer Organisation weiter. Er verwaltet den
   gesamten Konsultationsprozess und stellt sicher, dass das Wissen des Experten effektiv erfasst wird.

Diese Aufgabenteilung schafft einen robusten und zuverlässigen Workflow.

### Der Experten-Konsultations-Workflow in Aktion

Das folgende Diagramm veranschaulicht den vollständigen Ablauf, von der ersten Frage des Benutzers bis zur endgültigen,
vom Experten verifizierten Antwort und der Erfassung neuen Wissens.

```mermaid
sequenceDiagram
    participant User
    participant GroundedAgent as Expert Grounded Agent
    participant KnowledgeBase as Knowledge Base
    participant AskingAgent as Expert Asking Agent
    participant Slack
    participant HumanExpert as Human Expert

    User->>+GroundedAgent: Asks a complex question
    GroundedAgent->>+KnowledgeBase: Searches for relevant context
    KnowledgeBase-->>-GroundedAgent: Returns insufficient/no context
    
    GroundedAgent-->>User: "I don't know. May I ask an expert?"
    User->>+GroundedAgent: "Yes, please."
    
    GroundedAgent->>+AskingAgent: Delegates question (Agent-in-the-Loop)
    Note right of AskingAgent: Manages the human interaction
    
    AskingAgent->>+Slack: Posts question to expert channel
    Slack->>+HumanExpert: Notifies expert of the question
    
    HumanExpert->>+Slack: Provides answer in thread
    Slack-->>-AskingAgent: Forwards expert's response
    
    Note over AskingAgent: Evaluates response for completeness.<br/>(Optional: Asks follow-up questions if needed)

    AskingAgent->>+KnowledgeBase: Saves expert's answer as a new<br/>knowledge snippet for future use
    KnowledgeBase-->>-AskingAgent: Confirms knowledge is stored
    
    AskingAgent-->>-GroundedAgent: Returns the final, verified answer
    GroundedAgent-->>-User: Delivers the expert's answer
```

::: details Ablauf im Detail
1. **Erste Anfrage und Suche**: Der Benutzer stellt dem **Expert Grounded Agent** eine Frage. Der Agent konsultiert
   zuerst die **Wissensdatenbank**, um eine Antwort zu finden.
2. **Wissenslücke identifiziert**: Die Suche liefert unzureichende Informationen. Der Agent erkennt, dass er nicht
   zuverlässig antworten kann.
3. **Zustimmung des Benutzers zur Eskalation**: Der Agent informiert den Benutzer transparent über die Wissenslücke und
   bittet um Erlaubnis, einen menschlichen Experten zu konsultieren.
4. **Delegation an Spezialisten-Agenten**: Sobald der Benutzer zustimmt, delegiert der Grounded Agent die Aufgabe an den
   **Expert Asking Agent**.
5. **Expertenkonsultation in Slack**: Der Asking Agent veröffentlicht die Frage in einem vorkonfigurierten
   **Slack-Kanal** und benachrichtigt den benannten **menschlichen Experten**.
6. **Wissenserfassung und Speicherung**: Der Experte gibt eine Antwort in Slack. Der Asking Agent erfasst diese Antwort,
   verarbeitet sie in ein strukturiertes Format und speichert sie als neues, permanentes Wissenselement in der
   **Wissensdatenbank** ab.
7. **Antwortlieferung**: Die verifizierte Antwort wird vom Asking Agent zurück an den Grounded Agent übergeben, der sie
   dann dem Benutzer liefert.

Wenn das nächste Mal jemand eine ähnliche Frage stellt, findet der Agent das neu erfasste Expertenwissen in seiner
Wissensdatenbank und kann sofort antworten, ohne erneut eskalieren zu müssen.
:::

## Warum dies ein Game-Changer für Ihr Unternehmen ist

Dieses Human-in-the-Loop-Muster liefert tiefgreifenden Wert, der über die Beantwortung einer einzelnen Frage hinausgeht.

- **Garantierte Genauigkeit und Vertrauen**: Indem sie sich weigern zu antworten, wenn sie unsicher sind, eliminieren
  die Agenten das Risiko von Halluzinationen. Benutzer lernen der KI zu vertrauen, weil sie wissen, dass ihre Antworten
  stets auf verifizierten Informationen basieren, sei es aus einem Dokument oder von einem menschlichen Experten.
- **Erzeugt eine lebendige Wissensdatenbank**: Das wertvollste Wissen Ihrer Organisation befindet sich oft in den Köpfen
  Ihrer Experten. Dieses System bietet eine reibungslose Möglichkeit, dieses implizite Wissen zu erfassen und in ein
  durchsuchbares, wiederverwendbares digitales Asset umzuwandeln. Jede Expertenkonsultation macht Ihre KI aktiv
  intelligenter.
- **Experten arbeiten in ihrem gewohnten Flow**: Ihre Fachexperten müssen kein neues Tool lernen. Sie steuern ihr Wissen
  in der Umgebung bei, in der sie bereits arbeiten – **Slack**. Die KI erledigt den Rest.
- **Intelligente Nachfrage**: Wenn die anfängliche Antwort eines Experten kurz oder unvollständig ist, ist der Expert
  Asking Agent intelligent genug, dies zu erkennen. Er kann automatisch klärende Nachfragen generieren und stellen, bis
  er eine umfassende Antwort hat, wodurch sichergestellt wird, dass das erfasste Wissen vollständig und wertvoll ist.
- **Skalierbares Fachwissen**: Dieses System vervielfacht die Wirkung Ihrer Experten. Sie beantworten eine Frage einmal,
  und dieses Wissen steht dann der gesamten Organisation über die KI dauerhaft zur Verfügung. Dies entlastet die Zeit
  Ihrer Experten, damit sie sich auf die wirklich neuen und komplexen Herausforderungen konzentrieren können.

Durch die Implementierung der Experten-Agenten deployen Sie nicht nur einen KI-Assistenten; Sie bauen ein dynamisches,
sich selbst verbesserndes organisatorisches Gehirn auf, das kontinuierlich von Ihren sachkundigsten Mitarbeitern lernt.
