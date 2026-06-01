---
title: Das Ökosystemmodell
source_sha: "f804e02367c68804611981712e75df9ea5e11be6012415bf37e35ac32d6c107e"
---

# Das Ökosystemmodell: Wie alle profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsvorteil sein sollte. Grundlegende Funktionen wie LLM-Zugang, Dokumentenverarbeitung und RAG sollten Güter sein, die jedem zur Verfügung stehen. Schweizer Organisationen sollten auf ihrer Domänenexpertise und Geschäftsinnovation konkurrieren, nicht darauf, wer bessere Authentifizierungssysteme oder Vektordatenbanken bauen kann.

## Die Schweizer Gelegenheit

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft konkurriert, die von Tech-Giganten dominiert wird. Während Google, Microsoft und Amazon Milliarden in KI-Infrastruktur investieren, fehlen Schweizer Unternehmen individuell die Ressourcen, um diese Investition zu erreichen. Die typische Antwort wäre, die Abhängigkeit von ausländischen Plattformen zu akzeptieren, aber die Schweiz hat eine andere Option: die Zusammenarbeit.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Umgang mit KI verändern. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf die Grundlage konzentrieren, während wir auf der Anwendungsebene konkurrieren. Hier geht es nicht darum, den Wettbewerb zu eliminieren; es geht darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Commodity

Bedenken Sie, was jede Organisation, die KI aufbaut, benötigt:

- Sicherer Modellzugriff mit Kostenkontrollen
- Dokumentenverarbeitung und Vektorspeicherung
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsbedürfnisse einer Bank unterscheiden sich im Grunde nicht von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung ähneln denen eines produzierenden Unternehmens. Doch heute baut jede Organisation diese Funktionen entweder separat auf oder unterwirft sich einer ausländischen Plattform.

Der Swiss AI Hub macht diese Infrastruktur zu einem Commodity. Deployen Sie die Plattform einmal, und diese Probleme sind gelöst. Jede Verbesserung der Kernplattform kommt jeder Organisation zugute, die sie nutzt. Wenn jemand eine bessere Dokumentenanalyse beiträgt, verbessert sich die Dokumentenverarbeitung aller. Wenn jemand eine neue Sicherheitsfunktion hinzufügt, werden alle sicherer.

## Die Dynamik der Beiträge

Die Swiss AI Hub Plattform-Laufzeitumgebung, das SDK, die Agents, Pipelines und Prozesse sind unter Apache 2.0 lizenziert. (Die Web-UI und die Backup-Orchestrierung sind AGPL-3.0; die Multi-Tenant-Management-Ebene ist proprietär. Eine detaillierte Aufschlüsselung pro Paket finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).) Die permissive Lizenz für die Laufzeitumgebung und das SDK schafft natürliche Anreize zur Zusammenarbeit, ohne sie zu erzwingen.

**Geteilte Infrastruktur nützt allen:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das Teilen sinnvoll, weil alle davon profitieren. Eine Bank, die bessere Compliance-Protokollierung hinzufügt, hilft jeder regulierten Branche. Ein Gesundheitsdienstleister, der den Umgang mit PII verbessert, hilft allen mit Datenschutzbedenken. Diese Beiträge fließen natürlich zurück, weil eine bessere gemeinsame Infrastruktur die Kosten aller senkt.

**Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung, Ihre Domänenexpertise verkörpert – diese bleiben Ihnen. Die Apache 2.0-Laufzeitumgebung erfordert keine Rückgabe von Inhalten, sodass Sie strategische Innovationen privat halten können, während Sie von der gemeinsamen Infrastruktur profitieren und dazu beitragen.

## Warum Lizenzierung für KI-Infrastruktur wichtig ist

Das Verständnis von Softwarelizenzierung ist entscheidend beim Aufbau von KI-Infrastruktur. Viele Organisationen machen kostspielige Fehler, indem sie annehmen, dass Code auf GitHub automatisch kostenlos zu verwenden ist – das ist nicht der Fall.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ kostenlos nutzbar.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre Software mit restriktiven Lizenzen. Die Möglichkeit, Code *anzusehen* oder *herunterzuladen*, bedeutet nicht, dass Sie rechtlich dazu berechtigt sind, ihn zu *nutzen*, insbesondere in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use License" (keine Open-Source-Lizenz). Obwohl Sie es herunterladen und ausführen können, verbietet die Lizenz die kommerzielle Nutzung ohne den Kauf einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Lizenzkategorien erklärt

**Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren weitreichende Freiheiten – kommerzielle Nutzung, Modifikation, Verbreitung, private Weiterentwicklung von Modifikationen. Keine Einschränkungen. Diese sind ideal für den Aufbau von Geschäftsinfrastruktur.

**Copyleft-Lizenzen** (GPL, AGPL): Erfordern, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung als Open Source veröffentlichen. **AGPL erweitert dies auf die Netzwerkverwendung** – selbst das Anbieten der Software als Service löst diese Anforderung aus. Dies macht Copyleft zu einer schlechten Wahl für die Bausteine, die Sie mit proprietärer Logik erweitern – genau deshalb sind die Swiss AI Hub Laufzeitumgebung und das SDK permissiv und nicht Copyleft. (Copyleft ist die richtige Wahl für Endbenutzeranwendungen wie die UI; siehe unten.)

**Source-available-Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use"): Erlauben das Anzeigen und manchmal auch die Nutzung des Codes, aber auferlegen strenge Einschränkungen – oft verbieten sie die kommerzielle Nutzung, Managed Services oder konkurrierende Produkte. Trotz ihres Erscheinens auf GitHub sind sie nicht Open Source.

**Proprietäre/kundenspezifische Lizenzen**: Variieren stark. Erfordern eine sorgfältige rechtliche Prüfung. Verbieten oft die Nutzung in der Produktion ohne Bezahlung.

### Lizenzen, die in KI-Infrastruktur zu vermeiden sind

Für Produktions-KI-Systeme sollten Sie äusserst vorsichtig sein mit:

- **AGPL/GPL**: Zwingen Ihr gesamtes System in den Open-Source-Bereich, wenn Sie die Software modifizieren und verbreiten
- **SSPL (Server Side Public License)**: MongoDBs Versuch, Cloud-Anbieter daran zu hindern, Managed-Versionen anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus
- **Elastic License v2**: Verbietet das Anbieten der Software als konkurrierenden Service
- **Business Source License (BSL)**: Zeitlich verzögertes Open Source; restriktiv bis zum Ablaufdatum
- **Benutzerdefinierte „source-available“-Lizenzen**: Verbieten in der Regel die kommerzielle Nutzung oder haben unklare Bedingungen

Diese Lizenzen mögen zunächst akzeptabel erscheinen, schaffen aber rechtliche Fallstricke, wenn Sie skalieren, Services anbieten oder mit Kundensystemen integrieren – **wenn sie unter dem Code liegen, auf dem Sie aufbauen**. Genau deshalb hält der Swiss AI Hub die Laufzeitumgebung und das SDK permissiv. Die Web-UI und die Backup-Orchestrierung sind eine bewusste Ausnahme: Sie sind AGPL-3.0, *weil* sie Endbenutzeranwendungen und keine Bausteine sind, sodass Copyleft Community-Verbesserungen schützt, ohne jemals Ihre Agents oder Geschäftslogik offenzulegen.

### Unser Lizenzierungsengagement

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externen Docker-Images. Wir überprüfen, dass jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit geprüft und genehmigt wurde.

**Sie erhalten die Freiheit, die die Lizenz jedes Pakets gewährt – siehe [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) für die genauen Bedingungen pro Paket.** Kurz gesagt: Die Laufzeitumgebung + SDK (Apache 2.0) legen keine Beschränkungen für die kommerzielle Nutzung oder die Integration mit proprietären Systemen fest; die Web-UI und die Backup-Orchestrierung (AGPL-3.0) erfordern die Offenlegung des Quellcodes Ihrer Modifikationen, wenn Sie sie als Netzwerkdienst anbieten; die Multi-Tenant-Verwaltungsebene ist proprietär und erfordert eine kommerzielle Lizenz.

**Warum Apache 2.0 speziell für die Laufzeitumgebung und das SDK:** Neben der Permissivität enthält Apache 2.0 explizite Patenterteilungen, die Sie vor Patentansprüchen von Mitwirkenden schützen. Es wird von Unternehmen geschätzt, von Rechtsteams gut verstanden und ist mit praktisch allen anderen Lizenzen kompatibel. Es ist der Goldstandard für kollaborative Infrastruktur – was genau die Rolle der Laufzeitumgebung und des SDK ist.

Das ist nicht nur Idealismus – es ist Pragmatismus. Eine permissive Laufzeitumgebung + SDK beseitigt Adoptionsbarrieren und verhindert Vendor Lock-in für die Bausteine, die Sie erweitern; die AGPL-Komponenten schützen vor feindlichen SaaS-Rehosts der UI, ohne die Bausteine zu belasten; die proprietäre Ebene finanziert die weitere Entwicklung.

## Echte Kollaborationsmuster

Das Ökosystem zeigt bereits, wie dies funktioniert:

- **Gemeinsame Komponenten:** Gängige Agents für Dokumentenzusammenfassungen, Fragenbeantwortung und Datenextraktion werden zu Gemeinschaftsgütern. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.
- **Branchenlösungen:** Gesundheitsorganisationen arbeiten bei der medizinischen Dokumentenverarbeitung zusammen. Finanzdienstleister teilen auf Compliance ausgerichtete Agents. Diese branchenspezifischen Lösungen entstehen natürlich, wenn Organisationen erkennen, dass ihre Konkurrenten im Ausland und nicht im Inland die wahre Bedrohung sind.
- **Infrastrukturverbesserungen:** Performance-Optimierungen, Sicherheitsverbesserungen und operative Tools fliessen zurück zur Plattform. Alle profitieren von einer schnelleren, sichereren und zuverlässigeren Grundlage.
- **Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Dieselbe Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystemmodell eliminiert den Wettbewerb nicht; es konzentriert ihn dort, wo er wichtig ist:

- **Ihre Domänenexpertise** bleibt Ihre. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre Markteinblicke nicht. Diese schaffen Wettbewerbsvorteile.
- **Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie möglicherweise generische Dokumentenverarbeitung teilen, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.
- **Ihre Daten und Trainings** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten, aber die Daten selbst und die daraus abgeleiteten Erkenntnisse sind Ihr Wettbewerbsvorteil.
- **Ihre Geschäftsinnovation** ist der Bereich, in dem Wettbewerb stattfinden sollte. Anstatt zu konkurrieren, wer bessere Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Wenn mehr Organisationen den Swiss AI Hub adoptieren, stärkt sich das Ökosystem:

- **Die Entwicklung beschleunigt sich**, da gemeinsame Muster entstehen und in das SDK integriert werden. Was Wochen zum Aufbau benötigte, wird zu einer Konfigurationsoption.
- **Die Qualität verbessert sich** durch kollektives Debugging und Tests. Da viele Organisationen dieselbe Plattform betreiben, werden Randfälle schnell entdeckt und behoben.
- **Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation für die vollständige Entwicklung bezahlt, werden die Kosten im gesamten Ökosystem verteilt.
- **Die Innovation steigt**, weil Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu implementieren, können sie neue Funktionen erkunden.

## Der Schweizer KI-Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

- **Geschwindigkeit:** Neue Organisationen können Produktions-KI in Tagen statt Monaten deployen, indem sie auf bestehende Arbeit zurückgreifen.
- **Souveränität:** Schweizer Daten bleiben in der Schweiz, werden von Schweizer-kontrollierter Infrastruktur verarbeitet und unterliegen Schweizer Recht.
- **Unabhängigkeit:** Kein einzelner Anbieter kontrolliert die Plattform. Kein ausländisches Unternehmen kann Bedingungen ändern oder den Zugang unterbrechen.
- **Qualität:** Kollektive Investitionen führen zu einer besseren Infrastruktur, als jede einzelne Organisation aufbauen könnte.
- **Innovation:** Befreit von Infrastrukturbedenken konzentrieren sich Organisationen auf Geschäftsinnovationen, wo der wahre Wert liegt.

## Kollaboration erfolgreich gestalten

Das Ökosystem ist erfolgreich, weil es die Anreize korrekt ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen nicht-differenzierende Funktionen, weil Zusammenarbeit wertvoller ist als Geheimhaltung. Sie halten strategische Innovationen privat, weil Apache 2.0 beide Ansätze erlaubt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Zusammenarbeit, aber das Ökosystem wird von seinen Mitgliedern aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beisteuert oder Wissen teilt, stärkt die Schweizer KI-Fähigkeiten kollektiv.

So konkurriert die Schweiz global: nicht durch einzelne Organisationen, die versuchen, mit den Ressourcen der Big Tech gleichzuziehen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das zu konzentrieren, was sie einzigartig macht. Die Plattform ist die Commodity-Schicht, die Innovation ermöglicht.
