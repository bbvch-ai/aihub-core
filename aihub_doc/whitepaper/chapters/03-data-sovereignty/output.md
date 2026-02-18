# Datensouveränität und vollständige Kundenkontrolle

Die Einführung von künstlicher Intelligenz in Schweizer Unternehmen und Behörden scheitert oft nicht an der technischen
Machbarkeit, sondern an der grundlegenden Frage der Datenhoheit. Wer kontrolliert die Informationen, wenn sie in
Vektoren umgewandelt werden? Wo werden die Prompts verarbeitet? Und wie wird verhindert, dass strategisches Wissen in
den undurchsichtigen Trainingsdaten globaler KI-Modelle aufgeht? In einer Zeit, in der Daten als strategisches Kapital
gelten, ist die Souveränität über diese Ressourcen eine zwingende Voraussetzung für die digitale Handlungsfähigkeit.

Der Swiss AI Hub adressiert diese Risiken durch ein Architekturdesign, das konsequent auf dem Prinzip der strikten
Datensouveränität basiert. Dieses Kapitel legt dar, wie Organisationen die uneingeschränkte Hoheit über Speicherort,
Zugriffsrechte und Informationsflüsse wahren – unabhängig davon, ob die Plattform im eigenen Rechenzentrum, in einer
Private Cloud oder als verwaltete Instanz in der Schweiz betrieben wird.

## Auf einen Blick

- **Garantierte Datenresidenz:** Durch flexible Hosting-Modelle wie On-Premise oder Schweizer Private Cloud verbleiben
  sämtliche persistierten Daten physisch im Hoheitsgebiet der Schweiz.
- **Harte Isolation durch Multi-Instancing:** Die Architektur ermöglicht physisch getrennte Instanzen («Shared
  Nothing»), um Datenlecks zwischen verschiedenen Organisationseinheiten technisch auszuschliessen.
- **Strategische Modell-Agnostik:** Das integrierte LLM-Gateway entkoppelt die Anwendung von den Providern und
  verhindert so einen Vendor-Lock-in bei globalen Hyperscalern.
- **Schutz durch Invisibility:** Ein granulares, hierarchisches Berechtigungssystem blendet nicht autorisierte
  Funktionen und Agenten-Profile dynamisch aus, was die Angriffsfläche minimiert.
- **Compliance-Automatisierung:** Integrierte Mechanismen für PII-Maskierung und tiefe Observability erfüllen die
  strengen Anforderungen des revDSG und der DSGVO bereits im Standard.

## Physische Datenhoheit und flexible Infrastruktur

### Geschäftlicher Nutzen

Für regulierte Industrien, das Gesundheitswesen und die öffentliche Verwaltung ist der physische Standort der Daten eine
nicht verhandelbare Compliance-Vorgabe. Die Nutzung öffentlicher SaaS-Angebote scheidet oft aus, da die Datenhoheit
faktisch an den Anbieter abgetreten wird und die Datenflüsse ins Ausland kaum kontrollierbar sind. Organisationen
benötigen die Gewissheit, dass sensible Unternehmensdaten den definierten Rechtsraum niemals verlassen. Gleichzeitig
darf diese Sicherheit nicht zu Lasten der Agilität gehen; die IT benötigt eine Lösung, die sich nahtlos in bestehende
Umgebungen integriert, sei es in einem Hochsicherheits-Rechenzentrum oder einer verwalteten Schweizer Cloud.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt den Ansatz «Bring Your Own Infrastructure». Die Plattform wird als containerisierte
Software-Lösung bereitgestellt, die vollständig innerhalb der kontrollierten Umgebung des Mandanten operiert. Dabei wird
strikt zwischen Multi-Tenancy (logische Trennung innerhalb einer Instanz) und Multi-Instancing (physische Trennung)
unterschieden.

Für Szenarien mit extrem hohen Sicherheitsanforderungen, wie etwa der Trennung zwischen einem Versicherungsbetrieb und
dessen medizinischem Dienst, kommt das Multi-Instancing zum Tragen. Hierbei erhält jede Einheit eine eigene, autarke
Infrastruktur mit dedizierten Datenbanken und Diensten. Ein Datenabfluss ist somit nicht nur durch Software-Logik,
sondern durch physische Trennung unterbunden. Ergänzend ermöglicht das Modell des Air-Gapped-Betriebs eine Installation
ohne jegliche Internetverbindung, wobei lokale Modelle die externe Kommunikation vollständig ersetzen.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet ein Set von Docker-Containern, die eine klare Segmentierung durch eine «Docker Network
Isolation» in fünf Zonen (Proxy, Backend, Data, Storage, Egress) erzwingen. Dies verhindert, dass ein kompromittierter
Dienst direkten Zugriff auf die Datenbanken erhält. Die Datenhaltung ist lokalisiert: Relationale Unternehmensdaten
liegen in PostgreSQL, Vektoreinbettungen für die semantische Suche in Milvus und Dokumente in S3-kompatiblen Speichern
wie SeaweedFS.

Sogar bei der Nutzung von Cloud-Modellen bleibt die Souveränität gewahrt, da das LLM-Gateway (LiteLLM) zustandslos
arbeitet und keine Prompts oder Antworten persistiert. Für den vollständig autonomen Betrieb können lokale
Inferenz-Server wie vLLM oder llama.cpp eingebunden werden, die Open-Source-Modelle direkt auf eigener Hardware
ausführen.

## Granulare Zugriffskontrolle und dynamische Sichtbarkeit

### Geschäftlicher Nutzen

Datensouveränität bedeutet auch die Kontrolle über interne Informationsflüsse. Ein häufiges Hindernis für den breiten
KI-Einsatz ist die Sorge, dass sensible Dokumente durch eine KI-Suche für unberechtigte Mitarbeitende sichtbar werden.
C-Level-Verantwortliche benötigen die Garantie, dass das Prinzip der minimalen Rechtevergabe (Least Privilege)
konsequent durchgesetzt wird. Es muss sichergestellt werden, dass ein Benutzer nur jene Agenten-Profile und
Wissensdatenbanken nutzen kann, die für seine spezifische Rolle freigegeben sind, um interne Datenmissbräuche
systematisch zu verhindern.

### Konzeptioneller Ansatz

Der Swiss AI Hub implementiert das Modell «Security by Invisibility». Anstatt Benutzern den Zugriff auf nicht
autorisierte Funktionen durch Fehlermeldungen zu verweigern, passt sich die Benutzeroberfläche dynamisch an die
Berechtigungen an. Dienste, Sammlungen oder Agenten-Profile, für die keine Zugriffsrechte bestehen, sind in der
Oberfläche schlichtweg nicht vorhanden.

Dieser Zero-Trust-Ansatz stellt sicher, dass die KI-Agenten unabhängig von den Benutzerberechtigungen agieren. Ein Agent
erbt nicht die Rechte des Benutzers, sondern greift auf Daten basierend auf seiner eigenen, administrativ festgelegten
Konfiguration zu. Die Kontrolle erfolgt somit auf der Ebene der Agenten-Interaktion: Wer darf mit welchem Agenten
sprechen? Dies vereinfacht die Governance drastisch, da nicht Millionen von Dokumentenberechtigungen mit der KI
synchronisiert werden müssen.

### Technische Umsetzung im Swiss AI Hub

Das Berechtigungssystem basiert auf einer hierarchischen Punkt-Notation im Format
`aihub.[user|admin].<service>.<resource>.<id>`. Ein zentraler «Access Checker» im Backend validiert jede Anfrage gegen
die Rollen des Benutzers und die Grenzen des Mandanten.

Durch die Unterstützung von Wildcards wie `*` (einzelne Ebene) oder `>` (rekursiv) können komplexe
Organisationsstrukturen effizient abgebildet werden. Die Authentifizierung erfolgt über standardisierte Protokolle wie
OIDC oder OAuth2, was die nahtlose Integration bestehender Identitätssysteme wie Azure AD oder Keycloak ermöglicht. Da
die Berechtigungsprüfung im Backend stattfindet, sind Manipulationen an der Benutzeroberfläche wirkungslos; der Benutzer
erhält lediglich einen gefilterten Dienstkatalog, der exakt seinem Autorisierungslevel entspricht.

## Modell-Agnostik und proaktiver Datenschutz

### Geschäftlicher Nutzen

Die Abhängigkeit von einem einzelnen KI-Anbieter stellt ein erhebliches strategisches Risiko dar. Preisänderungen oder
geopolitische Verschiebungen können die Verfügbarkeit kritischer Funktionen gefährden. Zudem ist das unmaskierte Senden
von personenbezogenen Informationen (PII) an externe APIs oft ein direkter Verstoss gegen das revDSG. Unternehmen
benötigen eine Architektur, die als Schutzschild fungiert: Sie muss Modell-Provider austauschbar machen und
sicherstellen, dass sensible Daten anonymisiert werden, bevor sie das kontrollierte Netzwerk verlassen.

### Konzeptioneller Ansatz

Der Swiss AI Hub fungiert als intelligenter Mediator zwischen den Geschäftsanwendungen und den KI-Modellen. Durch die
Abstraktion aller Modell-APIs hinter einer einheitlichen, OpenAI-kompatiblen Schnittstelle bleibt die Organisation
technologisch agil. Ein Wechsel des Anbieters erfordert keine Änderung am Anwendungscode, sondern lediglich eine
Anpassung im zentralen LLM-Gateway.

Zum Schutz der Privatsphäre wird das Konzept der «Anonymisierung an der Quelle» angewandt. Bevor eine Anfrage an einen
externen Provider delegiert wird, scannt das System den Inhalt auf sensible Muster. Diese werden entweder maskiert oder
die Anfrage wird bei hochsensiblen Datenkategorien komplett blockiert. Dies ermöglicht die Nutzung leistungsfähiger
Cloud-Modelle, ohne die Compliance-Richtlinien zu verletzen.

### Technische Umsetzung im Swiss AI Hub

Das LLM-Gateway nutzt LiteLLM für das intelligente Routing und die Kostenkontrolle. Integrierte «Guards» ermöglichen
eine Echtzeit-Validierung von Ein- und Ausgaben. Der PII-Schutz wird durch die Integration von Presidio realisiert,
wobei Administratoren zwischen einem Maskierungsmodus (Ersetzung durch Platzhalter wie `[PERSON]`) und einem
Blockierungsmodus (Abweisung der Anfrage) wählen können.

Zusätzlich bietet die Plattform Schutzmechanismen auf Agenten-Ebene, die Antworten filtern, falls diese sensible
Informationen aus internen Wissensdatenbanken enthalten könnten. Diese mehrstufige Verteidigung («Defense-in-Depth»)
stellt sicher, dass sowohl Benutzereingaben als auch KI-generierte Antworten stets den Sicherheitsvorgaben entsprechen.

## Langzeit-Verfügbarkeit und Deep Observability

### Geschäftlicher Nutzen

Investitionen in KI-Infrastrukturen müssen langfristig gesichert und revisionssicher sein. Entscheidungsträger müssen
jederzeit nachweisen können, warum eine KI eine bestimmte Entscheidung getroffen hat, ohne dabei die Hoheit über die
Log-Daten an externe Monitoring-Anbieter abzugeben. In regulierten Branchen ist diese Erklärbarkeit keine Option,
sondern eine gesetzliche Pflicht. Ein System, das auf offenen Standards basiert, bietet hier die Gewissheit, dass das
Unternehmenswissen nicht in proprietären Datensilos gefangen ist und Audits jederzeit erfolgreich bestanden werden
können.

### Konzeptioneller Ansatz

Die Transparenz der Plattform basiert auf dem Einsatz von OpenTelemetry (OTel), dem Industriestandard für Observability.
Dies garantiert, dass sämtliche Telemetriedaten – also Metriken, Logs und Traces – vollständig im Besitz des Kunden
bleiben. Die Architektur ermöglicht eine «Deep Observability», bei der jeder Schritt eines Agenten-Workflows, jeder
Datenbankzugriff und jeder Modellaufruf präzise dokumentiert wird. Compliance wird so von einer manuellen Prüfaufgabe zu
einer automatisierten Systemeigenschaft, die auch Anforderungen wie das «Recht auf Vergessenwerden» durch definierte
Löschzyklen unterstützt.

### Technische Umsetzung im Swiss AI Hub

Die Plattform implementiert Distributed Tracing über alle Komponenten hinweg. Dabei werden «OpenInference Semantic
Conventions» genutzt, um KI-spezifische Details wie Token-Verbrauch und abgerufene Dokumente sichtbar zu machen. Der
OpenTelemetry Collector ermöglicht duale Datenströme: Während eine Pipeline detaillierte Traces für die Analyse an die
lokale Phoenix-Instanz liefert, sendet eine zweite Pipeline gefilterte operative Daten an Langzeitspeicher oder
bestehende Enterprise-Monitoring-Tools wie SigNoz oder Dynatrace.

Da alle Daten, einschliesslich der Vektoreinbettungen und Konfigurationen, in offenen Formaten (z. B. PostgreSQL/Milvus)
gespeichert werden, ist ein Export oder Systemwechsel jederzeit ohne proprietäre Werkzeuge möglich. Dies eliminiert das
Risiko eines Vendor-Lock-ins und sichert die strategische Handlungsfähigkeit der Organisation über den gesamten
Lebenszyklus der Plattform hinweg.
