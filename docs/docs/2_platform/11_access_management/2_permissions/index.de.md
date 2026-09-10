---
title: Berechtigungs- und Zugriffssteuerung
source_sha: b0f545d17acf875a94c437e2c0509823791828fe5a8fcfeb566cfe139862f0aa
---

# Berechtigungs- und Zugriffssteuerung

Die Benutzeroberfläche der Swiss AI Hub Suite implementiert eine ausgeklügelte berechtigungsbasierte Zugriffssteuerung,
die das Benutzererlebnis dynamisch an das Autorisierungsniveau jedes Einzelnen anpasst. Dieser Ansatz stellt sicher,
dass Benutzer nur relevante Funktionen sehen, während gleichzeitig Sicherheits- und Compliance-Anforderungen erfüllt
werden.

## Dynamische Service-Sichtbarkeit

Herkömmliche Anwendungsoberflächen präsentieren oft alle Funktionen allen Benutzern und verlassen sich auf
Authentifizierungsprüfungen, um unautorisierten Zugriff zu blockieren. Dies führt zu überladenen Benutzeroberflächen mit
deaktivierten Schaltflächen und Funktionen, die Benutzer nicht nutzen können, was Verwirrung und Supportaufwand
verursacht. Der Swiss AI Hub überdenkt diesen Ansatz grundlegend durch dynamische Service-Sichtbarkeit.

**Berechtigungsgefilterter Service-Katalog**: Wenn die Suite geladen wird, fragt sie das Backend nach dem autorisierten
Service-Katalog des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes
registrierten Services und gibt nur Services zurück, auf die der Benutzer zugreifen kann. Die Benutzeroberfläche rendert
Navigationselemente ausschließlich für autorisierte Services – Benutzer sehen einfach niemals Funktionen, die sie nicht
nutzen können.

**Saubere, fokussierte Oberfläche**: Dieser Ansatz schafft im Vergleich zu herkömmlichen Anwendungen dramatisch
einfachere Benutzeroberflächen. Ein Data Scientist sieht Evaluations- und Experimentier-Services prominent dargestellt.
Ein Business Analyst sieht Konversationsverläufe und Wissenserkundungstools. Ein Administrator sieht Benutzerverwaltung
und Systemkonfigurationsoptionen. Die Benutzeroberfläche jedes Benutzers spiegelt seine tatsächlichen Fähigkeiten wider,
nicht einen universellen Funktionssatz, der mit unzugänglichen Optionen überladen ist.

**Automatische Berechtigungsaktualisierungen**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungen eines
Benutzers ändert, spiegeln sich diese Änderungen automatisch in der Benutzeroberfläche des Benutzers in dessen nächster
Session wider. Es ist keine Cache-Invalidierung, manuelle Aktualisierung oder Abmelde-Anmelde-Zyklus erforderlich. Die
Architektur der Suite stellt sicher, dass die Benutzeroberfläche immer eine genaue Ansicht des aktuellen
Autorisierungsstatus darstellt.

**Sicherheit durch Unsichtbarkeit**: Indem die Suite unautorisierte Service-Navigationselemente nicht rendert,
eliminiert sie eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Services
durch Schnittstellenmanipulation zuzugreifen, da diese Services keine Schnittstellenpräsenz haben. Dieser
Defense-in-Depth-Ansatz ergänzt die Backend-Autorisierungsdurchsetzung.

## Hierarchisches Berechtigungssystem

Die Suite ist in das umfassende hierarchische Berechtigungssystem des Swiss AI Hub integriert, das eine feingranulare
Zugriffssteuerung durch eine strukturierte, Punkt-Notation-Berechtigungssyntax bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format
`aihub.[user|admin].<service>.<resource_type>.<resource_id>`, wodurch ein hierarchischer Namespace geschaffen wird, der
eine präzise Zugriffssteuerung ermöglicht. Zum Beispiel gewährt `aihub.user.agent.support_agent.instance_001` Zugriff
auf eine spezifische Agent-Instanz, während `aihub.admin.knowledge` administrativen Zugriff auf den gesamten
Wissensmanagement-Service gewährt.

**Wildcard-Unterstützung**: Das Berechtigungssystem unterstützt ausgeklügelte Wildcards, die eine flexible
Zugriffssteuerung ermöglichen, ohne dass jede Ressource explizit aufgelistet werden muss. Die Wildcard `*` entspricht
jedem einzelnen Pfadsegment, während die Wildcard `>` allen verbleibenden Pfadsegmenten entspricht. Dies ermöglicht
Regeln wie `aihub.user.agent.>` um Zugriff auf alle Agent-Ressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle
Services auf Benutzerebene, ohne dass für jeden Service explizite Berechtigungen erforderlich sind. Dies vereinfacht die
Berechtigungsverwaltung für Standardbenutzer, während eine feingranulare Kontrolle für spezialisierte Zugriffsmuster
beibehalten wird.

**Service-Level Zugriffssteuerung**: Jeder Service-Controller deklariert minimale Berechtigungsanforderungen für den
Zugriff. Der Suite-Endpoint bewertet, ob der Benutzer diese minimalen Berechtigungen beim Erstellen des Service-Katalogs
besitzt. Services, die Berechtigungen erfordern, die dem Benutzer fehlen, erscheinen einfach nicht in der
Katalogantwort.

## Rollenbasierte Schnittstellenanpassung

Über die einfache Anzeige-/Verbergelogik hinaus implementiert die Suite eine rollenbewusste Schnittstellenanpassung, die
unterschiedliche Ansichten und Funktionen basierend auf den Autorisierungsstufen des Benutzers präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpoint Berechtigungen auswertet, stellt er nicht nur fest, ob der
Benutzer auf einen Service zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Service besitzt.
Diese Unterscheidung wird dem Frontend mitgeteilt, das zusätzliche administrative Funktionen innerhalb der Schnittstelle
dieses Services präsentieren kann.

**Kontextsensitive Navigation**: Die Suite bewahrt das Bewusstsein für den aktuellen Autorisierungskontext des
Benutzers. Beim Anzeigen eines Agenten kann die Benutzeroberfläche feststellen, ob der Benutzer administrativen Zugriff
auf diesen spezifischen Agenten hat, und administrative Steuerungen wie die Konfigurationsbearbeitung nur bei
Autorisierung präsentieren. Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Granulare Funktionssteuerung**: Innerhalb einzelner Services kann die Benutzeroberfläche die Berechtigungen des
Benutzers für spezifische Ressourcen oder Operationen abfragen. Ein Benutzer könnte Lesezugriff auf Wissensdatenbanken
haben, aber keine Upload-Berechtigungen. Die Benutzeroberfläche spiegelt dies wider, indem sie
Wissenserkundungsfunktionen anzeigt, während sie die Steuerelemente zum Hochladen von Dokumenten ausblendet.

**Multi-Tenant-Isolation**: In Deployments, die mehrere Organisationseinheiten oder Kunden-Mandanten bedienen, stellt
das Berechtigungssystem eine vollständige Datenisolation sicher. Benutzer sehen nur Services und Ressourcen, die zu
ihrem organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb eines gemeinsam genutzten
Plattform-Deployments entstehen.

## Architektur der Berechtigungsprüfung

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen
Frontend-Abfragen und Backend-Evaluierungslogik.

**Backend-Berechtigungsprüfung**: Die gesamte Berechtigungsprüfung findet im Backend statt, wodurch sichergestellt wird,
dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpoint fragt
das Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen
vorgefilterten Service-Katalog zurück. Das Frontend vertraut diesem Katalog, ohne eine eigene Berechtigungslogik
auszuführen.

**Access Checker Integration**: Das Backend verwendet eine Access Checker Komponente, die die Berechtigungsprüfungslogik
kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster, bewertet, ob die Zugriffsregeln
des Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche Zugriffsentscheidungen oder eine detaillierte
Aufzählung der Zugriffsebene zurück (verweigert, Benutzerzugriff, administrativer Zugriff).

**Effiziente Berechtigungsabfragen**: Die Berechtigungsprüfung ist durch Caching-Strategien und effiziente
Musterabgleichs-Algorithmen auf Performance optimiert. Wenn der Suite-Endpoint die Service-Sichtbarkeit für einen
Benutzer bewertet, führt er diese Bewertungen parallel statt sequenziell durch, um reaktionsschnelle Ladezeiten der
Benutzeroberfläche auch bei zahlreichen Services zu gewährleisten.

**Generierung von Audit-Trails**: Jede Berechtigungsprüfung generiert Audit-Log-Einträge, die dokumentieren, welche
Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies schafft umfassende
Audit-Trails, die Compliance-Berichte und Sicherheits-Forensik unterstützen.

## Servicespezifische Berechtigungsmuster

Verschiedene Services implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen
Anforderungen, was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agent Service**: Implementiert eine Zugriffskontrolle pro Agent, bei der Benutzer Zugriff auf spezifische
Agent-Instanzen haben können, aber nicht auf andere. Berechtigungen wie `aihub.user.agent.customer_support.cs_001`
gewähren Zugriff auf einen spezifischen Agenten, während `aihub.user.agent.customer_support.*` Zugriff auf alle
Instanzen dieser Agentenklasse gewährt.

**Thread Service**: Steuert den Zugriff auf Konversations-Threads basierend auf Besitz- und Freigaberegeln. Benutzer
haben im Allgemeinen Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren
eine breitere Sichtbarkeit für Support- und Überwachungszwecke haben.

**Knowledge Service**: Implementiert eine Namespace-basierte Zugriffssteuerung, bei der Berechtigungen auf
Datenbankebene (`aihub.user.knowledge.hr_documents`) oder Namespace-Ebene (`aihub.user.knowledge.hr_documents.policies`)
erteilt werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Services**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder
`aihub.admin.roles`. Diese Services erscheinen niemals für Benutzer ohne administrative Berechtigungen, wodurch eine
klare Trennung zwischen Standard- und administrativen Schnittstellen geschaffen wird.

## Vorteile für die Benutzererfahrung

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile für die Benutzererfahrung und den Betrieb.

**Eliminierung von "Zugriff verweigert"-Fehlern**: Benutzer stoßen niemals auf "Zugriff verweigert"-Meldungen für
sichtbare Schnittstellenelemente, da unautorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine häufige
Quelle der Benutzerfrustration und von Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Schnittstellenkomplexität**: Indem nur autorisierte Funktionen angezeigt werden, bleibt die
Benutzeroberfläche übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht mental
von verfügbaren Funktionen filtern – alles, was sie sehen, können sie nutzen.

**Self-Service Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie
beobachten, was in der Suite-Navigation erscheint. Es ist nicht notwendig, separate Dokumentationen zu konsultieren oder
den Support zu kontaktieren, um herauszufinden, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die für ihre Rolle relevanten Funktionen, was die anfängliche
Plattform-Orientierung dramatisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt
Benutzern zu helfen, zu verstehen, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet Sicherheits- und Compliance-Vorteile, die über die Verbesserungen der
Benutzererfahrung hinausgehen.

**Defense in Depth**: Clientseitige Filterung unautorisierter Services ergänzt die Backend-Berechtigungsdurchsetzung und
schafft so mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend manipuliert, verhindert die
Backend-Autorisierungsdurchsetzung unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem keine Informationen über Services preisgegeben werden, auf die Benutzer keinen
Zugriff haben, offenbart die Suite potenziellen Angreifern weniger über die Fähigkeiten des Deployments. Benutzer können
deaktivierte Funktionen nicht sondieren, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsprüfungen unterstützt die
regulatorischen Compliance-Anforderungen für die Zugriffssteuerung, insbesondere in Sektoren mit strengen
Datenschutzanforderungen wie Gesundheitswesen, Finanzen und öffentliche Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Service-Zugriff eine
explizite Berechtigungsprüfung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf Netzwerkstandort
oder vorheriger Authentifizierung – jede Operation wird unabhängig autorisiert.

## Operative Vorteile

Neben Sicherheit und Benutzererfahrung bietet das Berechtigungssystem operative Vorteile für Plattform-Administratoren.

**Zentralisierte Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenmanagement-Service,
wobei Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht notwendig, Zugriffssteuerungen
für jeden Service separat zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgeklügelte Delegationsmuster. Leitenden
Mitarbeitern können breite Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während Nachwuchskräfte spezifische
Berechtigungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt Organisationsstrukturen, ohne komplexe
Zugriffssteuerungs-Konfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, wobei die Gewährung des
Zugriffs auf eine Ressource höherer Ebene automatisch den Zugriff auf enthaltene Ressourcen ermöglicht. Dies vereinfacht
die Berechtigungsverwaltung, während bei Bedarf eine präzise Kontrolle beibehalten wird.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren
Benutzern typischerweise Rollen zu, die Standardberechtigungssätze definieren. Rollenänderungen gelten automatisch für
alle zugewiesenen Benutzer und gewährleisten eine konsistente Zugriffssteuerung über Benutzerpopulationen hinweg.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte,
sichere Oberfläche bietet, die präzise auf sein Autorisierungsniveau und seine organisatorische Rolle zugeschnitten ist,
während gleichzeitig die betriebliche Einfachheit und Sicherheit beibehalten wird, die für Unternehmens- und öffentliche
Sektor-Deployments erforderlich sind.

# Rollenbasierte Zugriffssteuerung (RBAC)

## Überblick

**Rollenbasierte Zugriffssteuerung (RBAC)** ist ein Sicherheits-Framework, das den Systemzugriff basierend auf
Benutzerrollen innerhalb einer Organisation einschränkt. Der Swiss AI Hub implementiert ein hierarchisches RBAC-System
mit Mandant-spezifischen Rollen, das eine feingranulare Kontrolle über jeden Aspekt der Plattform bietet.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können (lokal verwaltet, nicht
  von Identitätsanbietern synchronisiert)
- **Mandanten**: Organisatorische Grenzen, die Rollenzuweisungen umfassen
- **Zugriffsregeln**: Spezifische Berechtigungen unter Verwendung der Punkt-Notation (z.B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Authentifiziert via OAuth2/OIDC, wobei Rollen aus der lokalen Mandant-spezifischen
  Rollendatenbank aufgelöst werden
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Wildcard-Unterstützung**: Flexibler Musterabgleich mit `*`, `>`, `?*` und `?>` Wildcards

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` – Benutzerzugriff auf spezifischen Agenten
- `aihub.admin.service.roles` – Admin-Zugriff auf Rollenverwaltung
- `aihub.user.agent.?>` – Benutzerzugriff auf beliebigen Agenten (Wildcard)

Für weitere Details zu Multi-Tenancy und Zugriffssteuerung siehe die Dokumentation zu
[Multi-Tenancy-Zugriffssteuerung](../../16_multi_tenancy/4_access_control/).
