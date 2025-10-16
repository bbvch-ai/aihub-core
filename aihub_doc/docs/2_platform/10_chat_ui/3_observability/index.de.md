---
title: Erweiterte Beobachtbarkeit
index: 3
source_sha: "5a23440b848ade93485eb3eed792f13b579075626a514f24557f34cca45393cb"
---

# Erweiterte Beobachtbarkeit

Über die Quellenattribution hinaus erweitert der Swiss AI Hub die Chat-Oberfläche um umfassende Beobachtbarkeitsfunktionen, die eine beispiellose Transparenz in die Ausführungsprozesse von Agenten ermöglichen. Diese Transparenz verwandelt KI-Interaktionen von undurchsichtigen „Black Boxes" in transparente, nachvollziehbare Workflows, die Debugging, Qualitätssicherung und die Einhaltung gesetzlicher Vorschriften unterstützen.

## Die Herausforderung der Beobachtbarkeit in KI-Systemen

Traditionelle KI-Systeme liefern Nutzern Ergebnisse – Chat-Antworten, Empfehlungen, Entscheidungen – ohne Einblick in die dahinterliegenden Denkprozesse. Nutzer erleben KI als mysteriöse Orakel, die irgendwie Ausgaben aus Eingaben erzeugen, ohne Einblick in Zwischenschritte, Entscheidungslogik oder potenzielle Fehlerquellen.

**Vertrauensbarrieren in Unternehmen**: Diese Undurchsichtigkeit schafft Vertrauensbarrieren für die Einführung in Unternehmen. Entscheidungsträger zögern, sich auf Systeme zu verlassen, die sie nicht verstehen, beheben oder validieren können. Wenn KI unerwartete Ergebnisse liefert, fehlen den Nutzern die notwendigen Informationen, um festzustellen, ob das System fehlerhaft war, Anforderungen falsch verstanden hat oder fehlerhafte Eingabedaten korrekt verarbeitet hat.

**Debugging und Qualitätssicherung**: Entwicklungsteams stehen vor ähnlichen Herausforderungen. Wenn Agenten in der Produktion unerwartet agieren, erfordert das Debugging umfangreiche Log-Analysen und Reproduktionsversuche. Qualitätssicherungsteams haben Schwierigkeiten, das Verhalten von Agenten systematisch zu validieren, ohne Einblick in die Ausführungsdetails zu haben.

**Regulatorische Anforderungen und Compliance**: Regulierte Branchen sehen sich zunehmend mit Anforderungen konfrontiert, KI-gestützte Entscheidungen zu erklären und zu begründen. Compliance-Frameworks fordern Nachweisreihen, die zeigen, wie Systeme zu Schlussfolgerungen gelangten, welche Daten die Entscheidungen informierten und wo menschliche Aufsicht stattfand. Undurchsichtige KI-Systeme können diese Anforderungen nicht erfüllen.

## Integration von Ausführungs-Traces

Der Swiss AI Hub begegnet diesen Herausforderungen durch eine tiefe Integration mit einer Infrastruktur für Ausführungs-Traces, die detaillierte Aufzeichnungen der Workflow-Ausführung von Agenten erfasst.

**Schritt-für-Schritt-Workflow-Visualisierung**: Wenn Nutzer Ausführungs-Traces einsehen, sehen sie die vollständige Abfolge der vom Agenten ausgeführten Schritte – Entscheidungspunkte, Tool-Aufrufe, Wissensabfragen, Zwischenberechnungen. Diese Visualisierung stellt Agenten-Workflows als strukturierte Prozesse dar und nicht als mysteriöse Berechnungen.

**Transparenz des Ereignisflusses**: Jeder Workflow-Schritt verbraucht Eingabeereignisse und erzeugt Ausgabeereignisse. Die Trace-Anzeige zeigt diese Ereignisflüsse und hilft den Nutzern zu verstehen, wie sich Daten im Verlauf des Workflows transformieren. Eingabemeldungen werden zu Klassifizierungsereignissen, die zu Abrufanfragen werden, die zu synthetisierten Antworten werden – die komplette Kette der Transformationen ist sichtbar und verständlich.

**Zeit- und Leistungsdaten**: Traces enthalten detaillierte Zeitinformationen für jeden Workflow-Schritt. Nutzer können Leistungsengpässe identifizieren, verstehen, wo Agenten Verarbeitungszeit investieren, und beurteilen, ob langsame Antworten auf komplexe Logik oder Infrastrukturverzögerungen zurückzuführen sind.

**Sichtbarkeit bedingter Verzweigungen**: Wenn Agenten-Workflows bedingte Logik enthalten – d.h. basierend auf Daten oder Kontext unterschiedliche Pfade nehmen – zeigen Traces, welche Verzweigungen ausgeführt wurden und warum. Diese Transparenz hilft Nutzern, die Entscheidungsfindung von Agenten zu verstehen und bestätigt, dass Agenten die passende Logik auf spezifische Szenarien anwenden.

## Interaktive Trace-Erkundung

Die Beobachtbarkeit geht über passive Anzeigen hinaus, um die interaktive Erkundung von Agenten-Ausführungsdetails zu ermöglichen.

**Integration des Trace-Panels**: Ähnlich der Quellenattribution öffnet die Trace-Anzeige ein angrenzendes Panel innerhalb der Chat-Oberfläche, wobei der Gesprächskontext erhalten bleibt und gleichzeitig Ausführungsdetails präsentiert werden. Nutzer können Chat-Antworten mit den Workflow-Schritten korrelieren, die sie erzeugt haben, ohne Anwendungen wechseln oder ihren Platz in Unterhaltungen verlieren zu müssen.

**Hierarchische Detailstufen**: Traces präsentieren Informationen hierarchisch – hochrangige Workflow-Übersicht, detaillierte Schrittausführung, granulare Ereignisdaten. Nutzer können in Bereiche von Interesse eintauchen, ohne bei einfachen Operationen von übermäßigen Details überwältigt zu werden.

**Inspektion von Ereignisdaten**: Auf der granularsten Ebene können Nutzer vollständige Ereignisdaten – die JSON-Strukturen, die zwischen den Workflow-Schritten fließen – untersuchen. Dieses Detail unterstützt anspruchsvolles Debugging und Validierung, indem es technischen Nutzern ermöglicht, Datentransformationen zu überprüfen und Datenqualitätsprobleme zu identifizieren.

**Dienstübergreifende Navigation**: Von Trace-Ansichten aus können Nutzer zu verwandten Plattformfunktionen navigieren – Wissensdokumente einsehen, die während Abrufschritten aufgerufen wurden, Agentenkonfigurationen prüfen, die das Verhalten bestimmten, Systemprotokolle für infrastrukturbezogene Untersuchungen abrufen.

## Phoenix Tracing Integration

Die Beobachtbarkeitsfunktion baut auf Arize Phoenix auf, einer Open-Source-KI-Beobachtbarkeitsplattform, die eine branchenübliche Tracing-Infrastruktur bereitstellt.

**OpenInference Kompatibilität**: Die Plattform implementiert OpenInference semantische Konventionen und stellt sicher, dass Trace-Daten standardisierten Formaten folgen, die mit branchenüblichen Beobachtbarkeits-Tools kompatibel sind. Diese Standardkonformität bietet Bereitstellungsflexibilität und verhindert die Bindung an proprietäre Beobachtbarkeitssysteme (Vendor Lock-in).

**Semantische Ereigniskorrelation**: Das System erfasst semantische Ereignisse – LLM-Aufrufe, Abrufoperationen, Embedding-Generierungen – als strukturierte Trace-Spans. Diese semantischen Ereignisse bieten eine KI-spezifische Beobachtbarkeit, die über generisches Anwendungs-Tracing hinausgeht und Konzepte wie Token-Nutzung, Abruf-Relevanzwerte und Modellauswahl erfasst.

**Multi-Agenten-Trace-Korrelation**: Wenn Workflows mehrere Agenten involvieren – Orchestrator-Agenten, die Worker-Agenten aufrufen, Human-in-the-Loop-Unterbrechungen, Agent-zu-Agent-Kollaboration – behalten Traces die Korrelation über diese Interaktionen hinweg bei. Nutzer können Ausführungsflüsse verfolgen, die sich über mehrere Agenten erstrecken, und so komplexe Multi-Agenten-Orchestrierung verstehen.

**Persistente Trace-Speicherung**: Ausführungs-Traces bleiben über Gesprächssitzungen hinaus bestehen und ermöglichen retrospektive Analysen. Nutzer können historische Agenten-Ausführungen für Qualitätssicherung, Compliance-Dokumentation oder Incident-Untersuchungen Wochen oder Monate nach den Interaktionen überprüfen.

## Geschäftswert der Beobachtbarkeit

Erweiterte Beobachtbarkeit bietet spezifische Geschäftsvorteile für KI-Implementierungen in Unternehmen.

**Beschleunigte Problembehebung**: Wenn Agenten unerwartet agieren, ermöglichen Ausführungs-Traces eine schnelle Fehlerbehebung. Support-Teams können genaue Ausführungssequenzen untersuchen, Fehlerpunkte identifizieren und Probleme ohne umfangreiche Reproduktionsversuche oder Entwickler-Eskalation beheben.

**Qualitätsvalidierung**: Qualitätssicherungsteams nutzen Ausführungs-Traces, um das Verhalten von Agenten systematisch zu validieren. Indem sie untersuchen, wie Agenten verschiedene Eingaben verarbeiten und Grenzfälle handhaben, kann die QS die Korrektheit vor der Produktionsbereitstellung überprüfen und Probleme identifizieren, die bei Tests nicht vorhergesehen wurden.

**Kontinuierliche Verbesserung**: Entwickler nutzen Trace-Daten, um Optimierungsmöglichkeiten zu identifizieren. Traces, die ineffiziente Abrufmuster, unnötige Workflow-Schritte oder mangelhafte bedingte Logik aufzeigen, leiten die Verfeinerungsbemühungen der Agenten, was die Leistung und Genauigkeit im Laufe der Zeit verbessert.

**Compliance-Nachweise**: Für die Einhaltung gesetzlicher Vorschriften liefern Ausführungs-Traces detaillierte Nachweisketten, die dokumentieren, wie Systeme zu Schlussfolgerungen gelangten. Compliance-Audits können Traces überprüfen, die eine angemessene Datennutzung, korrekte Workflow-Ausführung und menschliche Aufsicht an erforderlichen Entscheidungspunkten belegen.

**Benutzervertrauen**: Wenn Nutzer die Ausführungsdetails von Agenten untersuchen können, steigt das Vertrauen in KI-Systeme. Die Möglichkeit, „unter die Haube zu schauen", verwandelt KI von einer mysteriösen Technologie in verständliche Werkzeuge und beschleunigt die Akzeptanz bei Nutzern, die sich sonst möglicherweise scheuen würden, sich auf undurchsichtige Systeme zu verlassen.

## Beobachtbarkeit in der Agentenentwicklung

Über die Unterstützung von Endnutzern hinaus spielen Beobachtbarkeitsfunktionen eine entscheidende Rolle in den Entwicklungs- und Test-Workflows von Agenten.

**Debugging während der Entwicklung**: Entwickler, die Agenten bauen und verfeinern, nutzen Trace-Visualisierung intensiv während der Entwicklung. Anstatt sich auf Logfile-Analysen oder Debugging mit Print-Statements zu verlassen, beobachten Entwickler Workflows in Echtzeit über Trace-Schnittstellen und verstehen das Verhalten sofort.

**Testvalidierung**: Automatisierte Tests erfassen Ausführungs-Traces und ermöglichen Test-Assertions gegen Workflow-Ausführungsdetails, die über die Endergebnisse hinausgehen. Tests können überprüfen, ob Agenten die entsprechenden Tools aufgerufen, die richtigen Wissensquellen genutzt und die erwarteten Workflow-Pfade eingehalten haben – wodurch das Verhalten umfassend validiert wird.

**Leistungsprofilierung**: Trace-Zeitdaten ermöglichen eine systematische Leistungsprofilierung. Entwickler identifizieren langsame Workflow-Schritte, quantifizieren die Leistungsbeeinträchtigungen verschiedener Konfigurationen und validieren, dass Optimierungen die erwarteten Verbesserungen liefern.

**Workflow-Dokumentation**: Ausführungs-Traces dienen als lebendige Dokumentation von Agenten-Workflows. Anstatt separate Workflow-Diagramme zu pflegen, die von der Implementierung abweichen, beziehen sich Entwickler auf tatsächliche Ausführungs-Traces, die zeigen, wie Agenten in der Praxis agieren.

## Datenschutz- und Sicherheitsaspekte

Umfassende Beobachtbarkeit wirft Datenschutz- und Sicherheitsaspekte auf, die die Plattform durch entsprechende Kontrollen adressiert.

**Berechtigungsbasierter Zugriff**: Die Sichtbarkeit von Traces respektiert das Berechtigungssystem der Plattform. Nutzer können nur Traces für Unterhaltungen einsehen, an denen sie teilgenommen haben oder für die sie zur Überprüfung autorisiert sind. Administrativer Trace-Zugriff erfordert explizite Berechtigungen, um unautorisierten Einblick in sensible Unterhaltungen zu verhindern.

**Umgang mit sensiblen Daten**: Die Plattform kann sensible Informationen aus Trace-Anzeigen – persönlich identifizierbare Informationen, vertrauliche Geschäftsdaten – schwärzen, wobei die Workflow-Struktur und Ausführungsdetails, die für Debugging und Qualitätssicherung notwendig sind, erhalten bleiben.

**Audit-Trail des Trace-Zugriffs**: Das System protokolliert Trace-Zugriffe und erstellt Audit-Trails, die dokumentieren, wer welche Ausführungs-Traces wann überprüft hat. Dieses Meta-Auditing unterstützt Compliance-Anforderungen und erkennt unangemessenen Zugriff auf sensible Konversationsdaten.

**Aufbewahrungskontrollen**: Organisationen konfigurieren Trace-Aufbewahrungsrichtlinien, die den Beobachtbarkeitswert gegen Speicherkosten und Datenaufbewahrungsvorschriften abwägen. Traces können nach konfigurierbaren Zeiträumen ablaufen, oder eine selektive Aufbewahrung kann Traces für wichtige Konversationen erhalten, während routinemäßige Interaktionen auslaufen.

## Differenzierung durch Transparenz

Die Beobachtbarkeitsfunktionen des Swiss AI Hub stellen eine grundlegende philosophische Differenzierung im Vergleich zu vielen KI-Plattformen dar.

**Transparenz by Design**: Anstatt KI-Ausführungsdetails als nutzerverborgene Implementierungsspezifika zu behandeln, betrachtet die Plattform Transparenz als Kernprinzip. Diese Designphilosophie erkennt an, dass Implementierungen im Unternehmens- und öffentlichen Sektor Verständigungs- und Validierungsfähigkeiten erfordern, die über Konsumentenanwendungen hinausgehen.

**Standardsbasierte Implementierung**: Indem die Plattform auf Phoenix- und OpenInference-Standards statt auf proprietären Tracing-Systemen aufbaut, bietet sie Beobachtbarkeit, die sich in bestehende Unternehmens-Monitoring-Infrastrukturen integriert und Vendor Lock-in vermeidet.

**Vollständige Workflow-Sichtbarkeit**: Die Beobachtbarkeit erstreckt sich über einzelne Modellaufrufe hinaus auf die vollständige Workflow-Ausführung – die schrittbasierte Architektur, die Agenten definiert, unterstützt von Natur aus das Tracing auf Workflow-Ebene, nicht nur auf Modellebene.

Diese erweiterte Beobachtbarkeit, kombiniert mit Quellenattribution, zeigt, wie der Swiss AI Hub Open-Source-Chat-Infrastrukturen mit Enterprise-Funktionen erweitert. Organisationen erhalten sowohl die Gesprächsfreundlichkeit moderner Chat-Oberflächen als auch die Transparenz, die für eine zuversichtliche KI-Bereitstellung in Unternehmen erforderlich ist.
