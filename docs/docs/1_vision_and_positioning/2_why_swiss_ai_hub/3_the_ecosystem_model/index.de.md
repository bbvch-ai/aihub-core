---
title: Das Ökosystem-Modell
source_sha: "f804e02367c68804611981712e75df9ea5e11be6012415bf37e35ac32d6c107e"
---

# Das Ökosystem-Modell: Wie alle profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsvorteil sein sollte. Grundlegende Fähigkeiten wie der Zugriff auf LLMs, Dokumentenverarbeitung und RAG sollten Güter sein, die jedem zur Verfügung stehen. Schweizer Organisationen sollten sich auf ihre Domänenexpertise und Geschäftsinnovation konzentrieren, nicht darauf, wer bessere Authentifizierungssysteme oder Vektordatenbanken bauen kann.

## Die Schweizer Chance

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft im Wettbewerb mit Tech-Giganten steht. Während Google, Microsoft und Amazon Milliarden in die KI-Infrastruktur investieren, fehlt es Schweizer Unternehmen einzeln an den Ressourcen, um diese Investition zu erreichen. Die typische Reaktion wäre, die Abhängigkeit von ausländischen Plattformen zu akzeptieren, aber die Schweiz hat eine andere Option: die Zusammenarbeit.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Umgang mit KI verändern. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf der Grundlage bündeln und gleichzeitig auf der Anwendungsschicht konkurrieren. Hier geht es nicht darum, den Wettbewerb zu eliminieren, sondern darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Ware

Betrachten Sie, was jede Organisation, die KI entwickelt, benötigt:

- Sicherer Modellzugriff mit Kostenkontrollen
- Dokumentenverarbeitung und Vektorspeicherung
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsbedürfnisse einer Bank unterscheiden sich nicht grundlegend von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung spiegeln die einer Fertigungsfirma wider. Dennoch baut jede Organisation diese Fähigkeiten heute entweder separat auf oder unterwirft sich einer ausländischen Plattform.

Der Swiss AI Hub macht diese Infrastruktur zu einer Ware. Deployen Sie die Plattform einmal, und diese Probleme sind gelöst. Jede Verbesserung der Kernplattform kommt jeder Organisation zugute, die sie nutzt. Wenn jemand eine bessere Dokumentenanalyse beisteuert, verbessert sich die Dokumentenverarbeitung aller. Wenn jemand eine neue Sicherheitsfunktion hinzufügt, werden alle sicherer.

## Die Beitragsdynamik

Die Swiss AI Hub Plattform-Runtime, das SDK, die Agents, Pipelines und Prozesse sind unter Apache 2.0 lizenziert. (Die Web-Benutzeroberfläche und die Backup-Orchestrierung sind AGPL-3.0; die Multi-Tenant-Management-Ebene ist proprietär. Eine detaillierte Aufschlüsselung pro Paket finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).) Die permissive Lizenz für Runtime + SDK schafft natürliche Anreize zur Zusammenarbeit, ohne diese zu erzwingen.

- **Gemeinsame Infrastruktur nützt allen:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das Teilen sinnvoll, weil alle davon profitieren. Eine Bank, die eine bessere Compliance-Protokollierung hinzufügt, hilft jeder regulierten Branche. Ein Gesundheitsdienstleister, der den Umgang mit PII (persönlich identifizierbaren Informationen) verbessert, hilft allen mit Datenschutzbedenken. Diese Beiträge fliessen auf natürliche Weise zurück, da eine bessere gemeinsame Infrastruktur die Kosten für alle senkt.
- **Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung und Ihre Domänenexpertise verkörpert – diese bleiben Ihnen. Die Apache 2.0 Runtime erfordert kein Zurückteilen, sodass Sie strategische Innovationen privat halten können, während Sie von der gemeinsamen Infrastruktur profitieren und dazu beitragen.

## Warum Lizenzierung für KI-Infrastruktur wichtig ist

Das Verständnis von Softwarelizenzierung ist beim Aufbau von KI-Infrastruktur entscheidend. Viele Organisationen machen kostspielige Fehler, indem sie annehmen, dass Code auf GitHub automatisch frei zu verwenden ist – das ist er nicht.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ frei zu verwenden.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre Software mit restriktiven Lizenzen. Die Möglichkeit, Code zu *anzeigen* oder *herunterzuladen*, bedeutet nicht, dass Sie rechtlich dazu berechtigt sind, ihn zu *nutzen*, insbesondere in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use License" (keine Open-Source-Lizenz). Obwohl Sie es herunterladen und ausführen können, verbietet die Lizenz die kommerzielle Nutzung ohne den Erwerb einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Lizenzkategorien erklärt

- **Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren weitreichende Freiheiten – Nutzung, Modifikation, kommerzielle Verbreitung, Geheimhaltung von Modifikationen. Keine Bedingungen. Diese sind ideal für den Aufbau von Geschäftsinfrastruktur.
- **Copyleft-Lizenzen** (GPL, AGPL): Verlangen, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung als Open Source freigeben. **AGPL erweitert dies auf die Netzwerknutzung** – selbst das Anbieten der Software als Service löst die Anforderung aus. Dies macht Copyleft zu einer schlechten Wahl für die Bausteine, die Sie mit proprietärer Logik erweitern – genau aus diesem Grund sind die Swiss AI Hub Runtime und das SDK permissiv, nicht Copyleft. (Copyleft ist die richtige Wahl für Endbenutzeranwendungen wie die Benutzeroberfläche; siehe unten.)
- **Source-available Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use"): Ermöglichen das Anzeigen und manchmal auch die Nutzung des Codes, erlegen aber strenge Beschränkungen auf – oft das Verbot der kommerziellen Nutzung, von Managed Services oder konkurrierenden Produkten. Trotz des Erscheinens auf GitHub keine Open-Source-Lizenzen.
- **Proprietäre/kundenspezifische Lizenzen**: Variieren stark. Erfordern eine sorgfältige rechtliche Prüfung. Verbieten oft die Nutzung in der Produktion ohne Bezahlung.

### Zu vermeidende Lizenzen in der KI-Infrastruktur

Für KI-Produktionssysteme sollten Sie äusserst vorsichtig sein mit:

- **AGPL/GPL**: Zwingen Sie Ihr gesamtes System zur Open-Source-Freigabe, wenn Sie die Software modifizieren und vertreiben.
- **SSPL (Server Side Public License)**: Der Versuch von MongoDB, Cloud-Anbieter daran zu hindern, verwaltete Versionen anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus.
- **Elastic License v2**: Verbietet das Anbieten der Software als konkurrierenden Service.
- **Business Source License (BSL)**: Zeitverzögertes Open Source; restriktiv bis zum Ablaufdatum.
- **Kundenspezifische „Source-available"-Lizenzen**: Verbieten in der Regel die kommerzielle Nutzung oder haben unklare Bedingungen.

Diese Lizenzen mögen zunächst akzeptabel erscheinen, schaffen aber rechtliche Stolpersteine, wenn Sie skalieren, Services anbieten oder mit Kundensystemen integrieren – **wenn sie unter dem Code liegen, auf dem Sie aufbauen**. Genau deshalb hält der Swiss AI Hub die Runtime und das SDK permissiv. Die Web-Benutzeroberfläche und die Backup-Orchestrierung sind eine bewusste Ausnahme: Sie sind AGPL-3.0, *weil* sie Endbenutzeranwendungen und keine Bausteine sind, sodass Copyleft Community-Verbesserungen schützt, ohne jemals Ihre Agents oder Geschäftslogik zur Offenlegung zu zwingen.

### Unser Lizenzierungsengagement

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externen Docker-Images. Wir überprüfen, dass jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit geprüft und genehmigt wurde.

**Sie erhalten die Freiheiten, die die Lizenz jedes Pakets gewährt – die genauen Bedingungen pro Paket finden Sie unter [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).** Kurz gesagt: Die Runtime + SDK (Apache 2.0) unterliegen keinen Beschränkungen für die kommerzielle Nutzung oder die Integration mit proprietären Systemen; die Web-Benutzeroberfläche und die Backup-Orchestrierung (AGPL-3.0) erfordern die Offenlegung des Quellcodes Ihrer Modifikationen, wenn Sie diese als Netzwerkdienst anbieten; die Multi-Tenant-Administrations-Ebene ist proprietär und erfordert eine kommerzielle Lizenz.

**Warum Apache 2.0 speziell für die Runtime und das SDK:** Apache 2.0 ist nicht nur permissiv, sondern beinhaltet auch explizite Patentgewährungen, die Sie vor Patentansprüchen von Mitwirkenden schützen. Es wird von Unternehmen geschätzt, von Rechtsteams gut verstanden und ist mit praktisch allen anderen Lizenzen kompatibel. Es ist der Goldstandard für kollaborative Infrastruktur – genau die Rolle der Runtime und des SDK.

Dies ist nicht nur Idealismus – es ist Pragmatismus. Eine permissive Runtime + SDK beseitigt Adoptionshürden und verhindert Vendor Lock-in für die Bausteine, die Sie erweitern; die AGPL-Komponenten schützen vor feindlichen SaaS-Rehosts der Benutzeroberfläche, ohne die Bausteine zu belasten; die proprietäre Ebene finanziert die weitere Entwicklung.

## Echte Kollaborationsmuster

Das Ökosystem zeigt bereits, wie dies funktioniert:

- **Gemeinsame Komponenten:** Allgemeine Agents für Dokumentenzusammenfassungen, Beantwortung von Fragen und Datenextraktion werden zu Community-Assets. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.
- **Branchenlösungen:** Gesundheitsorganisationen arbeiten bei der medizinischen Dokumentenverarbeitung zusammen. Finanzdienstleister teilen auf Compliance fokussierte Agents. Diese branchenspezifischen Lösungen entstehen auf natürliche Weise, wenn Organisationen erkennen, dass ihre Konkurrenten im Ausland, nicht im Inland, die eigentliche Bedrohung sind.
- **Infrastrukturverbesserungen:** Leistungsoptimierungen, Sicherheitsverbesserungen und operationelle Tools fliessen in die Plattform zurück. Alle profitieren von einer schnelleren, sichereren und zuverlässigeren Grundlage.
- **Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Die gleiche Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystem-Modell eliminiert den Wettbewerb nicht; es konzentriert ihn dort, wo er wichtig ist:

- **Ihre Domänenexpertise** bleibt Ihre. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre Markteinblicke nicht. Diese schaffen Wettbewerbsvorteile.
- **Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie möglicherweise generische Dokumentenverarbeitung teilen, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.
- **Ihre Daten und Trainings** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten, aber die Daten selbst und die daraus gewonnenen Erkenntnisse sind Ihr Wettbewerbsvorteil.
- **Ihre Geschäftsinnovation** ist der Bereich, in dem Wettbewerb stattfinden sollte. Anstatt darum zu konkurrieren, wer bessere Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Wenn mehr Organisationen den Swiss AI Hub einführen, stärkt sich das Ökosystem:

- **Die Entwicklung beschleunigt sich**, weil gemeinsame Muster entstehen und in das SDK kodiert werden. Was Wochen zum Aufbau brauchte, wird zu einer Konfigurationsoption.
- **Die Qualität verbessert sich** durch kollektives Debugging und Testen. Da viele Organisationen dieselbe Plattform betreiben, werden Randfälle schnell entdeckt und behoben.
- **Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation für die vollständige Entwicklung bezahlt, werden die Kosten im gesamten Ökosystem verteilt.
- **Die Innovation nimmt zu**, weil Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu implementieren, können sie neue Funktionen erkunden.

## Der Swiss AI Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

- **Geschwindigkeit:** Neue Organisationen können Produktions-KI in Tagen, nicht in Monaten, deployen, indem sie bestehende Arbeit nutzen.
- **Souveränität:** Schweizer Daten bleiben in der Schweiz, werden von schweizerisch kontrollierter Infrastruktur verarbeitet und unterliegen schweizerischem Recht.
- **Unabhängigkeit:** Kein einzelner Anbieter kontrolliert die Plattform. Kein ausländisches Unternehmen kann Bedingungen ändern oder den Zugang sperren.
- **Qualität:** Kollektive Investitionen führen zu einer besseren Infrastruktur, als jede einzelne Organisation aufbauen könnte.
- **Innovation:** Befreit von Infrastrukturfragen konzentrieren sich Organisationen auf Geschäftsinnovationen, wo der wahre Wert liegt.

## Zusammenarbeit zum Erfolg führen

Das Ökosystem ist erfolgreich, weil es die Anreize korrekt ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen nicht-differenzierende Fähigkeiten, weil Zusammenarbeit wertvoller ist als Geheimhaltung. Sie halten strategische Innovationen privat, weil Apache 2.0 beide Ansätze zulässt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Zusammenarbeit, aber das Ökosystem wird von seinen Mitgliedern aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beisteuert oder Wissen teilt, stärkt die Schweizer KI-Fähigkeiten kollektiv.

So konkurriert die Schweiz global: nicht durch einzelne Organisationen, die versuchen, mit den Ressourcen der Big Tech gleichzuziehen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das zu konzentrieren, was sie einzigartig macht. Die Plattform ist die Warenschicht, die Innovation ermöglicht.
