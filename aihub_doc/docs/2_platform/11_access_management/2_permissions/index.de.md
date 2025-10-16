---
title: Berechtigungs- und Zugriffssteuerung
index: 2
source_sha: "de93d4a2641f62a6d9a23ac82ec68816b0c1da3598ade5539e487c1c47ed8c89"
---

# Berechtigungs- und Zugriffssteuerung

Die Oberfläche der Swiss AI Hub Suite implementiert eine ausgeklügelte berechtigungsbasierte Zugriffssteuerung, die das
Benutzererlebnis dynamisch an das Autorisierungslevel jedes Einzelnen anpasst. Dieser Ansatz stellt sicher, dass Benutzer
nur relevante Funktionen sehen, während gleichzeitig Sicherheits- und Compliance-Anforderungen eingehalten werden.

## Dynamische Sichtbarkeit von Services

Herkömmliche Anwendungsoberflächen präsentieren oft alle Funktionen allen Benutzern und verlassen sich auf Authentifizierungsprüfungen,
um unautorisierten Zugriff zu blockieren. Dies führt zu überladenen Oberflächen mit deaktivierten Schaltflächen und Funktionen,
die Benutzer nicht nutzen können, was zu Verwirrung und Supportaufwand führt. Der Swiss AI Hub überdenkt diesen Ansatz
grundlegend durch dynamische Servicesichtbarkeit.

**Berechtigungsgefilterter Servicekatalog**: Beim Laden der Suite fragt sie das Backend nach dem autorisierten Servicekatalog
des Benutzers ab. Das Backend bewertet die Berechtigungen des Benutzers anhand der Anforderungen jedes registrierten
Services und gibt nur die Services zurück, auf die der Benutzer zugreifen kann. Die Oberfläche rendert Navigationselemente
ausschließlich für autorisierte Services – Benutzer sehen Funktionen, die sie nicht nutzen können, einfach nie.

**Saubere, fokussierte Oberfläche**: Dieser Ansatz schafft im Vergleich zu traditionellen Anwendungen dramatisch einfachere
Oberflächen. Ein Data Scientist sieht prominente Bewertungs- und Experimentierdienste. Ein Business Analyst sieht
Konversations-Threads und Tools zur Wissenserkundung. Ein Administrator sieht Benutzerverwaltung und Systemkonfigurationsoptionen.
Die Oberfläche jedes Benutzers spiegelt seine tatsächlichen Fähigkeiten wider, nicht einen universellen Funktionsumfang,
der mit unzugänglichen Optionen überladen ist.

**Automatische Berechtigungsaktualisierungen**: Wenn ein Administrator die Rollenzuweisungen oder Berechtigungszuteilungen
eines Benutzers ändert, spiegeln sich diese Änderungen automatisch in der Benutzeroberfläche des Benutzers in dessen
nächster Sitzung wider. Es ist keine Cache-Invalidierung, manuelle Aktualisierung oder ein Abmelde-/Anmeldezyklus erforderlich.
Die Architektur der Suite stellt sicher, dass die Oberfläche stets eine genaue Ansicht des aktuellen Autorisierungsstatus
präsentiert.

**Sicherheit durch Unsichtbarkeit**: Indem keine Navigationselemente für nicht autorisierte Services gerendert werden,
eliminiert die Suite eine ganze Klasse von Sicherheitslücken. Benutzer können nicht versuchen, auf eingeschränkte Services
durch Oberflächenmanipulation zuzugreifen, da diese Services keine Präsenz in der Oberfläche haben. Dieser
Defense-in-Depth-Ansatz ergänzt die Backend-Autorisierungsdurchsetzung.

## Hierarchisches Berechtigungssystem

Die Suite integriert sich in das umfassende hierarchische Berechtigungssystem des Swiss AI Hubs, das eine
feingranulare Zugriffssteuerung durch eine strukturierte, punktnotierte Berechtigungssyntax bietet.

**Berechtigungsstruktur**: Berechtigungen folgen dem Format `aihub.[user|admin].<service>.<resource_type>.<resource_id>`
und schaffen einen hierarchischen Namensraum, der eine präzise Zugriffssteuerung ermöglicht. Zum Beispiel gewährt
`aihub.user.agent.support_agent.instance_001` Zugriff auf eine bestimmte Agenteninstanz, während `aihub.admin.knowledge`
administrativen Zugriff auf den gesamten Wissensmanagement-Service gewährt.

**Platzhalter-Unterstützung**: Das Berechtigungssystem unterstützt ausgeklügelte Platzhalter, die eine flexible
Zugriffssteuerung ermöglichen, ohne dass jede Ressource explizit aufgelistet werden muss. Der Platzhalter `*` stimmt
mit jedem einzelnen Pfadsegment überein, während der Platzhalter `>` mit allen verbleibenden Pfadsegmenten übereinstimmt.
Dies ermöglicht Regeln wie `aihub.user.agent.>`, um Zugriff auf alle Agentenressourcen in beliebiger Tiefe zu gewähren.

**Implizite Berechtigungen**: Benutzer mit dem impliziten Berechtigungsmuster `aihub.user.?>` erhalten Zugriff auf alle
Services auf Benutzerebene, ohne dass explizite Zuteilungen für jeden Service erforderlich sind. Dies vereinfacht die
Berechtigungsverwaltung für Standardbenutzer, während eine feingranulare Kontrolle für spezielle Zugriffsmuster
beibehalten wird.

**Service-Level-Zugriffssteuerung**: Jeder Service-Controller deklariert minimale Berechtigungsanforderungen für den
Zugriff. Der Suite-Endpunkt bewertet, ob der Benutzer diese minimalen Berechtigungen besitzt, wenn er den Servicekatalog
erstellt. Services, die Berechtigungen erfordern, die der Benutzer nicht besitzt, erscheinen einfach nicht in der
Katalogantwort.

## Rollenbasierte Oberflächenanpassung

Über eine einfache Anzeige-/Ausblende-Logik hinaus implementiert die Suite eine rollenbewusste Oberflächenanpassung,
die verschiedene Ansichten und Funktionen basierend auf den Autorisierungsstufen des Benutzers präsentiert.

**Administrative Privilegien**: Wenn der Suite-Endpunkt Berechtigungen evaluiert, bestimmt er nicht nur, ob der Benutzer
auf einen Service zugreifen kann, sondern auch, ob er administrative Privilegien für diesen Service besitzt. Diese
Unterscheidung wird dem Frontend mitgeteilt, das zusätzliche administrative Funktionen innerhalb der Oberfläche des
Services präsentieren kann.

**Kontextbezogene Navigation**: Die Suite behält das aktuelle Autorisierungskontext des Benutzers bei. Beim Anzeigen eines
Agenten kann die Oberfläche feststellen, ob der Benutzer administrativen Zugriff auf diesen spezifischen Agenten hat,
und administrative Steuerelemente wie die Konfigurationsbearbeitung nur dann anzeigen, wenn diese autorisiert sind.
Standardbenutzer sehen schreibgeschützte Ansichten derselben Ressourcen.

**Granulare Funktionskontrolle**: Innerhalb einzelner Services kann die Oberfläche die Berechtigungen des Benutzers für
spezifische Ressourcen oder Operationen abfragen. Ein Benutzer hat möglicherweise Lesezugriff auf Wissensdatenbanken,
aber keine Upload-Berechtigungen. Die Oberfläche spiegelt dies wider, indem sie Funktionen zur Wissenserkundung anzeigt,
während Steuerelemente für den Dokumenten-Upload ausgeblendet werden.

**Mandantenisolation**: In Bereitstellungen, die mehrere Organisationseinheiten oder Kundenmandanten bedienen, gewährleistet
das Berechtigungssystem eine vollständige Datenisolation. Benutzer sehen nur Services und Ressourcen, die zu ihrem
organisatorischen Kontext gehören, wodurch sichere, isolierte Arbeitsbereiche innerhalb einer gemeinsamen Plattformbereitstellung
geschaffen werden.

## Berechtigungsauswertungsarchitektur

Das berechtigungsbewusste Verhalten der Suite resultiert aus einer ausgeklügelten Koordination zwischen Frontend-Abfragen
und Backend-Evaluierungslogik.

**Backend-Berechtigungsauswertung**: Die gesamte Berechtigungsauswertung erfolgt im Backend, wodurch sichergestellt wird,
dass die Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Der Suite-Endpunkt fragt das
Berechtigungssystem ab, bewertet Zugriffsregeln anhand der Rollen und Berechtigungen des Benutzers und gibt einen
vorgefilterten Servicekatalog zurück. Das Frontend vertraut diesem Katalog, ohne eigene Berechtigungslogik auszuführen.

**Access Checker Integration**: Das Backend verwendet eine Access Checker-Komponente, die die Berechtigungsauswertungslogik
kapselt. Diese Komponente akzeptiert eine Benutzeridentität und ein Berechtigungsmuster, bewertet, ob die Zugriffsregeln des
Benutzers mit dem Muster übereinstimmen, und gibt entweder boolesche Zugriffsentscheidungen oder eine detaillierte
Auflistung der Zugriffsebene (verweigert, Benutzerzugriff, administrativer Zugriff) zurück.

**Effiziente Berechtigungsabfragen**: Die Berechtigungsauswertung ist auf Leistung optimiert durch Caching-Strategien
und effiziente Mustervergleichsalgorithmen. Wenn der Suite-Endpunkt die Servicesichtbarkeit für einen Benutzer auswertet,
führt er diese Auswertungen parallel statt sequenziell durch, um reaktionsschnelle Ladezeiten der Oberfläche auch bei
zahlreichen Services zu gewährleisten.

**Generierung von Audit-Trails**: Jede Berechtigungsauswertung generiert Audit-Log-Einträge, die dokumentieren, welche
Berechtigungen geprüft wurden, für welchen Benutzer und welche Entscheidung getroffen wurde. Dies erstellt umfassende
Audit-Trails, die Compliance-Berichte und Sicherheitsforensik unterstützen.

## Servicespezifische Berechtigungsmuster

Verschiedene Services implementieren unterschiedliche Berechtigungsmuster basierend auf ihren funktionalen Anforderungen,
was die Flexibilität des hierarchischen Berechtigungssystems demonstriert.

**Agenten-Service**: Implementiert eine Zugriffskontrolle pro Agent, bei der Benutzer möglicherweise Zugriff auf spezifische
Agenteninstanzen haben, aber nicht auf andere. Berechtigungen wie `aihub.user.agent.customer_support.cs_001` gewähren
Zugriff auf einen spezifischen Agenten, während `aihub.user.agent.customer_support.*` Zugriff auf alle Instanzen dieser
Agentenklasse gewährt.

**Thread-Service**: Steuert den Zugriff auf Konversations-Threads basierend auf Eigentums- und Freigaberegeln. Benutzer
haben in der Regel Zugriff auf Threads, die sie erstellt oder an denen sie teilgenommen haben, wobei Administratoren
eine breitere Sichtbarkeit für Support- und Überwachungszwecke haben.

**Wissens-Service**: Implementiert eine namensraumbasierte Zugriffssteuerung, bei der Berechtigungen auf Datenbankebene
(`aihub.user.knowledge.hr_documents`) oder auf Namensraumebene (`aihub.user.knowledge.hr_documents.policies`) erteilt
werden können, mit hierarchischer Vererbung durch den Berechtigungsbaum.

**Administrative Services**: Erfordern explizite administrative Berechtigungen wie `aihub.admin.users` oder `aihub.admin.roles`.
Diese Services erscheinen niemals für Benutzer ohne administrative Zuteilungen und schaffen so eine klare Trennung
zwischen Standard- und administrativen Oberflächen.

## Vorteile für die Benutzererfahrung

Die berechtigungsbewusste Suite-Architektur bietet erhebliche Vorteile für die Benutzererfahrung und den operativen Betrieb.

**Vermeidung von „Zugriff verweigert“-Fehlern**: Benutzer stoßen nie auf „Zugriff verweigert“-Meldungen für sichtbare
Oberflächenelemente, da nicht autorisierte Funktionen einfach nicht erscheinen. Dies eliminiert eine häufige Quelle für
Benutzerfrustration und Support-Tickets in traditionellen Unternehmensanwendungen.

**Reduzierte Komplexität der Oberfläche**: Indem nur autorisierte Funktionen angezeigt werden, bleibt die Oberfläche
übersichtlich und fokussiert. Benutzer müssen sichtbare, aber deaktivierte Funktionen nicht mental von verfügbaren
Funktionen trennen – alles, was sie sehen, können sie auch nutzen.

**Self-Service-Zugriffsverständnis**: Benutzer können ihre autorisierten Funktionen sofort verstehen, indem sie beobachten,
was in der Suitennavigation erscheint. Es ist nicht notwendig, separate Dokumentationen zu konsultieren oder den Support zu
kontaktieren, um zu erfahren, auf welche Funktionen sie zugreifen können.

**Optimiertes Onboarding**: Neue Benutzer sehen nur die Funktionen, die für ihre Rolle relevant sind, was die anfängliche
Plattformorientierung dramatisch vereinfacht. Schulungen können sich auf relevante Funktionen konzentrieren, anstatt Benutzern
zu helfen, zu verstehen, worauf sie nicht zugreifen können und warum.

## Sicherheits- und Compliance-Vorteile

Die berechtigungsbewusste Architektur bietet Sicherheits- und Compliance-Vorteile, die über die Verbesserungen der
Benutzererfahrung hinausgehen.

**Defense in Depth**: Die clientseitige Filterung nicht autorisierter Services ergänzt die Backend-Berechtigungsdurchsetzung
und schafft mehrere Sicherheitsebenen. Selbst wenn ein Angreifer das Frontend manipuliert, verhindert die Backend-Autorisierungsdurchsetzung
unautorisierte Operationen.

**Reduzierte Angriffsfläche**: Indem keine Informationen über Services preisgegeben werden, auf die Benutzer keinen Zugriff
haben, gibt die Suite potenziellen Angreifern weniger Informationen über die Fähigkeiten der Bereitstellung. Benutzer können
deaktivierte Funktionen nicht ausspionieren, um Informationen für Angriffe zu sammeln.

**Compliance-Unterstützung**: Die umfassende Audit-Protokollierung von Berechtigungsauswertungen unterstützt die Einhaltung
regulatorischer Anforderungen für die Zugriffssteuerung, insbesondere in Sektoren mit strengen Datenschutzanforderungen
wie Gesundheitswesen, Finanzen und öffentliche Verwaltung.

**Zero-Trust-Architektur**: Die Suite implementiert Zero-Trust-Prinzipien, bei denen jeder Servicezugriff eine explizite
Berechtigungsauswertung erfordert. Es gibt keine impliziten Vertrauensannahmen basierend auf Netzwerkstandort oder
vorheriger Authentifizierung – jede Operation wird unabhängig autorisiert.

## Operationelle Vorteile

Neben Sicherheit und Benutzererfahrung bietet das Berechtigungssystem auch operationelle Vorteile für Plattformadministratoren.

**Zentrale Berechtigungsverwaltung**: Administratoren verwalten Berechtigungen über den Rollenverwaltungsdienst, wobei
Änderungen automatisch in der gesamten Suite widergespiegelt werden. Es ist nicht notwendig, Zugriffssteuerungen separat
für jeden Service zu konfigurieren oder Berechtigungen über mehrere Systeme hinweg zu koordinieren.

**Flexible Delegation**: Das hierarchische Berechtigungssystem ermöglicht ausgeklügelte Delegationsmuster. Leitenden
Mitarbeitern können breite Zugriffsmuster wie `aihub.user.agent.>` gewährt werden, während Junior-Mitarbeiter spezifische
Zuteilungen für einzelne Ressourcen erhalten. Diese Flexibilität unterstützt Organisationsstrukturen, ohne komplexe
Zugriffssteuerungskonfigurationen zu erfordern.

**Berechtigungsvererbung**: Die hierarchische Struktur ermöglicht die Berechtigungsvererbung, wobei die Gewährung von
Zugriff auf eine übergeordnete Ressource automatisch Zugriff auf enthaltene Ressourcen bietet. Dies vereinfacht die
Berechtigungsverwaltung, während bei Bedarf eine präzise Kontrolle beibehalten wird.

**Rollenbasierte Administration**: Anstatt individuelle Benutzerberechtigungen zu verwalten, weisen Administratoren
Benutzer typischerweise Rollen zu, die Standardberechtigungssätze definieren. Rollenänderungen gelten automatisch für
alle zugewiesenen Benutzer und gewährleisten eine konsistente Zugriffssteuerung über alle Benutzerpopulationen hinweg.

Diese berechtigungsbewusste Architektur stellt sicher, dass die Swiss AI Hub Suite jedem Benutzer eine fokussierte,
sichere Oberfläche bietet, die präzise auf dessen Autorisierungslevel und organisatorische Rolle zugeschnitten ist,
während die operationelle Einfachheit und die Sicherheitsstrenge, die für Unternehmens- und öffentliche Sektor-Bereitstellungen
erforderlich sind, beibehalten werden.

# Rollenbasierte Zugriffssteuerung (RBAC) :shield: :lock:

::: info **Aktualisierung der Dokumentationsstruktur**
Die RBAC-Dokumentation wurde neu organisiert, um verschiedenen Zielgruppen besser zu dienen. Diese Seite bietet
schnellen Zugriff auf die für Ihre Bedürfnisse geeignete Dokumentation.
:::

## Schnellnavigation

### Für Entwickler und SDK-Benutzer

Wenn Sie RBAC in Ihren benutzerdefinierten Agenten, APIs oder Services implementieren und technische
Implementierungsdetails benötigen:

::: tip **SDK-Dokumentation**
🛠️ **[Vollständiger SDK RBAC Implementierungsleitfaden](../../../3_sdk/5_advanced_topics/5_rbac/)**

Behandelt:

- Zugriffs-schutz auf Controller-Ebene
- Dynamische Berechtigungsauflösung
- Implementierung der Zugriffssteuerung für Services und Agenten
- Erweiterte Berechtigungsmuster und Platzhalter
- Benutzerdefinierte Validierungslogik
- Testen von RBAC-Implementierungen
- Performance-Optimierung und Best Practices
:::

## Kurzübersicht

**Rollenbasierte Zugriffssteuerung (RBAC)** ist ein Sicherheitsframework, das den Systemzugriff basierend auf Benutzerrollen
innerhalb einer Organisation einschränkt. Der AI-Hub implementiert ein ausgeklügeltes, hierarchisches RBAC-System, das
eine granulare Kontrolle über jeden Aspekt Ihrer AI-Plattform bietet.

### Hauptvorteile

**🛡️ Enterprise Security Compliance**: Erfüllen Sie strenge regulatorische Anforderungen mit umfassenden Audit-Trails
und granularer Zugriffssteuerung.

**🎯 Granulare Ressourcenkontrolle**: Steuern Sie den Zugriff auf spezifische AI-Agenten, Prozesse und Services präzise.

**⚡ Skalierbares Berechtigungsmanagement**: Verwalten Sie Berechtigungen effizient in großen Organisationen mithilfe
rollenbasierter Hierarchien.

**🔗 Nahtlose Unternehmensintegration**: Native Integration mit bestehenden Unternehmensidentitätssystemen.

**🧠 Risikobewusste AI-Bereitstellung**: Setzen Sie AI-Funktionen mit Vertrauen ein, da der Zugriff kontrolliert und
überwacht wird.

### Kernkomponenten

- **Rollen**: Benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer tun können
- **Zugriffsregeln**: Spezifische Berechtigungen unter Verwendung der Punktnotation (z. B. `aihub.admin.service.roles`)
- **Benutzeridentität**: Integration mit Unternehmensauthentifizierungssystemen (Azure AD, OAuth2)
- **Berechtigungsvorlagen**: Dynamische Berechtigungsprüfung mit Pfadparameter-Substitution
- **Platzhalterunterstützung**: Flexible Mustererkennung mit `*`, `>`, `?*` und `?>` Platzhaltern

### Berechtigungsstruktur

Das System verwendet eine strukturierte Namenskonvention für Berechtigungen:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**

- `aihub.user.agent.customer_service.chatbot_v2` - Benutzerzugriff auf spezifischen Agenten
- `aihub.admin.service.roles` - Administratorzugriff auf die Rollenverwaltung
- `aihub.user.agent.?>` - Benutzerzugriff auf beliebigen Agenten (Platzhalter)

## Wählen Sie Ihren Pfad

- **Entwickler & Integratoren**: Beginnen Sie mit dem
  [SDK Implementierungsleitfaden](../../../3_sdk/5_advanced_topics/5_rbac/)

Beide Leitfäden bieten eine umfassende Abdeckung des AI-Hub RBAC-Systems, zugeschnitten auf Ihre spezifischen Bedürfnisse
und Anwendungsfälle.
