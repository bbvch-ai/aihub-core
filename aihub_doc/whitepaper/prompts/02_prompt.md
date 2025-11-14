# Kapitel 02: Plattform-Überblick - Die Swiss AI-Hub-Lösung

## Kapitelziel
Erklären Sie, was Swiss AI-Hub ist und wie es die in Kapitel 01 genannten Herausforderungen löst (600 Wörter, 2 Seiten).

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **kurz** (600 Wörter).

## Business-Dimensionen (Priorität für dieses Kapitel)
1. **ALLE DIMENSIONEN** - Kurze Erwähnung als Lösungsüberblick
2. Fokus: Wie die Plattform die in Kap. 01 genannten Probleme löst

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Themen und Inhalte

Beschreiben Sie folgende Themen und deren geschäftlichen Nutzen:

- **Was ist Swiss AI-Hub**: Komplette Enterprise-AI-Plattform zum selbst betreiben (nicht SaaS, Framework oder Managed Service, sondern produktionsreife Infrastruktur); Dreistufige Architektur in Business-Begriffen (Tier 1: Sicherer AI-Zugang wie privates ChatGPT, Tier 1+: Tool-Integration in Teams/Slack/Email, Tier 2: AI mit organisationalem Wissen/RAG, Tier 3: Prozessautomatisierung mit AI+Menschen+Systemen); Geschäftlicher Nutzen: Mehrere Use Cases mit einer Plattform, progressive Adoption (einfach starten, bei Bedarf erweitern), vollständige Kontrolle, Schweizer Datensouveränität eingebaut

- **Vollständige enthaltene Infrastruktur ("Batteries included")**: AI-Model-Gateway (LiteLLM für universellen Providerzugang), Wissenssystem (Vector-Datenbanken, Dokumentenverarbeitung), Event-Bus (NATS für Echtzeit-Koordination), Daten-Pipelines (Dagster für automatisierte Ingestion), Authentifizierung (OAuth/OIDC, Enterprise-Grade), Monitoring (OpenTelemetry, Phoenix), Benutzeroberflächen (Chat, Admin-Dashboard, Prozess-Management sofort nutzbar), Speichersysteme (Datenbanken, Vector-Stores, Object-Storage integriert); Geschäftlicher Nutzen: Keine zusätzliche Beschaffung, Komponenten bereits integriert, produktionsreif ab Tag 1 (30-Minuten-Deployment), keine Vendor-Abhängigkeiten für einzelne Komponenten

- **Open Source und Anbieter-Unabhängigkeit**: Apache-2.0-Lizenz (vollständig Open Source, permissive); Praktische Bedeutung (kein Vendor-Lock-in, Code gehört Ihnen/inspizierbar/modifizierbar, keine Lizenzgebühren, nur Infrastruktur bezahlen, transparenter Betrieb ohne Black Boxes, Community-getrieben, zukunftssicher selbst wenn Vendor verschwindet); Vendor-neutrale Basis (aufgebaut auf Open-Source-Komponenten), kommerzielles Ökosystem (Professional Services und Support verfügbar aber optional); Geschäftlicher Nutzen: Risikominderung (keine Abhängigkeit von einzelnem Vendor), Kostentransparenz (keine versteckten Gebühren/Per-User-Lizenzierung), Flexibilität (anpassen/erweitern/forken nach Bedarf), langfristige Tragfähigkeit (Open Source sichert Plattform-Langlebigkeit)

## Business-Fragen, die das Kapitel beantwortet

1. Was ist Swiss AI-Hub in einem Satz?
2. Wie unterscheidet sich das von direkter Nutzung von ChatGPT oder Azure OpenAI?
3. Was macht dies zu einer "Plattform" vs. "Framework" oder "Service"?
4. Warum ist "batteries included" für Business wichtig?
5. Welche Komponenten sind enthalten, welche erfordern zusätzliche Beschaffung?
6. Können wir wirklich in 30 Minuten deployen und produktionsreif sein?
7. Welches Lizenzmodell verwendet die Plattform?
8. Was bedeutet "Open Source" praktisch für unsere Organisation?
9. Gibt es laufende Lizenzgebühren oder Per-User-Fees?
10. Wie unterscheiden sich die Kosten von Cloud-AI-Services?
11. Unterstützt die Plattform verschiedene AI-Modelle und Use Cases?
12. Sind spätere Erweiterungen möglich?
13. Können einzelne Komponenten ausgetauscht werden?
14. Wie modular ist die Architektur?
15. Bin ich an einen bestimmten AI-Provider gebunden?
16. Was passiert, wenn der Plattform-Anbieter das Geschäft einstellt?
17. Kann ich die Plattform nach meinen Bedürfnissen anpassen?
18. Wie zukunftssicher ist die Investition?
