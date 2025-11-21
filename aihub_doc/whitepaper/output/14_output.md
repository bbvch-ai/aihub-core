# Kapitel 14: Business-Prozessautomatisierung

Die digitale Transformation in Schweizer Unternehmen ist untrennbar mit der Optimierung und Automatisierung komplexer
Geschäftsprozesse verbunden. Doch wo herkömmliche Automatisierungslösungen oft an der Starrheit regelbasierter Systeme
scheitern, bietet die Integration von Künstlicher Intelligenz (KI) das Potenzial, manuelle Engpässe zu beseitigen, die
Prozessqualität zu steigern und menschliche Entscheidungsfindung intelligent zu unterstützen. Dieses Kapitel beleuchtet,
wie der Swiss AI Hub eine umfassende Plattform für die Business-Prozessautomatisierung bereitstellt, die eine nahtlose
Zusammenarbeit zwischen KI-Agenten, menschlichen Entscheidungsträgern und bestehenden Fachsystemen ermöglicht. Ein
besonderer Fokus liegt dabei auf der Verbindung von strikter Regelkonformität mit adaptiver KI-Assistenz, um
regulatorische Anforderungen zu erfüllen und gleichzeitig Effizienzgewinne zu realisieren.

## 1. Ganzheitliche Prozess-Orchestrierung für End-to-End-Automatisierung

Die Fragmentierung von Geschäftsprozessen über verschiedene Systeme und die Notwendigkeit manueller Übergaben stellen
für viele Unternehmen eine erhebliche Effizienzbremse dar. Eine effektive KI-Strategie erfordert daher eine Plattform,
die nicht nur einzelne KI-Aufgaben löst, sondern komplexe End-to-End-Workflows orchestrieren kann – von der
Datenerfassung über intelligente Verarbeitung bis zur finalen Systemaktualisierung.

### Mehrwert und Nutzen: Medienbruchfreie Prozesse und beschleunigte Wertschöpfung

Für C-Level-Führungskräfte bedeutet die ganzheitliche Prozess-Orchestrierung eine signifikante Steigerung der operativen
Effizienz und eine Beschleunigung der Time-to-Value für digitale Initiativen. Durch die Eliminierung manueller
Medienbrüche und die Automatisierung repetitiver Aufgaben werden nicht nur Kosten gesenkt, sondern auch die
Fehleranfälligkeit reduziert. Dies ermöglicht eine schnellere Bearbeitung von Anfragen im öffentlichen Sektor und eine
verbesserte Kundenzufriedenheit. IT-Teams profitieren von einer zentralen Plattform, die es ermöglicht, autonome
KI-Agenten, menschliche Experten und bestehende Drittsysteme in einem gemeinsamen, transparenten Workflow zu verbinden,
was die Komplexität der Systemintegration reduziert und die Wartbarkeit verbessert.

### Konzepte & Prozesse: Agentische Prozesse und Event-gesteuerte Workflows

Der Swiss AI Hub ermöglicht die Automatisierung komplexer Geschäftsabläufe durch sogenannte "agentische Prozesse". Diese
Prozesse basieren auf einer ereignisgesteuerten Architektur, bei der definierte Workflows das Verhalten von KI-Agenten
steuern, menschliche Interaktionen integrieren und externe Systemaufrufe orchestrieren. Anstatt dass KI autonom und
unkontrollierbar agiert, folgen die Prozesse explizit definierten, schrittweisen Abfolgen von Operationen (siehe auch
Kapitel 13: AI-Agenten und Kernkonzepte). Jeder Schritt eines Prozesses kann die volle Leistung der KI nutzen, um zu
argumentieren und Entscheidungen zu treffen, der Gesamtpfad bleibt jedoch stets durch den vordefinierten Workflow
gesteuert. Über das Swiss AI Agent Protokoll (SAAP) kommunizieren die beteiligten Komponenten über standardisierte
Ereignisse, was eine flexible und robuste Orchestrierung ermöglicht.

### Technische Umsetzung im Swiss AI Hub: SDK für Prozessdefinitionen und dynamische Endpunkte

Entwickler definieren diese agentischen Prozesse mit dem AI-Hub SDK, indem sie Workflow-Schritte als Code
implementieren. Die Plattform abstrahiert die zugrundeliegende Komplexität der Orchestrierung. Für jeden in der
Plattform definierten Prozess erstellt der AI Hub automatisch dynamische REST-API-Endpunkte
(`/processes/{process_class}/{process_id}/{route}`), die auf die spezifischen Fähigkeiten der Prozessdefinition
zugeschnitten sind. Dies ermöglicht externen Systemen, menschlichen Benutzern oder anderen KI-Agenten, Prozesse über
eine standardisierte API auszulösen, ihren Status abzufragen und mit ihnen zu interagieren. Die dynamische Generierung
dieser Endpunkte eliminiert manuelle API-Entwicklungsengpässe und stellt sicher, dass die Integrationsschicht stets mit
den laufenden Diensten synchronisiert ist.

## 2. Hybride Entscheidungsarchitektur: Regeln und KI in Harmonie

In vielen geschäftskritischen Bereichen, insbesondere im öffentlichen Sektor, sind Entscheidungen nicht nur eine Frage
der Effizienz, sondern auch der strikten Einhaltung von Regeln und Vorschriften. Eine reine KI-Automatisierung ohne
Berücksichtigung deterministischer Regelwerke birgt erhebliche Compliance-Risiken.

### Mehrwert und Nutzen: Regulatorische Sicherheit und intelligente Unterstützung

Diese hybride Entscheidungsarchitektur bietet C-Level-Führungskräften die Gewissheit, dass automatisierte Prozesse und
KI-generierte Vorschläge stets innerhalb definierter rechtlicher und regulatorischer Leitplanken verbleiben. Das
minimiert Haftungsrisiken und stärkt das Vertrauen in die Konformität der KI-Anwendungen. IT-Profis können
KI-Intelligenz gezielt zur Effizienzsteigerung einsetzen, ohne die Notwendigkeit einer vollständigen Neuentwicklung
bestehender Regelwerke. Die Plattform ermöglicht es, KI plausible nächste Schritte in komplexen Prozessen vorzuschlagen
und gleichzeitig sicherzustellen, dass harte Regeln niemals verletzt werden.

### Konzepte & Prozesse: Regel-Integration in Agenten-Workflows

Der Swiss AI Hub ermöglicht die Kombination von deterministischen Regelwerken mit adaptiver KI-Intelligenz innerhalb
desselben Prozess-Workflows. Dies bedeutet, dass KI-Agenten nicht nur kontextbasierte Vorschläge machen können, sondern
diese Vorschläge auch automatisch gegen vordefinierte Regeln validieren, bevor sie zur Ausführung kommen oder einem
menschlichen Prüfer vorgelegt werden. Wenn beispielsweise ein Agent in einem Antragsprüfungsprozess eine Entscheidung
vorschlägt, kann ein nachgelagerter Schritt diesen Vorschlag automatisch gegen ein Set von Compliance-Regeln prüfen, um
sicherzustellen, dass alle gesetzlichen Vorgaben eingehalten werden. Bei Abweichungen kann der Prozess automatisch zur
Korrektur an den Agenten zurückgegeben oder an einen menschlichen Sachbearbeiter eskaliert werden.

### Technische Umsetzung im Swiss AI Hub: Konditionale Logik und LLM-Wächter

Innerhalb der Agenten-Workflows können Entwickler über das SDK bedingte Logik implementieren, die sowohl KI-Ergebnisse
als auch Daten aus externen Systemen verarbeitet, um Regeln durchzusetzen. Dies kann durch if/else-Statements in den
Python-Schritten der Agenten erfolgen. Zusätzlich können KI-spezifische LLM-Wächter ("Guardrails", siehe Kapitel 08:
Sicherheitsarchitektur) konfiguriert werden, die die Qualität und Angemessenheit von KI-Antworten und Entscheidungen
überprüfen, bevor diese weiterverarbeitet werden. Beispielsweise kann ein `Few-Shot-Wächter` sicherstellen, dass
KI-Antworten spezifischen internen Richtlinien entsprechen, oder ein `Kontext-Hinreichend-Wächter` Halluzinationen
verhindert, indem er prüft, ob die KI genügend Informationen für eine faktenbasierte Aussage hat. Diese Wächter wirken
als präventive Leitplanken, die sicherstellen, dass KI-generierte Inhalte innerhalb der regulatorischen Vorgaben
bleiben.

## 3. Nahtlose Systemintegration mit externen Fachanwendungen

Die Effizienz von Geschäftsprozessen wird oft durch manuelle Datenübertragungen zwischen verschiedenen
Unternehmenssystemen untergraben. Eine erfolgreiche Automatisierung erfordert eine tiefe Integration in die bestehende
heterogene IT-Landschaft, einschliesslich spezifischer eGovernment-Fachanwendungen.

### Mehrwert und Nutzen: Medienbruchfreier Datenaustausch und Investitionsschutz

Für Führungskräfte sichert die nahtlose Systemintegration den Investitionsschutz in bestehende ERP-, CRM- und
eGovernment-Lösungen, indem sie diese intelligent erweitert, anstatt sie zu ersetzen. Der medienbruchfreie
Datenaustausch beschleunigt Verwaltungsprozesse, reduziert Fehlerquoten und gewährleistet eine hohe Datenkonsistenz über
alle Systeme hinweg. Für IT-Teams bedeutet dies eine erhebliche Vereinfachung bei der Anbindung von KI-Funktionen an
etablierte Systeme durch standardisierte Schnittstellen und Ereignis-basierte Trigger, wodurch der administrative
Aufwand für Integration und Wartung minimiert wird.

### Konzepte & Prozesse: Vier Integrationsmuster für Flexibilität

Der Swiss AI Hub unterstützt vier Kernintegrationsmuster (siehe auch Kapitel 11: Integration und Interoperabilität), die
eine flexible Anbindung an externe Systeme ermöglichen:

1. **Direkte Agenten-API-Aufrufe**: Agenten können externe APIs (REST, SOAP, GraphQL) direkt aus ihren
   Workflow-Schritten aufrufen, um Daten abzurufen oder zu übermitteln (z.B. Kundendaten aus einem CRM abfragen,
   Formulare an ein Portal übermitteln).
2. **Plattform-API-Integration**: Externe Systeme können AI-Hub-Agenten über die Agent Interaction REST API auslösen, um
   KI-Funktionen zu nutzen (z.B. KI-Klassifizierung bei Dokumentenuploads, Zusammenfassungen für Dashboards).
3. **Datenpipeline-Integration**: Für leseintensive und grossflächige Datensynchronisation werden Dagster-Pipelines
   verwendet, die kontinuierlich Daten von externen Systemen in AI-Hub Wissensbasen laden (z.B. SharePoint-Dokumente
   synchronisieren, Support-Tickets für Analysen aufnehmen).
4. **MCP-Integration**: Für Entwicklungstools zur Beobachtung und Interaktion mit dem AI-Hub.

Diese Ansätze ermöglichen die Anbindung an breite ERP- und CRM-Systeme sowie spezialisierte eGovernment-Lösungen.

### Technische Umsetzung im Swiss AI Hub: Konnektoren, APIs und Webhooks

Die Plattform bietet vorkonfigurierte Konnektoren und unterstützt die Entwicklung kundenspezifischer Konnektoren für die
Datenpipeline-Integration mit Systemen wie Microsoft SharePoint, OneDrive, Confluence, File-Shares und S3-kompatiblen
Object Stores. Auch die Integration mit spezialisierten eGov-Fachverfahren wie CMI Axioma oder RMS Gever ist über die
flexible Datenpipeline-Architektur realisierbar.

Die **Agent Interaction REST API** ermöglicht bidirektionale Integrationen, wobei externe Systeme KI-Funktionen auslösen
und strukturierte Ergebnisse empfangen können. Die Authentifizierung eingehender HTTP-Anfragen erfolgt über OAuth 2.0,
API-Schlüssel oder Azure AD-Integration. Ausgehende Konnektivität für direkte Agenten-API-Aufrufe und Pipelines
erfordert ausgehenden HTTPS-Zugriff (Port 443) auf externe Endpunkte, wobei die Plattform API-Schlüssel, OAuth-Tokens
und zertifikatbasierte Authentifizierung unterstützt. Die ereignisgesteuerte Architektur ermöglicht zudem die
**Webhook-Unterstützung für Event-Driven-Integration**, wodurch die Plattform flexibel auf Ereignisse reagieren und
Aktionen in externen Systemen auslösen kann, z.B. die automatische Weitergabe von KI-generierten Empfehlungen an ein
nachgelagertes System.

## 4. Human-in-the-Loop-Eskalation für sichere Entscheidungen

Nicht jede Entscheidung in einem automatisierten Prozess kann vollständig einer KI überlassen werden, insbesondere bei
Unsicherheiten, komplexen Ausnahmen oder kritischen Auswirkungen. Menschliche Kontrolle und Expertise sind oft
unerlässlich.

### Mehrwert und Nutzen: Eliminierung von Fehlentscheidungen und effektive Wissenserfassung

Für C-Level-Führungskräfte eliminiert die Human-in-the-Loop (HITL)-Eskalation das Risiko von kostspieligen
Fehlentscheidungen durch die KI, indem die Plattform bei Unsicherheiten automatisch und kontexterhaltend an menschliche
Sachbearbeiter übergibt. Dies sichert die Compliance und die Verantwortlichkeit. Gleichzeitig wird durch die Rückführung
menschlicher Expertise in die Wissensbasis die KI kontinuierlich intelligenter. IT-Teams profitieren von definierten
Eskalationspfaden und der nahtlosen Integration menschlicher Interaktion in den Workflow, was komplexe Prozesse robuster
und fehlertoleranter macht. Die Weiterleitung von Aufgaben an Sachbearbeiter erfolgt automatisch und kann über
etablierte Kommunikationskanäle gesteuert werden.

### Konzepte & Prozesse: Kontextkonservierung und Expert Asking Agent

Das HITL-Muster ermöglicht es einem Agenten, seinen Workflow an einem kritischen Punkt zu pausieren und auf menschliche
Eingaben, Genehmigungen oder Anweisungen zu warten. Das Besondere daran ist, dass der Workflow genau an diesem Punkt mit
dem vollen Gedächtnis aller Zwischenergebnisse und vorheriger Schritte fortgesetzt wird. Die Wartezeiten können dabei
Minuten, Stunden oder sogar Tage betragen, ohne den technischen Ablauf zu unterbrechen (Management langlaufender
Prozesse).

Ein spezialisiertes `Experten-Agenten`-Paar (`Expert Grounded Agent` und `Expert Asking Agent`) ist für die Beantwortung
von Fragen zuständig, die das Wissen der KI übersteigen. Erkennt der `Expert Grounded Agent` eine Wissenslücke, bittet
er den Benutzer um Zustimmung und delegiert die Frage an den `Expert Asking Agent`. Dieser wiederum leitet die Frage an
einen menschlichen Experten (z.B. über Slack) weiter. Die Antwort des menschlichen Experten wird erfasst und als neues,
permanentes Wissenselement in der Wissensdatenbank gespeichert, wodurch die KI kontinuierlich lernt (siehe Kapitel 13).

### Technische Umsetzung im Swiss AI Hub: `HumanInTheLoop` Events und Integration mit Kollaborations-Tools

Das HITL-Muster wird durch spezielle `HumanInTheLoop.request` und `HumanInTheLoop.response` Events orchestriert. Der
`request`-Event pausiert den Workflow und präsentiert dem Benutzer eine Frage in der Benutzeroberfläche. Die Antwort des
Benutzers als `response`-Event setzt den Workflow fort. Eine Helferklasse vereinfacht die Implementierung dieser Muster
für einzelne oder mehrstufige Genehmigungsprozesse. Alle menschlichen Interaktionen werden im Rahmen der lückenlosen
Nachvollziehbarkeit aufgezeichnet. Die Plattform integriert sich über einen separat bereitstellbaren Bot Framework
API-Dienst mit dem Microsoft Azure Bot Service, was die Multichannel-Bereitstellung von KI-Agenten in
Kollaborationsplattformen wie **Microsoft Teams** und **Slack** ermöglicht. So können menschliche Sachbearbeiter
Aufgaben und Fragen der KI in ihrem gewohnten Arbeitsumfeld empfangen, bearbeiten und die Ergebnisse zurück in den
Prozess speisen.

## 5. Transparenz und Prozess-Optimierung durch Observability

Ohne transparente Einblicke in den Status, die Leistung und die Kosten laufender Prozesse können Unternehmen Engpässe
nicht identifizieren, Effizienzgewinne nicht messen und Compliance-Anforderungen nicht nachweisen.

### Mehrwert und Nutzen: Messbare Effizienz und fundierte Optimierung

Für Führungskräfte liefert Echtzeit-Monitoring eine fundierte Grundlage zur Messung des ROI von automatisierten
Prozessen und zur Identifizierung von Flaschenhälsen. Dies ermöglicht datengestützte Entscheidungen zur weiteren
Optimierung der Prozessabläufe und zur Steigerung der betrieblichen Effizienz. IT-Teams profitieren von einer
umfassenden Observability-Suite, die jederzeit Einblick in den Status laufender Vorgänge bietet, die Ursachenanalyse bei
Fehlern erleichtert und die Einhaltung von SLAs (Service Level Agreements) unterstützt. Die Verfolgung der Token-Nutzung
ermöglicht zudem eine genaue Kostenattribution pro Prozess oder Abteilung.

### Konzepte & Prozesse: Die Säulen der Observability und End-to-End-Tracing

Die Überwachungsphilosophie der Plattform basiert auf den branchenüblichen Säulen der Observability: Health Checks
(Liveness/Readiness), Metriken (Leistung/Ressourcennutzung) und Logs (detaillierte Ereignisaufzeichnungen). Ein
zentrales Element ist das End-to-End Distributed Tracing mittels OpenTelemetry, das jeden Anfragefluss über Dienste,
Agenten und LLM-Interaktionen hinweg verfolgt. Alle Interaktionen im Prozess, einschliesslich der menschlichen
Eingriffe, werden lückenlos protokolliert. Dies ist entscheidend, um die Nachvollziehbarkeit im Falle von Problemen zu
gewährleisten und die Einhaltung regulatorischer Anforderungen nachzuweisen.

### Technische Umsetzung im Swiss AI Hub: OpenTelemetry, SigNoz und Phoenix UI

Das gesamte Überwachungs- und Alarmierungssystem des Swiss AI Hub basiert auf **OpenTelemetry (OTel)**. Ein zentraler
**OpenTelemetry Collector** empfängt Logs, Metriken und Traces von allen Diensten, reichert sie mit Metadaten an und
exportiert sie sicher an die gewählten Ziele. Als offiziell unterstütztes Observability-Backend dient **SigNoz**, eine
Open-Source-, OpenTelemetry-native Plattform, die vereinheitlichte Dashboards für Infrastruktur, KI-Operationen
(Modellnutzung, Token-Verbrauch, Kosten pro Operation), Anwendungsleistung und Log-Analyse bereitstellt.

Für die detaillierte Analyse von Agenten-Workflows während der Entwicklung bietet die **Phoenix UI** spezialisierte
LLM-Observability mit Timeline-Ansichten, Token-Nutzung und Inspektionsmöglichkeiten abgerufener Dokumente. Flexible
Alarmierungsfunktionen können für kritische Dienstausfälle, Leistungsverschlechterung, Ressourcenlimits,
Kostenmanagement (ungewöhnlich hoher Token-Verbrauch in einem Prozess) und Sicherheitsereignisse konfiguriert und an
Kanäle wie E-Mail, Slack oder Microsoft Teams weitergeleitet werden. Diese detaillierten Einblicke ermöglichen eine
präzise Messung der Effizienzgewinne und unterstützen die kontinuierliche Prozess-Optimierung.
