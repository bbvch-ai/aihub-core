---
title: Das Ökosystem-Modell
source_sha: ab2757b0f05206f46f18fa736fa4a079dc11fcee35b299ea2f61ba7d77a3803d
---

# Das Ökosystem-Modell: Wie alle profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsvorteil sein sollte. Grundlegende Funktionen wie
LLM-Zugang, Dokumentenverarbeitung und RAG sollten Güter des täglichen Bedarfs sein, die jedem zugänglich sind.
Schweizer Organisationen sollten sich auf ihre Domänenexpertise und Geschäftsinnovation konzentrieren, nicht darauf, wer
bessere Authentifizierungssysteme oder Vektordatenbanken aufbauen kann.

## Die Schweizer Chance

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft, die von Tech-Giganten dominiert wird, konkurriert.
Während Google, Microsoft und Amazon Milliarden in KI-Infrastruktur investieren, fehlen Schweizer Unternehmen
individuell die Ressourcen, um diese Investitionen zu erreichen. Die typische Reaktion wäre, die Abhängigkeit von
ausländischen Plattformen zu akzeptieren, aber die Schweiz hat eine andere Option: Zusammenarbeit.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Ansatz zur KI
verändern. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf die
Grundlage konzentrieren, während wir auf der Anwendungsebene konkurrieren. Es geht hier nicht darum, den Wettbewerb zu
eliminieren; es geht darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Gut

Betrachten Sie, was jede Organisation, die KI aufbaut, benötigt:

- Sicherer Modellzugriff mit Kostenkontrolle
- Dokumentenverarbeitung und Vektorspeicherung
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsanforderungen einer Bank unterscheiden sich nicht grundlegend
von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung
spiegeln die einer Fertigungsfirma wider. Doch heute baut jede Organisation diese Funktionen entweder separat auf oder
unterwirft sich einer ausländischen Plattform.

Der Swiss AI Hub macht diese Infrastruktur zu einem Gut. Deployen Sie die Plattform einmal, und diese Probleme sind
gelöst. Jede Verbesserung der Kernplattform kommt jeder Organisation zugute, die sie nutzt. Wenn jemand eine bessere
Dokumentenanalyse beiträgt, verbessert sich die Dokumentenverarbeitung aller. Wenn jemand eine neue Sicherheitsfunktion
hinzufügt, werden alle sicherer.

## Die Beitragsdynamik

Der Swiss AI Hub ist vollständig unter Apache 2.0 lizenziert – Plattform, SDK, Agents, Pipelines und Prozesse. Diese
permissive Lizenzierung schafft natürliche Anreize zur Zusammenarbeit, ohne sie zu erzwingen.

**Gemeinsam genutzte Infrastruktur kommt allen zugute:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das
Teilen sinnvoll, weil alle davon profitieren. Eine Bank, die bessere Compliance-Protokollierung hinzufügt, hilft jeder
regulierten Branche. Ein Gesundheitsdienstleister, der die PII-Verarbeitung verbessert, hilft allen bei
Datenschutzbedenken. Diese Beiträge fliessen natürlich zurück, da eine bessere gemeinsam genutzte Infrastruktur die
Kosten für alle senkt.

**Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der
kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung, Ihre
Domänenexpertise verkörpert – diese bleiben Ihnen. Apache 2.0 verlangt kein Zurückteilen, sodass Sie strategische
Innovationen privat halten können, während Sie von der gemeinsam genutzten Infrastruktur profitieren und dazu beitragen.

## Warum Lizenzierung für KI-Infrastruktur wichtig ist

Das Verständnis von Softwarelizenzen ist beim Aufbau von KI-Infrastruktur entscheidend. Viele Organisationen machen
kostspielige Fehler, indem sie davon ausgehen, dass Code auf GitHub automatisch kostenlos nutzbar ist – das ist er
nicht.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ kostenlos nutzbar.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre
Software mit restriktiven Lizenzen. Die Möglichkeit, Code *anzusehen* oder *herunterzuladen*, bedeutet nicht, dass Sie
ihn rechtlich *nutzen* dürfen, insbesondere nicht in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use
License" (keine Open-Source-Lizenz). Während Sie es herunterladen und ausführen können, verbietet die Lizenz die
kommerzielle Nutzung ohne den Kauf einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen
entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Erläuterung der Lizenzkategorien

**Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren umfassende Freiheiten – kommerzielle Nutzung, Modifikation,
Verteilung, private Behaltung von Modifikationen. Keine Verpflichtungen. Diese sind ideal für den Aufbau von
Geschäftsinfrastruktur.

**Copyleft-Lizenzen** (GPL, AGPL): Erfordern, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz
veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung als
Open Source freigeben. **AGPL erweitert dies auf die Netzwerknutzung** – selbst das Anbieten der Software als Service
löst die Anforderung aus. Gefährlich für proprietäre KI-Produkte.

**Source-available-Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use"): Ermöglichen das Ansehen und manchmal die
Nutzung des Codes, aber auferlegen strenge Beschränkungen – oft verbieten sie die kommerzielle Nutzung, Managed Services
oder konkurrierende Produkte. Trotz des Erscheinens auf GitHub nicht Open Source.

**Proprietäre/kundenspezifische Lizenzen:** Variieren stark. Erfordern sorgfältige rechtliche Prüfung. Verbieten oft die
Produktionsnutzung ohne Bezahlung.

### Lizenzen, die in der KI-Infrastruktur vermieden werden sollten

Für KI-Produktionssysteme sollten Sie äusserst vorsichtig sein bei:

- **AGPL/GPL:** Zwingen Ihr gesamtes System in den Open-Source-Bereich, wenn Sie die Software modifizieren und
  vertreiben.
- **SSPL (Server Side Public License):** Der Versuch von MongoDB, Cloud-Anbieter daran zu hindern, Managed-Versionen
  anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus.
- **Elastic License v2:** Verbietet das Anbieten der Software als konkurrierenden Service.
- **Business Source License (BSL):** Zeitverzögerte Open-Source-Lizenz; restriktiv bis zum Ablaufdatum.
- **Kundenspezifische „source-available"-Lizenzen:** Verbieten in der Regel die kommerzielle Nutzung oder haben unklare
  Bedingungen.

Diese Lizenzen mögen anfänglich akzeptabel erscheinen, schaffen aber rechtliche Minenfelder, wenn Sie skalieren,
Services anbieten oder in Kundensysteme integrieren.

### Unser Lizenzierungsengagement

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externen
Docker-Images. Wir verifizieren, dass jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit
überprüft und genehmigt wurde.

**Sie erhalten vollständige Freiheit:** Nutzen Sie den gesamten Stack kommerziell, modifizieren Sie alles, integrieren
Sie ihn in proprietäre Systeme, bieten Sie ihn als Service an oder bauen Sie Produkte darauf auf – ohne Lizenzkonflikte,
versteckte Einschränkungen oder zukünftige Überraschungen.

**Warum speziell Apache 2.0:** Über die Permissivität hinaus enthält Apache 2.0 explizite Patentlizenzen, die Sie vor
Patentansprüchen von Mitwirkenden schützen. Sie wird von Unternehmen geschätzt, von Rechtsteams gut verstanden und ist
mit praktisch allen anderen Lizenzen kompatibel. Sie ist der Goldstandard für kollaborative Infrastruktur.

Das ist nicht nur Idealismus – es ist Pragmatismus. Permissive Lizenzierung beseitigt Adoptionsbarrieren, verhindert
Vendor Lock-in und stellt sicher, dass Sie Ihre KI-Infrastruktur vollständig besitzen. Keine Lizenzaudits, keine
Compliance-Risiken, keine plötzlichen Regeländerungen.

## Echte Kollaborationsmuster

Das Ökosystem zeigt bereits, wie dies funktioniert:

**Gemeinsame Komponenten:** Gängige Agents für Dokumentenzusammenfassungen, Frage-Antwort-Systeme und Datenextraktion
werden zu Community-Assets. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.

**Branchenlösungen:** Gesundheitsorganisationen arbeiten bei der medizinischen Dokumentenverarbeitung zusammen.
Finanzdienstleister teilen Compliance-fokussierte Agents. Diese branchenspezifischen Lösungen entstehen natürlich, wenn
Organisationen erkennen, dass ihre Konkurrenten im Ausland und nicht im Inland die eigentliche Bedrohung darstellen.

**Infrastrukturverbesserungen:** Leistungsoptimierungen, Sicherheitsverbesserungen und operationale Tools fliessen
zurück in die Plattform. Alle profitieren von einer schnelleren, sichereren und zuverlässigeren Grundlage.

**Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Die gleiche
Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystem-Modell eliminiert den Wettbewerb nicht; es konzentriert ihn dort, wo es wichtig ist:

**Ihre Domänenexpertise** bleibt Ihre. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre
Markteinblicke nicht. Diese schaffen Wettbewerbsvorteile.

**Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie möglicherweise
generische Dokumentenverarbeitung teilen, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.

**Ihre Daten und Trainings** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten,
aber die Daten selbst und die daraus abgeleiteten Erkenntnisse sind Ihr Wettbewerbsvorteil.

**Ihre Geschäftsinnovation** ist der Ort, an dem Wettbewerb stattfinden sollte. Anstatt darum zu konkurrieren, wer
bessere Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Je mehr Organisationen den Swiss AI Hub übernehmen, desto stärker wird das Ökosystem:

**Die Entwicklung beschleunigt sich**, da gemeinsame Muster entstehen und in das SDK kodiert werden. Was Wochen zum
Aufbau brauchte, wird zu einer Konfigurationsoption.

**Die Qualität verbessert sich** durch kollektives Debugging und Testen. Da viele Organisationen dieselbe Plattform
betreiben, werden Randfälle schnell entdeckt und behoben.

**Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation für die vollständige Entwicklung
bezahlt, werden die Kosten im gesamten Ökosystem verteilt.

**Die Innovation steigt**, weil Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu
implementieren, können sie neue Funktionen erkunden.

## Der Swiss AI Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

**Geschwindigkeit:** Neue Organisationen können Produktions-KI in Tagen statt Monaten deployen, indem sie bestehende
Arbeiten nutzen.

**Souveränität:** Schweizer Daten bleiben in der Schweiz, verarbeitet durch schweizerisch kontrollierte Infrastruktur,
unter Schweizer Recht.

**Unabhängigkeit:** Kein einzelner Anbieter kontrolliert die Plattform. Keine ausländische Firma kann Bedingungen ändern
oder den Zugang beschneiden.

**Qualität:** Kollektive Investitionen führen zu einer besseren Infrastruktur, als jede einzelne Organisation aufbauen
könnte.

**Innovation:** Befreit von Infrastrukturfragen konzentrieren sich Organisationen auf Geschäftsinnovationen, wo der
wahre Wert liegt.

## Kollaboration zum Erfolg führen

Das Ökosystem ist erfolgreich, weil es Anreize korrekt ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen
nicht-differenzierende Fähigkeiten, weil Zusammenarbeit wertvoller ist als Geheimhaltung. Sie halten strategische
Innovationen privat, weil Apache 2.0 beide Ansätze erlaubt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Zusammenarbeit, aber das Ökosystem wird von seinen
Mitgliedern aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beiträgt oder Wissen teilt, stärkt
die Schweizer KI-Fähigkeiten kollektiv.

So konkurriert die Schweiz global: nicht durch einzelne Organisationen, die versuchen, mit den Ressourcen von Big Tech
gleichzuziehen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das zu
konzentrieren, was sie einzigartig macht. Die Plattform ist die Commodity-Schicht, die Innovation ermöglicht.
