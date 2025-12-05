# Datensouveränität und vollständige Kundenkontrolle

## Das Ende des Vertrauensdilemmas

In der klassischen Software-as-a-Service (SaaS) Welt basiert Datensicherheit primär auf einem abstrakten
Vertrauensvorschuss: Unternehmen müssen sich darauf verlassen, dass der Anbieter seine Sicherheitsversprechen einhält,
dass Daten nicht intransparent für Modelltrainings abgezweigt werden und dass der physische Speicherort der Daten
tatsächlich den vertraglichen Zusicherungen entspricht. Für stark regulierte Branchen in der Schweiz, wie das
Finanzwesen, das Gesundheitswesen oder die öffentliche Verwaltung, ist dieses Modell oft unzureichend, da vertragliche
Garantien technische Zugriffsmöglichkeiten des Anbieters nicht physisch unterbinden können.

Der Swiss AI Hub löst dieses Dilemma durch einen fundamentalen Architekturwechsel: Vertrauen wird durch technische
Kontrolle ersetzt. Da die Plattform nicht als gemieteter Dienst, sondern als Infrastruktur-Produkt im Besitz des Kunden
betrieben wird, entfällt die Abhängigkeit von externen Sicherheitsgarantien. Die Hoheit über Datenhaltung,
Zugriffsrechte und Informationsflüsse liegt ausschliesslich bei der auftraggebenden Organisation. Es gibt keine «Black
Box» und keinen administrativen Zugriff durch den Hersteller.

## Garantierte Datenresidenz durch flexible Architektur

### Vom Vertrag zur physischen Realität

Die Einhaltung von Data Residency – also der Anforderung, dass bestimmte Daten den Schweizer Rechtsraum nicht verlassen
dürfen – ist oft eine juristische Herausforderung, wenn internationale Cloud-Anbieter involviert sind. Selbst bei
vertraglichen Zusicherungen («Swiss Region») bleibt oft unklar, ob Metadaten, temporäre Caches oder Support-Zugriffe
wirklich lokal bleiben.

Der Swiss AI Hub begegnet dieser Unsicherheit durch seine flexible Deployment-Architektur. Das System ist vollständig
containerisiert und läuft auf Standard-x86_64-Servern. Dies ermöglicht den Betrieb in drei Szenarien, die je nach
Sensitivität der Daten gewählt werden können:

1. **On-Premise:** Die Software läuft auf den eigenen Servern im unternehmenseigenen Rechenzentrum. Persistenzschichten
   wie PostgreSQL (Datenbank) und Milvus (Vektor-Store) liegen vollständig unter eigener Kontrolle. Persistente Volumes
   werden mittels LUKS oder ähnlichen Standards verschlüsselt.
2. **Private Cloud:** Betrieb in einer dedizierten Umgebung bei einem Schweizer Cloud-Provider oder in einer eigenen
   Cloud-Instanz (Azure/AWS/GCP), wobei die Datenhoheit durch eigene Verschlüsselungsschlüssel (BYOK) gewahrt bleibt.
3. **Air-Gapped:** Für höchste Sicherheitsanforderungen, etwa bei Nachrichtendiensten oder sensibler Forschung, kann das
   System vollständig ohne Internetverbindung betrieben werden. Hierbei kommen lokal gehostete LLMs (wie Llama oder
   Mistral) zum Einsatz, die auf eigener GPU-Hardware laufen.

### Multi-Instancing für strikte Isolation

Um auch innerhalb grosser Organisationen höchste Sicherheitsstandards zu gewährleisten, unterstützt der Swiss AI Hub das
Konzept des **Multi-Instancings**. Im Gegensatz zur reinen Multi-Tenancy, die nur eine logische Trennung innerhalb einer
Software-Instanz bietet, ermöglicht Multi-Instancing eine harte Infrastruktur-Trennung.

Technisch bedeutet dies, dass sensible Bereiche – beispielsweise eine medizinische Prüfungskommission – eine eigene,
vollständig isolierte Instanz des AI Hubs erhalten. Diese Instanzen teilen sich keine Datenbanken, Vektor-Stores oder
Dateispeicher. Selbst bei einer Fehlkonfiguration auf Applikationsebene ist ein Datenabfluss zwischen den Instanzen
(«Leaking») technisch ausgeschlossen. Dennoch ermöglicht die Architektur Effizienzgewinne: Über einen zentralen
**LiteLLM-Proxy** können Backend-Ressourcen wie teure GPU-Cluster oder Cloud-Modell-Abonnements von mehreren isolierten
Instanzen gemeinsam genutzt werden, ohne dass diese Zugriff auf die Daten der jeweils anderen haben. Der Kontext und die
Historie verbleiben strikt in der jeweiligen Instanz.

## Strategische Unabhängigkeit von Modell-Anbietern

### Das Risiko des strategischen Lock-ins

Eine der grössten Gefahren bei der heutigen KI-Adoption ist die Abhängigkeit von proprietären Modellen einzelner
Anbieter (Vendor Lock-in). Wenn eine Organisation ihre gesamte Applikationslogik direkt gegen die API eines spezifischen
Anbieters entwickelt, wird sie verwundbar gegenüber Preissteigerungen, Änderungen der Nutzungsbedingungen oder der
Einstellung von Modellen.

Der Swiss AI Hub verfolgt hier eine Strategie der radikalen Entkopplung. Die «Intelligenz» (das LLM) wird als
austauschbare Commodity betrachtet. Die Applikationslogik, die Agenten und die gespeicherten Vektordaten bleiben
unabhängig vom verwendeten Modell.

### Der LLM-Proxy als Abstraktionsschicht

Technisch wird diese Unabhängigkeit durch den integrierten **LiteLLM-Proxy** realisiert. Diese Komponente fungiert als
zentrales Gateway und Abstraktionsschicht zwischen den internen Anwendungen und den externen oder internen
Sprachmodellen. Der Proxy vereinheitlicht die Schnittstellen: Egal ob im Hintergrund ein GPT-4o über Azure, ein
Gemini-Modell von Google oder ein lokal gehostetes Open-Source-Modell läuft, die internen Agenten sprechen immer
dieselbe standardisierte, OpenAI-kompatible Sprache.

Ein Modellwechsel erfordert keine Code-Änderungen an den Applikationen, sondern lediglich eine Anpassung in der
zentralen Konfigurationsdatei. Dies ermöglicht hybride Strategien, bei denen Standard-Anfragen kostengünstige Modelle
nutzen, während vertrauliche Daten automatisch an lokale, selbst gehostete Modelle (via vLLM oder llama.cpp) geroutet
werden. Da auch die Vektordatenbanken auf offenen Standards basieren, sind die erzeugten Wissensdatenbanken jederzeit
exportierbar, was die langfristige Investitionssicherheit garantiert.

## Kontrolle der Datenflüsse und Anonymisierung

### Schutz vor versehentlichem Datenabfluss

Selbst bei Nutzung externer Cloud-Modelle muss sichergestellt sein, dass keine besonders schützenswerten Personendaten
(PII) wie Namen, Kreditkartennummern oder Sozialversicherungsnummern die eigene Kontrolle verlassen. Menschliche Fehler,
wie das versehentliche Einfügen einer Kundenliste in ein Chat-Fenster, stellen hierbei ein signifikantes Risiko dar.

Der Swiss AI Hub implementiert technische Guardrails, die greifen, *bevor* eine Anfrage das interne Netzwerk verlässt.
Im LiteLLM-Proxy ist **Microsoft Presidio** als Sicherheitsmodul integriert, das jeden Prompt in Echtzeit auf definierte
Muster sensibler Daten scannt.

### Maskierungs- und Blockierungsmodi

Die Anonymisierung lässt sich granular konfigurieren, um Sicherheit und Funktionalität abzuwägen:

1. **Maskierungsmodus (Mask Mode):** Sensible Entitäten werden durch generische Platzhalter ersetzt (z.B. wird «Hans
   Müller» zu «[PERSON]» oder eine E-Mail zu «[EMAIL_ADDRESS]»). Die Struktur der Anfrage bleibt erhalten, sodass das
   externe Modell den Kontext verstehen und eine Antwort generieren kann, ohne die echten Daten zu sehen. Dies ist ideal
   für Szenarien, in denen der Kontext, aber nicht die Identität relevant ist.
2. **Blockierungsmodus (Block Mode):** Bei Erkennung hochkritischer Daten (z.B. Kreditkartennummern) wird die Anfrage
   vollständig blockiert und gar nicht erst an das Modell gesendet. Der Benutzer erhält eine Fehlermeldung, was die
   Compliance bei strikten "No-Go"-Daten gewährleistet.

Diese Prüfung erfolgt zentral auf der Infrastruktur-Ebene und gilt somit für alle angeschlossenen Agenten
gleichermassen, unabhängig vom verwendeten Modell.

## Interne Zugriffskontrolle und Governance

### Dynamische Dienstsichtbarkeit

Datensouveränität bedeutet nicht nur Schutz nach aussen, sondern auch Kontrolle im Inneren. Ein häufiges Problem bei
Enterprise-Software sind überladene Benutzeroberflächen, die Funktionen anzeigen, auf die der Nutzer keinen Zugriff hat.
Der Swiss AI Hub implementiert hier eine **dynamische Dienstsichtbarkeit**.

Beim Laden der Suite fragt das Frontend den autoritativen Rechtekatalog des Backends ab. Die Benutzeroberfläche rendert
daraufhin ausschliesslich jene Navigationselemente und Dienste, für die der Benutzer tatsächlich autorisiert ist. Ein
Data Scientist sieht Experimentier-Tools, während ein HR-Mitarbeiter nur Zugriff auf den Personal-Bot erhält. Nicht
autorisierte Dienste sind nicht nur ausgeblendet, sondern auf API-Ebene technisch unerreichbar («Security through
invisibility»). Dies verhindert, dass Benutzer durch URL-Manipulation auf verborgene Funktionen zugreifen können.

### Hierarchisches RBAC-System

Die Berechtigungsstruktur basiert auf einem granularen, hierarchischen **rollenbasierenden Zugriffskontrollsystem
(RBAC)**. Berechtigungen folgen einer Punkt-Notation (z.B. `aihub.user.agent.hr_bot`), was eine extrem feingliedrige
Steuerung erlaubt.

Das System unterstützt komplexe Wildcard-Berechtigungen:

- Einem Abteilungsleiter kann über `aihub.user.agent.hr.*` Zugriff auf alle HR-Agenten gewährt werden.
- Ein Power-User erhält über `aihub.user.agent.?>` Zugriff auf alle Agenten-Dienste.

Diese Architektur trennt zudem strikt administrative Privilegien von inhaltlichen Nutzungsrechten. Ein
Systemadministrator, der die Container wartet (Rolle `aihub.admin.service.*`), hat standardmässig keinen Einblick in die
Vektordatenbanken oder Chat-Historien der Geschäftsleitung, sofern dies nicht explizit konfiguriert ist. Dies entspricht
dem "Least Privilege"-Prinzip, das für Zertifizierungen wie ISO 27001 essentiell ist.

## Compliance, Auditierung und revDSG

### Transparenz durch Deep Observability

Um regulatorische Anforderungen wie das revDSG oder die DSGVO zu erfüllen, reicht einfaches Logging oft nicht aus. Der
Swiss AI Hub nutzt **OpenTelemetry** als fundamentales Framework für eine tiefe Observability (Beobachtbarkeit).

Jede Interaktion – von der Benutzeranfrage über den Agenten-Workflow bis hin zum LLM-Aufruf – wird als Trace erfasst.
Dies ermöglicht eine lückenlose Nachvollziehbarkeit:

- **Traceability:** Administratoren können exakt nachvollziehen, welche Dokumente für eine Antwort herangezogen wurden
  (RAG-Quellennachweis) und welches Modell zu welchem Zeitpunkt verwendet wurde.
- **Kostenattribution:** Token-Nutzung und API-Aufrufe werden bis auf den einzelnen Benutzer oder Agenten
  heruntergebrochen, was eine verursachergerechte Weiterverrechnung ermöglicht.

Diese Daten werden standardmässig an kompatible Backends wie **Phoenix** (für LLM-spezifische Analysen) oder SigNoz
exportiert, bleiben aber stets im Besitz des Kunden.

### Technische Massnahmen für Datenschutz

Die Plattform unterstützt spezifische Anforderungen des Schweizer Datenschutzgesetzes (revDSG) durch technische
Massnahmen ("Privacy by Design"):

- **Recht auf Löschung:** Ephemere Daten werden automatisch nach 30 Tagen gelöscht.
- **Recht auf Auskunft:** Über APIs können alle gespeicherten Daten zu einem Benutzerprofil extrahiert werden.
- **Audit-Sicherheit:** Audit-Logs sind unveränderlich und dokumentieren jede Änderung an Berechtigungen oder
  Konfigurationen, was für Compliance-Audits unerlässlich ist.

## Fazit: Souveränität als Standard

Der Swiss AI Hub etabliert Datensouveränität nicht als optionales Feature, sondern als unveränderlichen Standard der
Plattformarchitektur. Durch die physische Kontrolle über die Infrastruktur (Data Residency), die technische Entkopplung
von Modell-Anbietern (Model Independence) und die granulare Steuerung interner und externer Datenflüsse erhalten
Organisationen ihre volle strategische Handlungsfähigkeit zurück.

Sie entscheiden, wo Daten liegen, wer sie sieht und welche Modelle sie verarbeiten. Die Kombination aus technischer
Isolation durch Multi-Instancing und intelligenter Ressourcenteilung ermöglicht es, höchste Sicherheitsanforderungen zu
erfüllen, ohne auf die Effizienzvorteile moderner KI-Modelle verzichten zu müssen.
