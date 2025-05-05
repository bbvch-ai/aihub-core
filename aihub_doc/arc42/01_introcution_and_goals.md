# Einführung und Ziele
<!--

> **How to arc42:** 💡
>
>Beschreibt die wesentlichen Anforderungen und treibenden Kräfte, die bei
>der Umsetzung der Softwarearchitektur und Entwicklung des Systems
>berücksichtigt werden müssen.
>
>Dazu gehören:
>
>-   zugrunde liegende Geschäftsziele,
>
>-   wesentliche Aufgabenstellungen,
>
>-   wesentliche funktionale Anforderungen,
>
>-   Qualitätsziele für die Architektur und
>
>-   relevante Stakeholder und deren Erwartungshaltung.*

-->

Dieser Abschnitt beschreibt die Aufgabenstellung des bbv AI Hubs und die Ziele die mit dem bbv AI Hub verfolgt werden.

## Aufgabenstellung

<!--

> **How to arc42: 💡**
>
>**Inhalt**
> 
> Kurzbeschreibung der fachlichen Aufgabenstellung, treibenden Kräfte,
>Extrakt (oder Abstract) der Anforderungen. Verweis auf (hoffentlich
>vorliegende) Anforderungsdokumente (mit Versionsbezeichnungen und
>Ablageorten).
>
>**Motivation**
>
> Aus Sicht der späteren Nutzung ist die Unterstützung einer fachlichen
>Aufgabe oder Verbesserung der Qualität der eigentliche Beweggrund, ein
>neues System zu schaffen oder ein bestehendes zu modifizieren.
>
>**Form**
>
> Kurze textuelle Beschreibung, eventuell in tabellarischer Use-Case Form.
>Sofern vorhanden, sollte die Aufgabenstellung Verweise auf die
>entsprechenden Anforderungsdokumente enthalten.
>
>Halten Sie diese Auszüge so knapp wie möglich und wägen Sie Lesbarkeit
>und Redundanzfreiheit gegeneinander ab.
>
>Siehe [Anforderungen und Ziele](https://docs.arc42.org/section-1/) in
>der online-Dokumentation (auf Englisch!).

-->

### Kurzbeschreibung

Die Anwendung "bbv AI-Hub" wird entwickelt, um die Einführung und Implementierung von Generativer Künstlicher Intelligenz (KI) 
in Unternehmen zu vereinfachen und effizienter zu gestalten. Sie bietet ein schnelles und kostengünstiges Setup, 
das es Unternehmen jeder Grösse ermöglicht, die Vorteile der KI zu nutzen. Der Fokus liegt auf der Bereitstellung 
spezialisierter KI-Agenten, die als virtuelle Mitarbeiter mit klaren "Jobbeschreibungen" spezifische Aufgaben übernehmen. 
Der "bbv AI-Hub" ermöglicht zudem die Kollaboration zwischen verschiedenen Agenten und menschlichen Mitarbeitern, 
um Schwarmintelligenz zu erzeugen und die Benutzererfahrung zu verbessern.

### Treibende Kräfte

Der AI-Hub adressiert die Notwendigkeit, KI-gestützte Unterstützung gezielt und kontrolliert einzusetzen, 
um die Effizienz und Konsistenz innerhalb von Unternehmen zu steigern. Durch die Bereitstellung von KI-Agenten 
mit umfangreichem Kontextwissen wird der Aufwand für Benutzer minimiert. Zudem fördert der AI-Hub die Nutzung von 
firmeninternem Wissen und dessen Erweiterung, sowohl intern als auch extern.

### Anforderungen

- **LLM-agnostisch**: Integration und Zusammenarbeit mit mehreren Large Language Models (LLMs) wie Azure Open AI, Open AI Chat GPT, Gemini und LLama.
- **tiefgehende Fähigkeiten**: Bereitstellung spezialisierter Fähigkeiten durch KI-Agenten, wie Retrieval-Augmented-Generation (RAG), Internet-Recherche, Sprachverarbeitung und mehr.
- **Zugriffskontrolle**: Sicherstellung der Datenkontrolle und -sicherheit durch rollenbasierte Zugriffskontrollen (RBAC) und verschlüsselte Kommunikationskanäle (TLS).
- **Anpassungsfähigkeit**: Anpassungsfähigkeit an spezifische Kundenanforderungen durch ein modulares und flexibles Systemdesign.

### Motivation

Die Motivation hinter dem bbv AI-Hub ist eine tiefe Eintritts-Hürde für Unternehmen zu schaffen um KI effizient ein zusetzten.
Für die bbv soll der bbv AI Hub auch eine Plattform sein um schnell und kostengünstig mit Kunden Prototypen zu entwickeln 
und als Grundlage dienen für custom Entwicklungen. Der bbv AI-Hub soll also Basis für eine längere Zusammenarbeit sein und
dient auch als Marketing-Instrument während der aktuell KI-Hype-Phase.



## Qualitätsziele

<!--

> **How to arc42:** 💡
>
>**Inhalt**
>
>Die Top-3 bis Top-5 der Qualitätsanforderungen für die Architektur,
>deren Erfüllung oder Einhaltung den massgeblichen Stakeholdern besonders
>wichtig sind. Gemeint sind hier wirklich Qualitätsziele, die nicht
>unbedingt mit den Zielen des Projekts übereinstimmen. Beachten Sie den
>Unterschied.
>
>Hier ein Überblick möglicher Themen (basierend auf dem ISO 25010
>Standard):
>
>![Kategorien von
>Qualitätsanforderungen](images/01_2_iso-25010-topics-DE.drawio.png)
>
>**Motivation**
>
>Weil Qualitätsziele grundlegende Architekturentscheidungen oft
>massgeblich beeinflussen, sollten Sie die für Ihre Stakeholder relevanten
>Qualitätsziele kennen, möglichst konkret und operationalisierbar.
>
>**Form**
>
>Tabellarische Darstellung der Qualitätsziele mit möglichst konkreten
>Szenarien, geordnet nach Prioritäten.

-->

1. **Helpfulness** - Der "bbv AI Hub" und die darauf entwickelte Agenten sollen hilfreich sein. Schlussendlich soll es für die Nutzer einfacher sein ihre Aufgabe mit einem KI-Agenten als ohne zu bearbeiten.
2. **Installability** - Der "bbv AI Hub" soll auf azure Infrastrucktur des Kunden einfach installiert werden. Der Kunden Aufwand soll minimiert sein und so einfach wie Möglich
3. **Compliance** - Der "bbv AI Hub" soll die Datenschutz bestimmungen erfüllen und somit sollten nur die absolut notwendigen Daten gespeichert werden und das Backend sollte möglichst "stateless" sein
4. ... tbd

## Stakeholder

<!--

> **How to arc42:** 💡
> 
>**Inhalt**
>
>Expliziter Überblick über die Stakeholder des Systems – über alle
>Personen, Rollen oder Organisationen –, die
>
>-   die Architektur kennen sollten oder
>
>-   von der Architektur überzeugt werden müssen,
>
>-   mit der Architektur oder dem Code arbeiten (z.B. Schnittstellen
>    nutzen),
>
>-   die Dokumentation der Architektur für ihre eigene Arbeit benötigen,
>
>-   Entscheidungen über das System und dessen Entwicklung treffen.
>
>**Motivation**
>
>Sie sollten die Projektbeteiligten und -betroffenen kennen, sonst
>erleben Sie später im Entwicklungsprozess Überraschungen. Diese
>Stakeholder bestimmen unter anderem Umfang und Detaillierungsgrad der
>von Ihnen zu leistenden Arbeit und Ergebnisse.
>
>**Form**
>
>Tabelle mit Rollen- oder Personennamen, sowie deren Erwartungshaltung
>bezüglich der Architektur und deren Dokumentation.
>
>| Rolle           | Kontakt         | Erwartungshaltung                 |
>|-----------------|-----------------|-----------------------------------|
>| *\<Rolle-1>*    | *\<Kontakt-1>*  | *\<Erwartung-1>*                  |
>| *\<Rolle-2>*    | *\<Kontakt-2>*  | *\<Erwartung-2>*                  |

-->

| Rolle                                 | Kontakt | Erwartungshaltung                                                                                                                                                                                           |
|---------------------------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *IT Verantwortlicher des Kunden*      |         | <ul><li>möchte wissen welche Infrastrucktur Komponenten benötigt werden </li><li> möchte wissen wie Bechechtigungs und Authentifizierungsmethoden funktionieren</li></ul>                                   |
| *Datenschutz Beauftragter des Kunden* |         | <ul><li>möchte die Berechtigungsstrucktur kennen </li><li> möchte wissen wie die Daten fliessen und wo diese gespeichert werden </li></ul>                                                                  |
| bbv Sales                             |         | <ul><li>möchte die gelisteten Kunden Rollen beraten können </li><li> möchte den Feature Umfang kennen </li><li> möchte den Installationsaufwand und Entwicklungsaufwand von erweiterungen kennen </li></ul> |
| ... (more to come)                    | ...     | ...                                                                                                                                                                                                         |