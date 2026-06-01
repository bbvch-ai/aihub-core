---
title: Das Ökosystem-Modell
source_sha: 300357d666a98e3b374d6673af4cb775a7fcfcf3ed305b37a600e22339782894
---

# Das Ökosystem-Modell: Wie alle profitieren

Der Swiss AI Hub existiert, weil KI-Infrastruktur kein Wettbewerbsvorteil sein sollte. Grundlegende Funktionen wie
LLM-Zugang, Dokumentenverarbeitung und RAG sollten Standardgüter sein, die jedem zur Verfügung stehen. Schweizer
Organisationen sollten sich auf ihr Fachwissen und ihre Geschäftsinnovationen konzentrieren, nicht darauf, wer bessere
Authentifizierungssysteme oder Vektordatenbanken bauen kann.

## Die Schweizer Chance

Die Schweiz ist ein kleines Land, das in einer globalen Wirtschaft konkurriert, die von Technologiegiganten dominiert
wird. Während Google, Microsoft und Amazon Milliarden in die KI-Infrastruktur investieren, fehlt es Schweizer
Unternehmen individuell an den Ressourcen, um diese Investitionen zu erreichen. Die typische Reaktion wäre, die
Abhängigkeit von ausländischen Plattformen zu akzeptieren, aber die Schweiz hat eine andere Option: Zusammenarbeit.

Dieselben demokratischen Prinzipien, die die Schweiz als Nation erfolgreich machen, können unseren Umgang mit KI
transformieren. Anstatt dass jede Organisation redundante Infrastruktur aufbaut, können wir unsere Anstrengungen auf die
Grundlagen bündeln und gleichzeitig auf der Anwendungsschicht konkurrieren. Hier geht es nicht darum, den Wettbewerb zu
eliminieren; es geht darum, den Wettbewerb dorthin zu verlagern, wo er Wert schafft.

## Infrastruktur als Standardgut

Betrachten Sie, was jede Organisation, die KI aufbaut, benötigt:

- Sicheren Modellzugriff mit Kostenkontrolle
- Dokumentenverarbeitung und Vektorspeicher
- Authentifizierung und Benutzerverwaltung
- Monitoring und Observability
- Deployment- und Skalierungsmuster

Diese Anforderungen sind universell. Die Authentifizierungsbedürfnisse einer Bank unterscheiden sich nicht grundlegend
von denen einer Versicherungsgesellschaft. Die Herausforderungen eines Pharmaunternehmens bei der Dokumentenverarbeitung
spiegeln die einer Produktionsfirma wider. Doch heute baut jede Organisation diese Fähigkeiten entweder separat auf oder
unterwirft sich einer ausländischen Plattform.

Der Swiss AI Hub macht diese Infrastruktur zu einem Standardgut. Deployen Sie die Plattform einmal, und diese Probleme
sind gelöst. Jede Verbesserung der Kernplattform nützt jeder Organisation, die sie nutzt. Wenn jemand ein besseres
Dokumenten-Parsing beisteuert, verbessert sich die Dokumentenverarbeitung aller. Wenn jemand eine neue
Sicherheitsfunktion hinzufügt, werden alle sicherer.

## Die Dynamik der Beiträge

Die Swiss AI Hub Plattform-Runtime, das SDK, die Agents, Pipelines und Prozesse sind unter Apache 2.0 lizenziert. (Die
Web-UI und Backup-Orchestrierung sind AGPL-3.0; die Multi-Tenant-Management-Plane ist proprietär. Eine detaillierte
Aufschlüsselung pro Paket finden Sie in [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).)
Die permissive Lizenz für Runtime + SDK schafft natürliche Anreize zur Zusammenarbeit, ohne diese zu erzwingen.

**Gemeinsam genutzte Infrastruktur nützt allen:** Wenn Organisationen die Kerninfrastruktur verbessern, ist das Teilen
sinnvoll, weil alle davon profitieren. Eine Bank, die ein besseres Compliance-Logging hinzufügt, hilft jeder regulierten
Branche. Ein Gesundheitsdienstleister, der den Umgang mit PII verbessert, hilft allen mit Datenschutzbedenken. Diese
Beiträge fliessen natürlich zurück, weil eine bessere gemeinsam genutzte Infrastruktur die Kosten für alle senkt.

**Strategische Differenzierung bleibt privat:** Organisationen behalten ihre Wettbewerbsvorteile proprietär. Der
kundenorientierte Agent, der Ihre einzigartigen Geschäftsprozesse, Ihre spezialisierte Datenverarbeitung, Ihr Fachwissen
verkörpert – diese bleiben Ihnen vorbehalten. Die Apache 2.0 Runtime erfordert kein Zurückteilen von Änderungen, sodass
Sie strategische Innovationen privat halten können, während Sie von der gemeinsam genutzten Infrastruktur profitieren
und dazu beitragen.

## Warum Lizenzen für KI-Infrastruktur wichtig sind

Das Verständnis von Softwarelizenzen ist entscheidend beim Aufbau von KI-Infrastruktur. Viele Organisationen machen
kostspielige Fehler, indem sie davon ausgehen, dass Code auf GitHub automatisch kostenlos nutzbar ist – das ist er
nicht.

### Das GitHub-Missverständnis

**Quellcode sehen ≠ Open Source ≠ kostenlos nutzbar.** GitHub hostet sowohl Open-Source-Projekte als auch proprietäre
Software mit restriktiven Lizenzen. Die Möglichkeit, Code *anzusehen* oder *herunterzuladen*, bedeutet nicht, dass Sie
rechtlich berechtigt sind, ihn zu *nutzen*, insbesondere nicht in Produktions- oder kommerziellen Kontexten.

Beispiel: **n8n**, eines der beliebtesten Workflow-Automatisierungstools auf GitHub, verwendet die „Sustainable Use
License" (keine Open-Source-Lizenz). Obwohl Sie es herunterladen und ausführen können, verbietet die Lizenz die
kommerzielle Nutzung ohne den Kauf einer Enterprise-Lizenz – selbst wenn Sie es selbst hosten. Viele Organisationen
entdecken dies zu spät, nachdem sie Abhängigkeiten von diesen Tools aufgebaut haben.

### Lizenzkategorien erklärt

**Permissive Lizenzen** (MIT, Apache 2.0, BSD): Gewähren weitreichende Freiheiten – verwenden, modifizieren, kommerziell
vertreiben, Änderungen privat halten. Keine Bedingungen geknüpft. Diese sind ideal für den Aufbau von
Geschäftsinfrastruktur.

**Copyleft-Lizenzen** (GPL, AGPL): Erfordern, dass alle Modifikationen oder abgeleiteten Werke unter derselben Lizenz
veröffentlicht werden. Wenn Sie auf GPL-Software aufbauen und diese vertreiben, müssen Sie Ihre gesamte Anwendung als
Open Source freigeben. **AGPL erweitert dies auf die Netzwerknutzung** – selbst das Anbieten der Software als Service
löst die Anforderung aus. Gefährlich für proprietäre KI-Produkte.

**Source-available Lizenzen** (Elastic License, BSL, SSPL, „Sustainable Use"): Ermöglichen Ihnen das Ansehen und
manchmal die Nutzung des Codes, erlegen aber strenge Beschränkungen auf – oft verbieten sie die kommerzielle Nutzung,
Managed Services oder konkurrierende Produkte. Trotz ihres Erscheinens auf GitHub sind sie keine Open-Source-Lizenzen.

**Proprietäre/Benutzerdefinierte Lizenzen**: Variieren stark. Erfordern eine sorgfältige rechtliche Prüfung. Verbieten
oft den Produktionseinsatz ohne Bezahlung.

### Lizenzen, die in der KI-Infrastruktur zu vermeiden sind

Für Produktions-KI-Systeme sollten Sie äusserst vorsichtig sein bei:

- **AGPL/GPL**: Zwingen Ihr gesamtes System zur Open-Source-Freigabe, wenn Sie die Software modifizieren und vertreiben
- **SSPL (Server Side Public License)**: Der Versuch von MongoDB, Cloud-Anbieter daran zu hindern, Managed-Versionen
  anzubieten; löst Open-Source-Anforderungen für die Infrastruktur aus
- **Elastic License v2**: Verbietet das Anbieten der Software als konkurrierenden Service
- **Business Source License (BSL)**: Zeitverzögerter Open Source; restriktiv bis zum Ablaufdatum
- **Benutzerdefinierte „Source-available"-Lizenzen**: Verbieten in der Regel die kommerzielle Nutzung oder haben unklare
  Bedingungen

Diese Lizenzen mögen anfänglich akzeptabel erscheinen, schaffen aber rechtliche Fallstricke, wenn Sie skalieren,
Services anbieten oder mit Kundensystemen integrieren.

### Unser Lizenzversprechen

Der Swiss AI Hub bewertet jede Abhängigkeit rigoros – alle 232 Python-Pakete, 197 Node.js-Pakete und 28 externen
Docker-Images. Wir verifizieren, dass jede Komponente permissive Lizenzen (MIT, Apache 2.0, BSD) verwendet oder explizit
geprüft und genehmigt wurde.

**Sie erhalten die Freiheiten, die die Lizenz jedes Pakets gewährt – die genauen Bedingungen pro Paket finden Sie in
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).** Kurz gesagt: Die Runtime + SDK (Apache
2.0) auferlegen keine Einschränkungen für die kommerzielle Nutzung oder Integration mit proprietären Systemen; die
Web-UI und Backup-Orchestrierung (AGPL-3.0) erfordern die Offenlegung des Quellcodes Ihrer Modifikationen, wenn Sie
diese als Netzwerkdienst anbieten; die Multi-Tenant-Administrations-Plane ist proprietär und erfordert eine kommerzielle
Lizenz.

**Warum Apache 2.0 speziell für die Runtime und das SDK:** Apache 2.0 ist nicht nur permissiv, sondern beinhaltet auch
explizite Patentlizenzen, die Sie vor Patentansprüchen von Mitwirkenden schützen. Es wird von Unternehmen geschätzt, von
Rechtsteams gut verstanden und ist mit praktisch allen anderen Lizenzen kompatibel. Es ist der Goldstandard für
kollaborative Infrastruktur – genau die Rolle der Runtime und des SDK.

Das ist nicht nur Idealismus – es ist Pragmatismus. Eine permissive Runtime + SDK beseitigt Adoptionsbarrieren und
verhindert Vendor Lock-in für die Bausteine, die Sie erweitern; die AGPL-Komponenten schützen vor feindseligen
SaaS-Rehosts der Benutzeroberfläche, ohne die Bausteine zu belasten; die proprietäre Ebene finanziert die
Weiterentwicklung.

## Reale Kollaborationsmuster

Das Ökosystem zeigt bereits, wie das funktioniert:

**Gemeinsame Komponenten:** Gängige Agents für Dokumentenzusammenfassung, Fragenbeantwortung und Datenextraktion werden
zu Gemeinschaftsgütern. Jede Organisation benötigt diese Grundlagen, daher ist das Teilen sinnvoll.

**Branchenlösungen:** Gesundheitsorganisationen arbeiten bei der Verarbeitung medizinischer Dokumente zusammen.
Finanzdienstleister teilen Compliance-orientierte Agents. Diese branchenspezifischen Lösungen entstehen natürlich, wenn
Organisationen erkennen, dass ihre Wettbewerber im Ausland, nicht im Inland, die eigentliche Bedrohung sind.

**Infrastrukturverbesserungen:** Performance-Optimierungen, Sicherheitsverbesserungen und operative Tools fliessen
zurück zur Plattform. Alle profitieren von einer schnelleren, sichereren, zuverlässigeren Grundlage.

**Wissensaustausch:** Organisationen teilen Deployment-Muster, Best Practices und gewonnene Erkenntnisse. Dieselbe
Plattform bedeutet, dass Lösungen übertragbar sind.

## Wo Wettbewerb hingehört

Das Ökosystem-Modell eliminiert den Wettbewerb nicht; es konzentriert ihn auf das Wesentliche:

**Ihr Fachwissen** bleibt bei Ihnen. Die Plattform kennt Ihre Geschäftsregeln, Ihre Kundenbeziehungen oder Ihre
Markterkenntnisse nicht. Diese schaffen Wettbewerbsvorteile.

**Ihre spezialisierten Agents** spiegeln Ihre einzigartigen Prozesse und Ihr Wissen wider. Während Sie möglicherweise
generische Dokumentenverarbeitung teilen, verkörpert Ihr Kundenservice-Agent Ihren spezifischen Ansatz.

**Ihre Daten und Trainings** bleiben proprietär. Die Plattform bietet Tools zur Verarbeitung und Abfrage Ihrer Daten,
aber die Daten selbst und die daraus abgeleiteten Erkenntnisse sind Ihr Wettbewerbsvorteil.

**Ihre Geschäftsinnovation** ist der Ort, wo Wettbewerb hingehört. Anstatt darum zu konkurrieren, wer bessere
Vektordatenbanken hat, konkurrieren Sie darum, wer KI kreativer einsetzt, um Kunden zu bedienen.

## Der Netzwerkeffekt

Wenn mehr Organisationen den Swiss AI Hub nutzen, stärkt sich das Ökosystem:

**Die Entwicklung beschleunigt sich**, weil gemeinsame Muster entstehen und in das SDK kodiert werden. Was Wochen zum
Bauen dauerte, wird zu einer Konfigurationsoption.

**Die Qualität verbessert sich** durch kollektives Debugging und Testen. Da viele Organisationen dieselbe Plattform
betreiben, werden Randfälle schnell entdeckt und behoben.

**Die Kosten sinken** durch gemeinsame Investitionen. Anstatt dass jede Organisation die vollständige Entwicklung
bezahlt, werden die Kosten im Ökosystem verteilt.

**Die Innovation nimmt zu**, weil Entwickler auf einer höheren Grundlage aufbauen können. Anstatt Grundlagen neu zu
implementieren, können sie neue Fähigkeiten erkunden.

## Der Swiss AI Vorteil

Dieser kollaborative Ansatz verschafft Schweizer Organisationen kollektive Vorteile:

**Geschwindigkeit:** Neue Organisationen können Produktions-KI in Tagen, nicht Monaten, deployen, indem sie bestehende
Arbeit nutzen.

**Souveränität:** Schweizer Daten bleiben in der Schweiz, werden von schweizerisch kontrollierter Infrastruktur
verarbeitet und unterliegen Schweizer Recht.

**Unabhängigkeit:** Kein einzelner Anbieter kontrolliert die Plattform. Kein ausländisches Unternehmen kann Bedingungen
ändern oder den Zugang sperren.

**Qualität:** Kollektive Investitionen produzieren bessere Infrastruktur, als jede einzelne Organisation bauen könnte.

**Innovation:** Befreit von Infrastruktur-Belangen, konzentrieren sich Organisationen auf Geschäftsinnovationen, wo der
wahre Wert liegt.

## Zusammenarbeit ermöglichen

Das Ökosystem ist erfolgreich, weil es die Anreize richtig ausrichtet:

Organisationen tragen zur Infrastruktur bei, weil sie direkt von Verbesserungen profitieren. Sie teilen
nicht-differenzierende Fähigkeiten, weil Zusammenarbeit wertvoller ist als Geheimhaltung. Sie halten strategische
Innovationen privat, weil Apache 2.0 beide Ansätze zulässt – die Wahl liegt immer bei Ihnen.

Der Swiss AI Hub bietet die technische Grundlage für diese Zusammenarbeit, aber das Ökosystem wird von seinen
Mitgliedern aufgebaut. Jede Organisation, die die Plattform deployt, Verbesserungen beisteuert oder Wissen teilt, stärkt
die Schweizer KI-Fähigkeiten kollektiv.

So ist die Schweiz global wettbewerbsfähig: nicht durch einzelne Organisationen, die versuchen, mit den Ressourcen von
Big Tech gleichzuziehen, sondern durch kollaborative Infrastruktur, die es jeder Organisation ermöglicht, sich auf das
zu konzentrieren, was sie einzigartig macht. Die Plattform ist die Standard-Schicht, die Innovation ermöglicht.
