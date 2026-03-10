---
title: Berechtigungs- und Zugriffsverwaltung
source_sha: 2879915908da11490d98e8af9a9ceddc76a6c4a2f6ba9b6f5cfec587b02f7a79
---

# Berechtigungs- und Zugriffsverwaltung

Die Benutzeroberfläche der Swiss AI Hub Suite implementiert eine ausgeklügelte berechtigungsbasierte Zugriffsverwaltung,
die die Benutzererfahrung dynamisch an das Autorisierungsniveau jedes Einzelnen anpasst. Dieser Ansatz stellt sicher,
dass Benutzer nur relevante Funktionen sehen und gleichzeitig Sicherheits- und Compliance-Anforderungen eingehalten
werden.

## Dynamische Service-Sichtbarkeit

Herkömmliche Anwendungsoberflächen präsentieren oft alle Funktionen allen Benutzern und verlassen sich auf
Authentifizierungsprüfungen, um unbefugten Zugriff zu blockieren. Dies führt zu überladenen Benutzeroberflächen voller
deaktivierter Schaltflächen und Funktionen, die Benutzer nicht nutzen können, was Verwirrung und Supportaufwand
verursacht. Der Swiss AI Hub überdenkt diesen Ansatz grundlegend durch dynamische Service-Sichtbarkeit.

**Berechtigungsgefilterter Service-Katalog**: Wenn die Suite geladen wird, fragt sie das Backend nach dem autorisierten
Service-Katalog des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes
registrierten Service und gibt nur die Services zurück, auf die der Benutzer zugreifen kann. Die Benutzeroberfläche
rendert Navigationselemente ausschließlich für autorisierte Services – Benutzer sehen einfach nie Funktionen, die sie
nicht nutzen können.

**Saubere, fokussierte Benutzeroberfläche**: Dieser Ansatz schafft dramatisch einfachere Benutzeroberflächen im
Vergleich zu traditionellen Anwendungen. Ein Data Scientist sieht Bewertungs- und Experimentierdienste prominent
dargestellt. Ein Business Analyst sieht Konversationsverläufe und Tools zur Wissenserforschung. Ein Administrator sieht
Optionen zur Benutzerverwaltung und Systemkonfiguration. Die Benutzeroberfläche jedes Benutzers spiegelt seine
tatsächlichen Fähigkeiten wider, nicht einen universellen Funktionsumfang, der mit unzugänglichen Optionen überladen
ist.

**Automatische Berechtigungs-Updates**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungen eines Benutzers
ändert, spiegeln sich diese Änderungen bei der nächsten Sitzung automatisch in der Benutzeroberfläche des Benutzers
wider. Es ist keine Cache-Invalidierung, manuelles Aktualisieren oder ein Ab-/Anmeldezyklus erforderlich. Die
Architektur der Suite stellt sicher, dass die Benutzeroberfläche immer eine genaue Ansicht des aktuellen
Autorisierungsstatus darstellt.

**Sicherheit durch Unsichtbarkeit**: Indem die Suite keine Navigationselemente für unautorisierte Services rendert,
eliminiert sie eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Services
durch Manipulation der Benutzeroberfläche zuzugreifen, da diese Services keine Präsenz in der Benutzeroberfläche haben.
Dieser Defense-in-Depth-Ansatz ergänzt die Autorisierungsdurchsetzung im Backend.

## Hierarchisches Berechtigungssystem

Die Suite integriert sich in das umfassende hierarchische Berechtigungssystem des Swiss AI Hub, das eine feingranulare
Zugriffsverwaltung durch eine strukturierte Punktnotations-Berechtigungssyntax bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format
`aihub.[user|admin].<service>.<resource_type>.<resource_id>`, wodurch ein hierarchischer Namespace geschaffen wird, der
eine präzise Zugriffsverwaltung ermöglicht. Zum Beispiel gewährt `aihub.user.agent.support_agent.instance_001` Zugriff
auf eine bestimmte Agent-Instanz, während `aihub.admin.knowledge` administrativen Zugriff auf den gesamten Knowledge
Management Service gewährt.

**Wildcard-Unterstützung**: Das Berechtigungssystem unterstützt ausgeklügelte Wildcards, die eine flexible
Zugriffsverwaltung ermöglichen, ohne dass jede Ressource explizit aufgelistet werden muss. Das `*`-Wildcard passt zu
jedem einzelnen Pfadsegment, während das `>`-Wildcard zu allen verbleibenden Pfadsegmenten passt. Dies ermöglicht Regeln
wie `aihub.user.agent.>`, um Zugriff auf alle Agent-Ressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle
Services auf Benutzerebene, ohne explizite Berechtigungen für jeden Service zu benötigen. Dies vereinfacht die
Berechtigungsverwaltung für Standardbenutzer und behält gleichzeitig eine feingranulare Kontrolle für spezielle
Zugriffsmuster bei.

**Service-Level-Zugriffsverwaltung**: Jeder Service Controller deklariert minimale Berechtigungsanforderungen für den
Zugriff. Der Suite-Endpunkt bewertet, ob der Benutzer diese Mindestberechtigungen besitzt, wenn der Servicekatalog
erstellt wird. Services, die Berechtigungen erfordern, die dem Benutzer fehlen, erscheinen einfach nicht in der
Katalogantwort.

## Rollenbasierte Benutzeroberflächenanpassung

Über die einfache Anzeige-/Ausblendelogik hinaus implementiert die Suite eine rollenbewusste Oberflächenanpassung, die
verschiedene Ansichten und Funktionen basierend auf den Autorisierungsstufen des Benutzers präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpunkt Berechtigungen bewertet, stellt er nicht nur fest, ob der
Benutzer auf einen Service zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Service besitzt.
Diese Unterscheidung wird an das Frontend kommuniziert, das innerhalb der Benutzeroberfläche dieses Service zusätzliche
administrative Funktionen präsentieren kann.

**Kontextbewusste Navigation**: Die Suite berücksichtigt den aktuellen Autorisierungskontext des Benutzers. Beim
Anzeigen eines Agents kann die Benutzeroberfläche feststellen, ob der Benutzer administrativen Zugriff auf diesen
spezifischen Agent hat, und zeigt administrative Steuerelemente wie die Konfigurationsbearbeitung nur bei entsprechender
Autorisierung an. Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Granulare Feature-Kontrolle**: Innerhalb einzelner Services kann die Benutzeroberfläche die Berechtigungen des
Benutzers für bestimmte Ressourcen oder Operationen abfragen. Ein Benutzer könnte Lesezugriff auf Wissensdatenbanken
haben, aber keine Upload-Berechtigungen. Die Benutzeroberfläche spiegelt dies wider, indem sie Funktionen zur
Wissenserforschung anzeigt, während Steuerelemente zum Hochladen von Dokumenten ausgeblendet werden.

**Multi-Mandanten-Isolation**: Bei Deployments, die mehrere Organisationseinheiten oder Kundenmandanten bedienen,
gewährleistet das Berechtigungssystem eine vollständige Datenisolation. Benutzer sehen nur Services und Ressourcen, die
zu ihrem organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb eines gemeinsam
genutzten Plattform-Deployments entstehen.

## Architektur der Berechtigungsbewertung

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen
Frontend-Abfragen und Backend-Evaluierungslogik.

**Backend-Berechtigungsbewertung**: Die gesamte Berechtigungsbewertung erfolgt im Backend, wodurch sichergestellt wird,
dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpunkt fragt
das Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen
vorgefilterten Service-Katalog zurück. Das Frontend vertraut diesem Katalog, ohne eine eigene Berechtigungslogik
auszuführen.

**Access-Checker-Integration**: Das Backend verwendet eine Access-Checker-Komponente, die die
Berechtigungsbewertungslogik kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster,
bewertet, ob die Zugriffsregeln des Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche
Zugriffsentscheidungen oder eine detaillierte Aufzählung der Zugriffsebenen zurück (verweigert, Benutzerzugriff,
administrativer Zugriff).

**Effiziente Berechtigungsabfragen**: Die Berechtigungsbewertung ist durch Caching-Strategien und effiziente
Musterabgleichalgorithmen auf Leistung optimiert. Wenn der Suite-Endpunkt die Service-Sichtbarkeit für einen Benutzer
bewertet, führt er diese Bewertungen parallel und nicht sequentiell durch, um reaktionsschnelle Ladezeiten der
Benutzeroberfläche auch bei zahlreichen Services zu gewährleisten.

**Generierung von Audit-Trails**: Jede Berechtigungsbewertung generiert Audit-Log-Einträge, die dokumentieren, welche
Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies schafft umfassende
Audit-Trails, die Compliance-Reporting und Sicherheitsforensik unterstützen.

## Service-spezifische Berechtigungsmuster

Verschiedene Services implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen
Anforderungen, was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agent Service**: Implementiert eine Zugriffsverwaltung pro Agent, bei der Benutzer möglicherweise Zugriff auf
bestimmte Agent-Instanzen haben, aber nicht auf andere. Berechtigungen wie `aihub.user.agent.customer_support.cs_001`
gewähren Zugriff auf einen spezifischen Agent, während `aihub.user.agent.customer_support.*` Zugriff auf alle Instanzen
dieser Agent-Klasse gewähren.

**Thread Service**: Steuert den Zugriff auf Konversations-Threads basierend auf Eigentums- und Freigaberegeln. Benutzer
haben in der Regel Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren für
Support- und Überwachungszwecke eine breitere Sichtbarkeit haben.

**Knowledge Service**: Implementiert eine Namespace-basierte Zugriffsverwaltung, bei der Berechtigungen auf
Datenbankebene (`aihub.user.knowledge.hr_documents`) oder Namespace-Ebene (`aihub.user.knowledge.hr_documents.policies`)
vergeben werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Services**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder
`aihub.admin.roles`. Diese Services erscheinen niemals für Benutzer ohne administrative Berechtigungen, wodurch eine
klare Trennung zwischen Standard- und administrativen Benutzeroberflächen geschaffen wird.

## Vorteile für die Benutzererfahrung

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile für die Benutzererfahrung und den Betrieb.

**Eliminierung von "Zugriff verweigert"-Fehlern**: Benutzer stoßen nie auf „Zugriff verweigert“-Meldungen für sichtbare
Benutzeroberflächenelemente, da unautorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine häufige Quelle
für Benutzerfrustration und Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Benutzeroberflächenkomplexität**: Indem nur autorisierte Funktionen angezeigt werden, bleibt die
Benutzeroberfläche übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht mental
von verfügbaren Funktionen filtern – alles, was sie sehen, können sie nutzen.

**Self-Service-Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie
beobachten, was in der Suite-Navigation erscheint. Es ist nicht nötig, separate Dokumentationen zu konsultieren oder den
Support zu kontaktieren, um herauszufinden, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die für ihre Rolle relevanten Funktionen, was die anfängliche
Plattformorientierung drastisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt den
Benutzern zu helfen, zu verstehen, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet Sicherheits- und Compliance-Vorteile, die über die Verbesserungen der
Benutzererfahrung hinausgehen.

**Defense in Depth**: Das clientseitige Filtern unautorisierter Services ergänzt die Backend-Berechtigungsdurchsetzung
und schafft so mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend manipuliert, verhindert die
Backend-Autorisierungsdurchsetzung unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem keine Informationen über Services preisgegeben werden, auf die Benutzer nicht
zugreifen können, enthüllt die Suite potenziellen Angreifern weniger über die Funktionen des Deployments. Benutzer
können deaktivierte Funktionen nicht sondieren, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsbewertungen unterstützt die
regulatorischen Compliance-Anforderungen für die Zugriffsverwaltung, insbesondere in Sektoren mit strengen
Datenschutzanforderungen wie Gesundheitswesen, Finanzen und öffentlicher Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Service-Zugriff eine
explizite Berechtigungsbewertung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf dem
Netzwerkstandort oder früherer Authentifizierung – jede Operation wird unabhängig autorisiert.

## Operationelle Vorteile

Neben Sicherheit und Benutzererfahrung bietet das Berechtigungssystem operationelle Vorteile für
Plattformadministratoren.

**Zentralisierte Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenmanagement-Service,
wobei Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht erforderlich,
Zugriffssteuerungen separat für jeden Service zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu
koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgeklügelte Delegationsmuster. Älteren
Mitarbeitern können umfassende Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während jüngere Mitarbeiter
spezifische Berechtigungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt Organisationsstrukturen,
ohne komplexe Zugriffssteuerungskonfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, bei der das Gewähren von
Zugriff auf eine Ressource höherer Ebene automatisch den Zugriff auf enthaltene Ressourcen ermöglicht. Dies vereinfacht
die Berechtigungsverwaltung und behält gleichzeitig bei Bedarf eine präzise Kontrolle bei.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren
Benutzern in der Regel Rollen zu, die Standardberechtigungssätze definieren. Rollenänderungen werden automatisch auf
alle zugewiesenen Benutzer angewendet, wodurch eine konsistente Zugriffsverwaltung über alle Benutzergruppen hinweg
gewährleistet wird.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte,
sichere Benutzeroberfläche bietet, die präzise auf sein Autorisierungsniveau und seine organisatorische Rolle
zugeschnitten ist, wobei die operationelle Einfachheit und die Sicherheitsstrenge gewahrt bleiben, die für Enterprise-
und Public-Sector-Deployments erforderlich sind.

# Rollenbasierte Zugriffsverwaltung (RBAC)

## Überblick

**Role-Based Access Control (RBAC)** ist ein Sicherheitsframework, das den Systemzugriff basierend auf Benutzerrollen
innerhalb einer Organisation einschränkt. Der Swiss AI Hub implementiert ein hierarchisches RBAC-System mit
mandantenspezifischen Rollen, das eine granulare Kontrolle über jeden Aspekt der Plattform bietet.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können (lokal verwaltet, nicht
  von Identitätsanbietern synchronisiert)
- **Mandanten**: Organisationale Grenzen, die Rollenzuweisungen definieren
- **Zugriffsregeln**: Spezifische Berechtigungen in Punktnotation (z. B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Authentifiziert über OAuth2/OIDC, wobei Rollen aus der lokalen mandantenspezifischen
  Rollendatenbank aufgelöst werden
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Wildcard-Unterstützung**: Flexibler Musterabgleich mittels `*`, `>`, `?*` und `?>` Wildcards

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` - Benutzerzugriff auf spezifischen Agent
- `aihub.admin.service.roles` - Administratorzugriff auf Rollenverwaltung
- `aihub.user.agent.?>` - Benutzerzugriff auf beliebigen Agent (Wildcard)

Für Details zu Multi-Tenancy und Zugriffsverwaltung siehe die Dokumentation unter
[Multi-Tenancy Access Control](/de/docs/16_multi_tenancy/4_access_control/).
