---
title: Speicher
source_sha: cbba80c898bf716f93707619acf6b9061d75567886b522705a041d307c1e2db9
---

# Agentenspeicher

KI-Agents benötigen Kontext, um relevante, personalisierte Unterstützung zu leisten. Ohne Speicher beginnen Agents jede
Konversation von Neuem, was Sie dazu zwingt, Ihre Präferenzen, Arbeitsweise und den organisatorischen Kontext wiederholt
zu erklären. Das Speichersystem des Swiss AI Hub ermöglicht es Agents, Informationen über Konversationen hinweg zu
lernen und zu behalten.

## Warum Speicher wichtig ist

Speicher ermöglicht Funktionen, die zustandslose Agents nicht bieten können. Ein Agent lernt, dass Sie prägnante
Codebeispiele in Python bevorzugen, und passt dann zukünftige Antworten automatisch an Ihren Arbeitsstil an. Wenn ein
Benutzer einen Agenten bezüglich einer Unternehmensrichtlinie korrigiert, kommt diese Korrektur allen zugute – alle
Agents arbeiten sofort mit den aktualisierten Informationen. Sie erklären Ihre Projektstruktur einmal, und die Agents
merken sie sich für alle zukünftigen Interaktionen. Informationen überleben Personalwechsel; wenn Teammitglieder das
Unternehmen verlassen, bleibt ihr dokumentiertes Wissen für Agents, die neue Mitarbeiter betreuen, zugänglich.

## Zwei Arten von Speicher

Die Plattform verwendet zwei verschiedene Speichertypen:

**Benutzerspeicher** speichert persönliche Präferenzen und individuellen Kontext. Dieser Speicher ist privat für Sie.
Wenn ein Agent lernt, dass Sie detaillierte Erklärungen bevorzugen oder hauptsächlich in einem bestimmten
Technologie-Stack arbeiten, bleiben diese Informationen nur Ihnen zugänglich.

**Organisationsspeicher** speichert geteiltes Wissen, das allen Benutzern innerhalb Ihrer Organisation zugänglich ist.
Unternehmensrichtlinien, Projektdetails, Teamkonventionen und sachliche Informationen gehören hierher. Wenn ein Benutzer
dokumentiert, dass "Projekt Falcon eine Microservices-Architektur verwendet", können alle Agents dieses Wissen nutzen,
um jedes Teammitglied zu unterstützen, das an diesem Projekt arbeitet.

Diese Struktur balanciert individuelle Personalisierung mit organisatorischer Konsistenz. Agents passen sich an die
Präferenzen jedes Benutzers an, während sie ein gemeinsames Verständnis der unternehmensweiten Fakten bewahren.

## Wie Speicher funktioniert

### Automatisches Lernen

Der Benutzerspeicher erfordert keinen manuellen Aufwand. Agents extrahieren automatisch relevante Informationen aus
Ihren Konversationen. Wenn Sie mit einem Code-Assistenten über Python-Projekte chatten, lernt dieser Ihre
Sprachpräferenz. Wenn Sie Termine mit einem Prozess-Assistenten besprechen, lernt dieser Ihre Freigabemuster.

Jeder Agententyp lernt anders. Ein Code-Assistent konzentriert sich auf technische Präferenzen und Arbeitsstile. Ein
Knowledge-Retrieval-Agent lernt Ihre Interessengebiete und bevorzugten Informationsformate.

### Explizite Dokumentation

Der Organisationsspeicher funktioniert anders. Da dieses Wissen alle Benutzer betrifft, erfordert die Plattform eine
explizite Dokumentation anstelle einer automatischen Inferenz. Sie wählen aus, welche Informationen als
Organisationswissen erhalten bleiben sollen.

Dieses Design verhindert, dass sich Fehler in der gesamten Organisation verbreiten. Ein Agent wird einen einmaligen
Kommentar nicht versehentlich in eine dauerhafte Unternehmensrichtlinie umwandeln.

### Transparenz

Die Plattform bietet volle Transparenz darüber, was Agents sich merken. Jeder Speicher enthält den Konversationsverlauf,
in dem er entstanden ist, den Agenten, der ihn erstellt hat, und den genauen Zeitstempel. Wenn ein Agent einen Speicher
verwendet, um seine Antwort zu informieren, wird diese Nutzung protokolliert und ist im Konversations-Trace sichtbar.
Durch das Swiss AI Agent Protocol integrieren sich alle Speicheroperationen in das Observability-System der Plattform.

Sie können genau sehen, was Agents über Sie wissen, woher diese Informationen stammen und wann sie verwendet werden.

## Ihre Kontrolle über den Speicher

### Benutzerspeicher verwalten

Sie haben die vollständige Kontrolle über Ihre persönlichen Speicher. Greifen Sie auf den Benutzerspeicher-Service zu,
um alles zu sehen, was Agents über Sie gelernt haben. Sie können jeden Speicher bearbeiten, um zu korrigieren oder zu
verfeinern, was Agents sich merken, bestimmte Speicher löschen oder alle Benutzerspeicher vollständig löschen.

Die Plattform respektiert Datensouveränität und DSGVO-Anforderungen. Sie können Ihr Recht auf Vergessenwerden ausüben,
indem Sie alle Benutzerspeicher mit einer einzigen Aktion löschen.

### Organisationsspeicher verwalten

Der Organisationsspeicher folgt einem ähnlichen Muster mit einem wichtigen Unterschied: Änderungen wirken sich auf alle
Benutzer aus. Wenn Sie einen Organisationsspeicher bearbeiten oder löschen, ändern Sie Wissen, auf das die Agents
anderer Teammitglieder angewiesen sind.

Der Zugriff auf die Verwaltung des Organisationsspeichers ist typischerweise auf Administratoren oder Knowledge Manager
beschränkt, die die Auswirkungen ihrer Änderungen verstehen.

## Erste Schritte

Navigieren Sie zum **Benutzerspeicher**-Service in der Plattform-Oberfläche. Sie sehen alle Informationen, die Agents
über Ihre Präferenzen und Ihren Arbeitsstil gelernt haben. Jeder Speicher zeigt die gemerkten Informationen, wann sie
gelernt wurden, welcher Agent sie erstellt hat und den Konversationsverlauf, in dem sie entstanden sind. Versuchen Sie,
einen Speicher zu bearbeiten, um zu sehen, wie sich Agents an Ihre Korrekturen anpassen.

Greifen Sie auf den **Organisationsspeicher**-Service zu, um das geteilte Wissen Ihrer Organisation einzusehen –
Unternehmensrichtlinien, Projektinformationen und Teamkonventionen, die alle Agents verwenden. Wenn Sie über
entsprechende Berechtigungen verfügen, können Sie neues Organisationswissen beisteuern oder bestehende Informationen
aktualisieren.

Während Konversationen mit Agents können Sie die Anzeigeereignisse beobachten, um zu sehen, wann Agents Speicher abrufen
und verwenden. Diese Transparenz zeigt Ihnen genau, wie der Speicher die Antworten der Agents beeinflusst.

## Datenschutz und Datensouveränität

Das Speichersystem hält sich an die Schweizer Prinzipien der Datensouveränität. Ihre persönlichen Speicher sind niemals
für andere Benutzer sichtbar. Organisationsspeicher sind auf Ihren Mandanten beschränkt, wodurch ein Informationsleck
zwischen verschiedenen Organisationen, die die Plattform nutzen, verhindert wird. Große Organisationen können
Organisationsspeicher nach Abteilung oder Team weiter isolieren.

Beide Speichertypen unterstützen vollständige CRUD-Operationen (Erstellen, Lesen, Aktualisieren, Löschen), wodurch die
Einhaltung der Datenschutzbestimmungen gewährleistet ist. Alle Speicherdaten verbleiben auf Schweizer Infrastruktur mit
den gleichen Datenschutzgarantien wie der Rest der Plattform.
