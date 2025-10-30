---
title: Benutzeroberfläche
source_sha: 4fd611e399aed3c360eaf2bd446d1320d79922f439c995b23cfe595030e6ccf8
---

# Die Plattform-Benutzeroberfläche

Die Benutzeroberfläche des Swiss AI Hub ist als integrierte Suite konzipiert, nicht als Sammlung separater Tools. Dieser
Ansatz spiegelt bekannte Produktivitätssoftware wie Microsoft Office oder Google Workspace wider, bei der verschiedene
Anwendungen für unterschiedliche Aufgaben in einer einzigen, einheitlichen Umgebung koexistieren.

Benutzer authentifizieren sich einmal, um auf eine kohärente Suite von KI-Diensten zuzugreifen. Ein gemeinsames
Navigationsframework und eine konsistente Designsprache über alle Funktionen hinweg reduzieren die Lernkurve und
eliminieren die Workflow-Unterbrechung, die bei fragmentierten Plattformen üblich ist. Dieses Design ermöglicht es den
Benutzern, sich auf ihre Arbeit zu konzentrieren und nicht darauf, die Navigation verschiedener Tools zu erlernen.

## Der Service-Katalog

Die Benutzeroberfläche bietet eine Reihe spezialisierter Dienste, die den gesamten Lebenszyklus von Unternehmens-KI
abdecken, von der Wissensverwaltung und Agentenentwicklung bis hin zur Prozessautomatisierung und -bewertung.

### Agentenverwaltung

Dies ist die zentrale Anlaufstelle zum Entdecken, Interagieren mit und Überwachen aller in Ihrer Organisation
eingesetzten KI-Agenten. Es bietet einen durchsuchbaren Katalog verfügbarer Agenten, der Benutzern ermöglicht, deren
Fähigkeiten zu verstehen, bevor sie mit ihnen interagieren.

::: details Kernfunktionen
- **Agenten-Erkennung**: Durchsuchen Sie einen visuellen Katalog aller Agenten, auf die Sie zugreifen dürfen, mit
  Beschreibungen und Statusindikatoren.
- **Workflow-Visualisierung**: Untersuchen Sie Agenten-Workflows als interaktive Diagramme, die deren Entscheidungslogik
  und Tool-Integrationen zeigen.
- **Direkte Interaktion**: Initiieren Sie Chat-Sitzungen direkt aus dem Profil des Agenten.
- **Thread-Übersicht**: Zeigen Sie alle Konversations-Threads an, die einem bestimmten Agenten zugeordnet sind, um
  dessen Interaktionshistorie zu überprüfen.
- **Statusüberwachung**: Sehen Sie Echtzeit-Indikatoren, die zeigen, ob Agenten laufen, gestoppt sind oder Fehler
  aufweisen.
:::

### Thread-Verwaltung

Dieser Dienst bietet eine vollständige Historie aller Konversationen zwischen Benutzern und KI-Agenten. Er ermöglicht es
Ihnen, vergangene Interaktionen fortzusetzen, die Argumentation eines Agenten zu überprüfen und eine vollständige
Audit-Spur von KI-gestützten Dialogen zu führen.

::: details Kernfunktionen
- **Thread-Katalog**: Zeigen, suchen und filtern Sie alle Ihre vergangenen Konversations-Threads.
- **Konversationshistorie**: Greifen Sie auf die vollständige Nachrichtenhistorie für jeden Thread zu, mit Zeitstempeln
  und Teilnehmerdetails.
- **Konversationen fortsetzen**: Setzen Sie jede vergangene Interaktion dort fort, wo Sie aufgehört haben, wobei der
  vollständige Kontext erhalten bleibt.
- **Ereignisanzeige**: Sehen Sie eine umfassende Visualisierung der internen Operationen eines Agenten während einer
  Konversation, einschließlich seines Denkprozesses, der Tool-Nutzung und der Schritte zur Datenabfrage.
:::

### Wissensverwaltung

Dieser Dienst bietet Ihnen transparente Kontrolle über die Wissensdatenbanken, die Ihre KI-Agenten für
Retrieval-Augmented Generation (RAG) verwenden. Sie können die Dokumente und Daten verwalten, die den Antworten Ihrer
Agenten Kontext verleihen.

::: details Kernfunktionen
- **Wissen organisieren**: Strukturieren Sie Informationen in Datenbanken und Namespaces, die die Datenstrukturen Ihrer
  Organisation widerspiegeln.
- **Dokumenten-Upload**: Laden Sie Dokumente manuell mit Vorschauen und Validierung hoch.
- **Verarbeitungs-Transparenz**: Sehen Sie genau, wie Dokumente geparst, zerstückelt und für die KI-Abfrage vorbereitet
  werden.
- **Dokumenten-Rekonstruktion**: Zeigen Sie die endgültige, verarbeitete Version eines Dokuments an, um zu verstehen,
  wie ein Agent es sieht.
:::

### Prozessverwaltung

Dieser Dienst dient der Visualisierung und Verwaltung komplexer, mehrstufiger Workflows, die KI-Agenten, menschliche
Entscheidungspunkte und Integrationen mit externen Systemen umfassen. Er bietet operationelle Transparenz in
hochentwickelte KI-gestützte Automatisierung.

::: details Kernfunktionen
- **Prozessvisualisierung**: Zeigen Sie interaktive Diagramme Ihrer automatisierten Geschäftsprozesse an.
- **Ausführungsüberwachung**: Verfolgen Sie den Echtzeit-Fortschritt laufender Prozesse und sehen Sie, welcher Schritt
  gerade aktiv ist.
- **Menschliche Intervention**: Nehmen Sie an Workflows teil, die an bestimmten Schritten eine menschliche Genehmigung
  oder Überprüfung erfordern.
- **Ausführungshistorie**: Überprüfen Sie eine vollständige Audit-Spur jedes Prozesslaufs, mit
  Schritt-für-Schritt-Protokollen und Ergebnissen.
:::

### Evaluierungsdienst

Dieser Dienst bringt systematische Tests und Qualitätssicherung für Ihre KI-Agenten. Er ermöglicht es Ihnen, die
Agentenleistung anhand vordefinierter Datensätze zu validieren, um Qualität und Genauigkeit vor und nach der
Bereitstellung sicherzustellen.

::: details Kernfunktionen
- **Datensatzverwaltung**: Laden und verwalten Sie Testdatensätze mit Frage-Antwort-Paaren oder anderen
  Bewertungskriterien.
- **Experimentkonfiguration**: Definieren und führen Sie automatisierte Experimente durch, die Agenten anhand Ihrer
  Datensätze testen.
- **Ergebnisanalyse**: Zeigen Sie umfassende Ergebnisse an, die Erfolgsraten, Leistungsmetriken und Fehleranalyse
  zeigen.
- **Vergleichende Analyse**: Vergleichen Sie die Ergebnisse verschiedener Experimente, um die Auswirkungen von
  Konfigurationsänderungen zu messen.
:::

### Administrative Dienste

Eine Reihe von Diensten ermöglicht es Administratoren, Benutzer, Rollen und Berechtigungen über eine intuitive
Benutzeroberfläche zu verwalten. Dies zentralisiert die Plattform-Governance für Sicherheits-, Compliance- und
Betriebsteams.

::: details Kernfunktionen
- **Benutzerverwaltung**: Benutzerkonten bereitstellen, ändern und deaktivieren.
- **Rollenverwaltung**: Definieren Sie Rollen mit spezifischen Berechtigungssätzen (z. B. „Agent Developer“, „Knowledge
  Manager“).
- **Berechtigungszuweisung**: Weisen Sie Benutzern Rollen zu, um ihnen Zugriff auf bestimmte Dienste und Funktionen zu
  gewähren.
- **Audit-Spuren**: Überprüfen Sie Benutzeraktivitätsprotokolle und Zugriffsmuster auf der gesamten Plattform.
:::

## Einheitliche Erfahrung

Diese Dienste sind keine isolierten Anwendungen. Die Suite ist so konzipiert, dass sie einen nahtlosen Workflow schafft,
bei dem der Kontext zwischen ihnen fließt.

- **Persistente Navigation**: Eine permanente Seitenleiste bietet den Zugriff auf jeden autorisierten Dienst mit einem
  Klick, von überall in der Anwendung. Sie müssen nie zu einem „Home“-Bildschirm zurückkehren, um Aufgaben zu wechseln.
- **Konsistentes Design**: Alle Dienste teilen dasselbe visuelle Design und dieselben Interaktionsmuster. Formulare,
  Tabellen und Schaltflächen verhalten sich überall vorhersehbar, sodass das Erlernen eines Dienstes Ihnen hilft, alle
  zu verstehen.
- **Dienstübergreifender Kontext**: Die Benutzeroberfläche versteht die Beziehungen zwischen Objekten. Beim Betrachten
  eines Agenten können Sie direkt zu seinen Wissensquellen oder seinen Konversations-Threads navigieren. Beim Überprüfen
  eines Threads können Sie sehen, welcher Agent teilgenommen hat.
- **Intelligente Benutzeroberfläche**: Die Benutzeroberfläche verwendet moderne Webmuster, um sich schnell und
  reaktionsschnell anzufühlen. Skeleton-Screens zeigen Ihnen, welche Inhalte geladen werden, und Echtzeit-Updates werden
  über WebSockets für die Live-Agenten-Ausführung und Prozessüberwachung übertragen.

Dieser integrierte Ansatz stellt sicher, dass die Plattform nicht nur eine Sammlung leistungsstarker Funktionen, sondern
eine produktive und kohärente Umgebung für alle Benutzer ist.
