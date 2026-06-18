---
title: Das Ökosystem-Modell
source_sha: d857b20fb83cf52b5cdaeb29210842d5bde91b7b5f362db892483cc9aa9b6164
---

# Das Ökosystem-Modell: Wie alle profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsdifferenzierungsmerkmal sein sollte. Grundlegende
Fähigkeiten wie LLM-Zugang, Dokumentenverarbeitung und RAG sollten Commodities sein, die für jeden verfügbar sind.
Schweizer Organisationen sollten in ihrer Domänenexpertise und Geschäftsinnovation konkurrieren, nicht darin, wer
bessere Authentifizierungssysteme oder Vektordatenbanken aufbauen kann.

## Die Schweizer Chance

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft im Wettbewerb mit Technologiegiganten steht. Während
Google, Microsoft und Amazon Milliarden in KI-Infrastruktur investieren, fehlen den Schweizer Unternehmen einzeln die
Ressourcen, um diese Investition zu erreichen. Die typische Antwort wäre, die Abhängigkeit von ausländischen Plattformen
zu akzeptieren, aber die Schweiz hat eine andere Option: Kollaboration.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Umgang mit KI
verändern. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf die
Grundlage bündeln, während wir auf der Anwendungsschicht konkurrieren. Hier geht es nicht darum, den Wettbewerb zu
eliminieren; es geht darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Commodity

Betrachten Sie, was jede Organisation, die KI entwickelt, benötigt:

- Sicheren Modellzugang mit Kostenkontrollen
- Dokumentenverarbeitung und Vektorspeicherung
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsbedürfnisse einer Bank unterscheiden sich nicht grundlegend
von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung
spiegeln die einer Fertigungsfirma wider. Doch heute baut jede Organisation diese Fähigkeiten entweder separat auf oder
kapituliert vor einer ausländischen Plattform.

Der Swiss AI Hub macht diese Infrastruktur zu einer Commodity. Deployen Sie die Plattform einmal, und diese Probleme
sind gelöst. Jede Verbesserung der Kernplattform kommt jeder Organisation zugute, die sie nutzt. Wenn jemand eine
bessere Dokumentenanalyse beiträgt, verbessert sich die Dokumentenverarbeitung für alle. Wenn jemand eine neue
Sicherheitsfunktion hinzufügt, werden alle sicherer.

## Die Dynamik der Beiträge

Die Swiss AI Hub Plattform-Runtime, das SDK, Agents, Pipelines und Prozesse sind unter Apache 2.0 lizenziert. (Die
Web-UI, die Multi-Tenant-Verwaltungsebene und die Backup-Orchestrierung sind AGPL-3.0-or-later. Eine detaillierte
Aufschlüsselung pro Paket finden Sie in [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).)
Die permissive Lizenz für Runtime + SDK schafft natürliche Anreize zur Kollaboration, ohne sie zu erzwingen.

**Geteilte Infrastruktur nützt allen:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das Teilen sinnvoll,
weil alle davon profitieren. Eine Bank, die bessere Compliance-Logging-Funktionen hinzufügt, hilft jeder regulierten
Branche. Ein Gesundheitsdienstleister, der den Umgang mit PII verbessert, hilft allen mit Datenschutzbedenken. Diese
Beiträge fliessen auf natürliche Weise zurück, da eine bessere gemeinsame Infrastruktur die Kosten aller senkt.

**Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der
kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung, Ihre
Domänenexpertise verkörpert – diese bleiben Ihnen. Die Apache 2.0-Runtime erfordert kein Zurückteilen, sodass Sie
strategische Innovationen privat halten können, während Sie von der gemeinsamen Infrastruktur profitieren und zu ihr
beitragen.

## Warum Lizenzierung für KI-Infrastruktur wichtig ist

Das Verständnis von Softwarelizenzierung ist beim Aufbau von KI-Infrastruktur entscheidend. Viele Organisationen machen
kostspielige Fehler, indem sie annehmen, dass Code auf GitHub automatisch kostenlos nutzbar ist – das ist er nicht.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ kostenlose Nutzung.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre
Software mit restriktiven Lizenzen. Die Möglichkeit, Code zu *sehen* oder *herunterzuladen*, bedeutet nicht, dass Sie
ihn legal *nutzen* dürfen, insbesondere in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use
License“ (keine Open-Source-Lizenz). Obwohl Sie es herunterladen und ausführen können, verbietet die Lizenz die
kommerzielle Nutzung ohne den Kauf einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen
entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Lizenzkategorien erklärt

**Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren weitreichende Freiheiten – kommerzielle Nutzung, Modifikation,
Distribution, private Beibehaltung von Modifikationen. Keine Bedingungen. Diese sind ideal für den Aufbau von
Geschäftsinfrastruktur.

**Copyleft-Lizenzen** (GPL, AGPL): Erfordern, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz
veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung Open
Source machen. **AGPL erweitert dies auf die Netzwerk-Nutzung** – selbst das Anbieten der Software als Service löst
diese Anforderung aus. Dies macht Copyleft zu einer schlechten Wahl für die Bausteine, die Sie mit proprietärer Logik
erweitern – genau deshalb sind die Swiss AI Hub Runtime und das SDK permissiv, nicht Copyleft. (Copyleft ist die
richtige Wahl für Endbenutzeranwendungen wie die UI; siehe unten.)

**Source-Available-Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use“): Ermöglichen es Ihnen, den Code anzusehen
und manchmal auch zu verwenden, aber sie auferlegen strenge Beschränkungen – oft verbieten sie die kommerzielle Nutzung,
Managed Services oder konkurrierende Produkte. Trotz ihres Erscheinens auf GitHub sind sie nicht Open Source.

**Proprietäre/Benutzerdefinierte Lizenzen**: Variieren stark. Erfordern eine sorgfältige rechtliche Prüfung. Verbieten
oft die Produktionsnutzung ohne Bezahlung.

### Zu vermeidende Lizenzen in der KI-Infrastruktur

Für KI-Produktionssysteme sollten Sie äusserst vorsichtig sein mit:

- **AGPL/GPL**: Zwingen Ihr gesamtes System, Open Source zu sein, wenn Sie die Software modifizieren und vertreiben.
- **SSPL (Server Side Public License)**: MongoDBs Versuch, Cloud-Anbieter daran zu hindern, Managed-Versionen
  anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus.
- **Elastic License v2**: Verbietet das Anbieten der Software als konkurrierenden Service.
- **Business Source License (BSL)**: Zeitverzögerte Open Source; restriktiv bis zum Ablaufdatum.
- **Benutzerdefinierte „Source-Available“-Lizenzen**: Verbieten in der Regel die kommerzielle Nutzung oder haben unklare
  Bedingungen.

Diese Lizenzen mögen anfänglich akzeptabel erscheinen, schaffen aber rechtliche Stolperfallen, wenn Sie skalieren,
Services anbieten oder sich in Kundensysteme integrieren – **wenn sie unter dem Code liegen, auf dem Sie aufbauen**.
Genau deshalb hält der Swiss AI Hub die Runtime und das SDK permissiv. Die Web-UI und die Backup-Orchestrierung sind
eine bewusste Ausnahme: Sie sind AGPL-3.0-or-later, *weil* sie Endbenutzeranwendungen und keine Bausteine sind, sodass
Copyleft Gemeinschaftsverbesserungen schützt, ohne jemals Ihre Agents oder Geschäftslogik zur Offenlegung zu zwingen.

### Unser Engagement für Lizenzierung

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externen
Docker-Images. Wir überprüfen, ob jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit
überprüft und genehmigt wurde.

**Sie erhalten die Freiheit, die die Lizenz jedes Pakets gewährt – die genauen Bedingungen pro Paket finden Sie unter
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).** Kurz gesagt: Die Runtime + das SDK
(Apache 2.0) legen keine Beschränkungen für die kommerzielle Nutzung oder die Integration mit proprietären Systemen
fest; die Web-UI, die Multi-Tenant-Verwaltungsebene und die Backup-Orchestrierung (AGPL-3.0-or-later) erfordern die
Offenlegung Ihrer Modifikationen, wenn Sie diese als Netzwerkdienst anbieten.

**Warum Apache 2.0 speziell für die Runtime und das SDK:** Neben der Permissivität umfasst Apache 2.0 explizite
Patenterteilungen, die Sie vor Patentansprüchen von Mitwirkenden schützen. Sie wird von Unternehmen geschätzt, von
Rechtsteams gut verstanden und ist mit praktisch allen anderen Lizenzen kompatibel. Sie ist der Goldstandard für
kollaborative Infrastruktur – genau die Rolle der Runtime und des SDK.

Dies ist nicht nur Idealismus – es ist Pragmatismus. Eine permissive Runtime + ein SDK beseitigen Akzeptanzbarrieren und
verhindern Vendor Lock-in für die Bausteine, die Sie erweitern; die AGPL-Komponenten schützen vor feindlichen
SaaS-Rehosts der UI und der Verwaltungsebene, ohne die Bausteine zu belasten.

## Echte Kollaborationsmuster

Das Ökosystem zeigt bereits, wie dies funktioniert:

**Gemeinsame Komponenten:** Gängige Agents für Dokumentenzusammenfassung, Fragenbeantwortung und Datenextraktion werden
zu Gemeinschaftsgütern. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.

**Branchenlösungen:** Gesundheitsorganisationen kollaborieren bei der medizinischen Dokumentenverarbeitung.
Finanzdienstleister teilen Compliance-fokussierte Agents. Diese branchenspezifischen Lösungen entstehen natürlich, wenn
Organisationen erkennen, dass ihre Konkurrenten im Ausland, nicht im Inland, die eigentliche Bedrohung sind.

**Infrastrukturverbesserungen:** Performance-Optimierungen, Sicherheitsverbesserungen und operative Tools fliessen in
die Plattform zurück. Alle profitieren von einer schnelleren, sichereren und zuverlässigeren Grundlage.

**Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Dieselbe
Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystem-Modell eliminiert den Wettbewerb nicht; es konzentriert ihn auf das, worauf es ankommt:

**Ihre Domänenexpertise** bleibt Ihre. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre
Markteinblicke nicht. Diese schaffen Wettbewerbsvorteile.

**Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie generische
Dokumentenverarbeitung teilen könnten, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.

**Ihre Daten und Ihr Training** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten,
aber die Daten selbst und die daraus abgeleiteten Erkenntnisse sind Ihr Wettbewerbsvorteil.

**Ihre Geschäftsinnovation** ist der Ort, an dem Wettbewerb stattfinden sollte. Anstatt darum zu konkurrieren, wer
bessere Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Wenn mehr Organisationen den Swiss AI Hub einführen, stärkt sich das Ökosystem:

**Die Entwicklung beschleunigt sich**, da gemeinsame Muster entstehen und in das SDK kodiert werden. Was Wochen zum
Aufbau dauerte, wird zu einer Konfigurationsoption.

**Die Qualität verbessert sich** durch kollektives Debugging und Testen. Da viele Organisationen dieselbe Plattform
betreiben, werden Edge Cases schnell entdeckt und behoben.

**Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation die komplette Entwicklung bezahlt,
verteilen sich die Kosten auf das gesamte Ökosystem.

**Die Innovation steigt**, da Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu
implementieren, können sie neue Fähigkeiten erkunden.

## Der Schweizer KI-Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

**Geschwindigkeit:** Neue Organisationen können produktive KI in Tagen, nicht in Monaten, durch die Nutzung bestehender
Arbeiten deployen.

**Souveränität:** Schweizer Daten bleiben in der Schweiz, verarbeitet von schweizerisch kontrollierter Infrastruktur,
reguliert durch schweizerisches Recht.

**Unabhängigkeit:** Kein einzelner Vendor kontrolliert die Plattform. Kein ausländisches Unternehmen kann Bedingungen
ändern oder den Zugang sperren.

**Qualität:** Kollektive Investitionen führen zu einer besseren Infrastruktur, als jede einzelne Organisation aufbauen
könnte.

**Innovation:** Von Infrastrukturproblemen befreit, konzentrieren sich Organisationen auf Geschäftsinnovation, wo der
wahre Wert liegt.

## Kollaboration erfolgreich gestalten

Das Ökosystem ist erfolgreich, weil es Anreize korrekt ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen
nicht-differenzierende Fähigkeiten, weil Kollaboration wertvoller ist als Geheimhaltung. Sie halten strategische
Innovationen privat, weil Apache 2.0 beide Ansätze erlaubt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Kollaboration, aber das Ökosystem wird von seinen Mitgliedern
aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beiträgt oder Wissen teilt, stärkt die Schweizer
KI-Fähigkeiten kollektiv.

So konkurriert die Schweiz global: nicht durch einzelne Organisationen, die versuchen, die Ressourcen der Big Tech zu
erreichen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das zu
konzentrieren, was sie einzigartig macht. Die Plattform ist die Commodity-Schicht, die Innovation ermöglicht.
