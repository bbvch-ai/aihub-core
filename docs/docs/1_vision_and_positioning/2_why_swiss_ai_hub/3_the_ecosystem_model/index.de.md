---
title: Das Ökosystem-Modell
source_sha: "706ece8d3491f90543ea15bc96d04d42f10ba8201f2bf141e9781c7b56b063d7"
---

# Das Ökosystem-Modell: Wie alle davon profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsvorteil sein sollte. Grundlegende Fähigkeiten wie LLM-Zugriff, Dokumentenverarbeitung und RAG sollten Güter sein, die allen zur Verfügung stehen. Schweizer Organisationen sollten auf ihrer Domänenexpertise und Geschäftsinnovation konkurrieren, nicht darauf, wer bessere Authentifizierungssysteme oder Vektordatenbanken aufbauen kann.

## Die Schweizer Chance

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft konkurriert, die von Tech-Giganten dominiert wird. Während Google, Microsoft und Amazon Milliarden in KI-Infrastruktur stecken, fehlt es Schweizer Unternehmen individuell an den Ressourcen, um diese Investition zu erreichen. Die typische Reaktion wäre, die Abhängigkeit von ausländischen Plattformen zu akzeptieren, aber die Schweiz hat eine andere Option: die Zusammenarbeit.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Ansatz zur KI transformieren. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf die Grundlage konzentrieren und gleichzeitig auf der Anwendungsschicht konkurrieren. Hier geht es nicht darum, den Wettbewerb zu eliminieren; es geht darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Gut

Betrachten Sie, was jede Organisation, die KI aufbaut, benötigt:

- Sicherer Modellzugriff mit Kostenkontrollen
- Dokumentenverarbeitung und Vektorspeicherung
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsbedürfnisse einer Bank unterscheiden sich nicht grundlegend von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung spiegeln die eines Fertigungsunternehmens wider. Doch heute baut jede Organisation diese Fähigkeiten entweder separat auf oder gibt sich einer ausländischen Plattform hin.

Der Swiss AI Hub macht diese Infrastruktur zu einem Gut. Deployen Sie die Plattform einmal, und diese Probleme sind gelöst. Jede Verbesserung der Kernplattform kommt jeder Organisation zugute, die sie nutzt. Wenn jemand eine bessere Dokumentenanalyse beisteuert, verbessert sich die Dokumentenverarbeitung aller. Wenn jemand eine neue Sicherheitsfunktion hinzufügt, werden alle sicherer.

## Die Beitragsdynamik

Die Runtime, das SDK, die Agents, Pipelines und Prozesse der Swiss AI Hub Plattform sind unter Apache 2.0 lizenziert. (Die Web-UI und die Backup-Orchestrierung sind AGPL-3.0; die Multi-Tenant-Management-Ebene ist proprietär. Eine detaillierte Aufschlüsselung pro Paket finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).) Die permissive Lizenz für die Runtime + SDK schafft natürliche Anreize zur Zusammenarbeit, ohne sie zu erzwingen.

**Gemeinsam genutzte Infrastruktur kommt allen zugute:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das Teilen sinnvoll, weil alle davon profitieren. Eine Bank, die eine bessere Compliance-Protokollierung hinzufügt, hilft jeder regulierten Branche. Ein Gesundheitsdienstleister, der den Umgang mit PII verbessert, hilft allen mit Datenschutzbedenken. Diese Beiträge fließen natürlich zurück, weil eine bessere gemeinsame Infrastruktur die Kosten aller senkt.

**Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung, Ihre Domänenexpertise verkörpert – diese bleiben Ihre. Die Apache 2.0 Runtime erfordert kein Zurückgeben von Beiträgen, sodass Sie strategische Innovationen privat halten können, während Sie von der gemeinsamen Infrastruktur profitieren und dazu beitragen.

## Warum Lizenzen für KI-Infrastruktur wichtig sind

Das Verständnis von Softwarelizenzen ist beim Aufbau von KI-Infrastruktur entscheidend. Viele Organisationen machen kostspielige Fehler, indem sie davon ausgehen, dass Code auf GitHub automatisch kostenlos nutzbar ist – das ist er nicht.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ kostenlose Nutzung.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre Software mit restriktiven Lizenzen. Die Möglichkeit, Code zu *sehen* oder herunterzuladen, bedeutet nicht, dass Sie ihn legal *nutzen* dürfen, insbesondere nicht in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use License“ (keine Open-Source-Lizenz). Obwohl Sie es herunterladen und ausführen können, verbietet die Lizenz die kommerzielle Nutzung ohne den Kauf einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Lizenzkategorien erklärt

**Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren weitreichende Freiheiten – Nutzung, Änderung, kommerzielle Verbreitung, private Haltung von Modifikationen. Keine Bedingungen. Diese sind ideal für den Aufbau von Geschäftsinfrastruktur.

**Copyleft-Lizenzen** (GPL, AGPL): Erfordern, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung quelloffen machen. **AGPL erweitert dies auf die Netzwerknutzung** – selbst das Anbieten der Software als Service löst diese Anforderung aus. Dies macht Copyleft zu einer schlechten Wahl für die Bausteine, die Sie mit proprietärer Logik erweitern – genau aus diesem Grund sind die Swiss AI Hub Runtime und das SDK permissiv, nicht Copyleft. (Copyleft ist die richtige Wahl für Endbenutzeranwendungen wie die UI; siehe unten.)

**Source-available-Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use“): Ermöglichen Ihnen das Anzeigen und manchmal auch die Nutzung des Codes, erlegen jedoch strenge Beschränkungen auf – oft ist die kommerzielle Nutzung, Managed Services oder konkurrierende Produkte verboten. Nicht quelloffen, obwohl sie auf GitHub erscheinen.

**Proprietäre/Kundenspezifische Lizenzen**: Variieren stark. Erfordern eine sorgfältige rechtliche Prüfung. Verbieten oft die Nutzung in der Produktion ohne Bezahlung.

### Lizenzen, die in KI-Infrastruktur vermieden werden sollten

Für KI-Produktionssysteme sollten Sie extrem vorsichtig sein mit:

-   **AGPL/GPL**: Zwingen Ihr gesamtes System zur Offenlegung des Quellcodes, wenn Sie die Software modifizieren und vertreiben
-   **SSPL (Server Side Public License)**: MongoDBs Versuch, Cloud-Anbieter daran zu hindern, Managed Services anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus
-   **Elastic License v2**: Verbietet das Anbieten der Software als konkurrierenden Service
-   **Business Source License (BSL)**: Zeitverzögertes Open Source; restriktiv bis zum Ablaufdatum
-   **Benutzerdefinierte „Source-available“-Lizenzen**: Verbieten in der Regel die kommerzielle Nutzung oder haben unklare Bedingungen

Diese Lizenzen mögen anfangs akzeptabel erscheinen, schaffen aber rechtliche Fallstricke, wenn Sie skalieren, Services anbieten oder in Kundensysteme integrieren – **wenn sie sich unter dem Code befinden, auf dem Sie aufbauen**. Genau aus diesem Grund hält der Swiss AI Hub die Runtime und das SDK permissiv. Die Web-UI und die Backup-Orchestrierung sind eine bewusste Ausnahme: Sie sind AGPL-3.0, *weil* sie Endbenutzeranwendungen und keine Bausteine sind, sodass Copyleft Community-Verbesserungen schützt, ohne jemals Ihre Agents oder Geschäftslogik zur Offenlegung zu zwingen.

### Unser Lizenzierungs-Engagement

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externe Docker-Images. Wir verifizieren, dass jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit überprüft und genehmigt wurde.

**Sie erhalten die Freiheit, die die Lizenz jedes Pakets gewährt – siehe [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die genauen Bedingungen pro Paket.** Kurz gesagt: Die Runtime + SDK (Apache 2.0) legen keine Beschränkungen für die kommerzielle Nutzung oder die Integration mit proprietären Systemen fest; die Web-UI und die Backup-Orchestrierung (AGPL-3.0) erfordern die Offenlegung des Quellcodes Ihrer Modifikationen, wenn Sie diese als Netzwerkservice anbieten; die Multi-Tenant-Administrationsplattform ist proprietär und erfordert eine kommerzielle Lizenz.

**Warum Apache 2.0 speziell für die Runtime und das SDK:** Apache 2.0 ist nicht nur permissiv, sondern enthält auch explizite Patenterteilungen, die Sie vor Patentansprüchen von Mitwirkenden schützen. Es wird von Unternehmen geschätzt, von Rechtsteams gut verstanden und ist mit praktisch allen anderen Lizenzen kompatibel. Es ist der Goldstandard für kollaborative Infrastruktur – was genau die Rolle der Runtime und des SDK ist.

Dies ist nicht nur Idealismus – es ist Pragmatismus. Eine permissive Runtime + SDK beseitigt Adoptionsbarrieren und verhindert einen Vendor Lock-in für die Bausteine, die Sie erweitern; die AGPL-Komponenten schützen vor feindseligen SaaS-Rehosts der UI, ohne die Bausteine zu belasten; die proprietäre Ebene finanziert die fortgesetzte Entwicklung.

## Echte Kollaborationsmuster

Das Ökosystem zeigt bereits, wie dies funktioniert:

**Gemeinsam genutzte Komponenten:** Gängige Agents für Dokumentenzusammenfassung, Frage-Antwort-Systeme und Datenextraktion werden zu Community-Assets. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.

**Branchenlösungen:** Gesundheitsorganisationen arbeiten an der Verarbeitung medizinischer Dokumente zusammen. Finanzdienstleister teilen Compliance-fokussierte Agents. Diese branchenspezifischen Lösungen entstehen natürlich, wenn Organisationen erkennen, dass ihre Konkurrenten im Ausland, nicht im Inland, die eigentliche Bedrohung darstellen.

**Infrastrukturverbesserungen:** Performance-Optimierungen, Sicherheitsverbesserungen und operative Tools fließen in die Plattform zurück. Alle profitieren von einer schnelleren, sichereren, zuverlässigeren Grundlage.

**Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Die gleiche Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystem-Modell eliminiert den Wettbewerb nicht; es konzentriert ihn dort, wo er wichtig ist:

**Ihre Domänenexpertise** bleibt Ihre. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre Markteinblicke nicht. Diese schaffen Wettbewerbsvorteile.

**Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie möglicherweise generische Dokumentenverarbeitung teilen, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.

**Ihre Daten und Trainings** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten, aber die Daten selbst und die daraus abgeleiteten Erkenntnisse sind Ihr Wettbewerbsvorteil.

**Ihre Geschäftsinnovation** ist der Ort, an dem Wettbewerb stattfinden sollte. Anstatt darum zu konkurrieren, wer bessere Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Je mehr Organisationen den Swiss AI Hub adoptieren, desto stärker wird das Ökosystem:

**Die Entwicklung beschleunigt sich**, weil gemeinsame Muster entstehen und in das SDK kodiert werden. Was Wochen zum Bauen dauerte, wird zu einer Konfigurationsoption.

**Die Qualität verbessert sich** durch kollektives Debugging und Testen. Da viele Organisationen dieselbe Plattform betreiben, werden Randfälle schnell entdeckt und behoben.

**Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation für die vollständige Entwicklung bezahlt, werden die Kosten auf das gesamte Ökosystem verteilt.

**Die Innovation nimmt zu**, weil Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu implementieren, können sie neue Fähigkeiten erkunden.

## Der Schweizer KI-Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

**Geschwindigkeit:** Neue Organisationen können Produktions-KI in Tagen statt in Monaten deployen, indem sie bestehende Arbeiten nutzen.

**Souveränität:** Schweizer Daten bleiben in der Schweiz, werden von Schweizer kontrollierter Infrastruktur verarbeitet und unterliegen Schweizer Recht.

**Unabhängigkeit:** Kein einzelner Anbieter kontrolliert die Plattform. Kein ausländisches Unternehmen kann Bedingungen ändern oder den Zugang sperren.

**Qualität:** Kollektive Investitionen führen zu einer besseren Infrastruktur, als jede einzelne Organisation aufbauen könnte.

**Innovation:** Befreit von Infrastrukturfragen konzentrieren sich Organisationen auf Geschäftsinnovationen, wo der wahre Wert liegt.

## Kollaboration erfolgreich gestalten

Das Ökosystem ist erfolgreich, weil es Anreize korrekt ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen nicht-differenzierende Fähigkeiten, weil Zusammenarbeit wertvoller ist als Geheimhaltung. Sie halten strategische Innovationen privat, weil Apache 2.0 beide Ansätze erlaubt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Zusammenarbeit, aber das Ökosystem wird von seinen Mitgliedern aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beisteuert oder Wissen teilt, stärkt die Schweizer KI-Fähigkeiten kollektiv.

So konkurriert die Schweiz global: nicht durch einzelne Organisationen, die versuchen, die Ressourcen von Big Tech zu erreichen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das zu konzentrieren, was sie einzigartig macht. Die Plattform ist die Rohstoffschicht, die Innovation ermöglicht.
