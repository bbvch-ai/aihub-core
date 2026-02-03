---
title: Gedächtnis
source_sha: ebba0c0958f79f6092ae700a1a39bffe66d32c092eef19fc550f436b273828e4
---

# Agenten-Gedächtnis

KI-Agents benötigen Kontext, um relevante, personalisierte Unterstützung zu bieten. Ohne Gedächtnis beginnen Agents jede
Konversation von Neuem, wodurch Sie gezwungen sind, Ihre Präferenzen, Ihren Arbeitsstil und den organisatorischen
Kontext wiederholt zu erklären. Das Gedächtnissystem des Swiss AI Hub ermöglicht es Agents, Informationen über
Konversationen hinweg zu lernen und zu behalten.

## Warum Gedächtnis wichtig ist

Gedächtnis ermöglicht Fähigkeiten, die zustandslose Agents nicht bieten können. Ein Agent lernt, dass Sie prägnante
Codebeispiele in Python bevorzugen, und passt dann zukünftige Antworten automatisch an Ihren Arbeitsstil an. Wenn ein
Benutzer einen Agenten bezüglich einer Unternehmensrichtlinie korrigiert, kommt diese Korrektur allen zugute – alle
Agents arbeiten sofort mit den aktualisierten Informationen. Sie erklären Ihre Projektstruktur einmal, und die Agents
merken sich diese für alle zukünftigen Interaktionen. Informationen überdauern den Personalwechsel; wenn Teammitglieder
das Unternehmen verlassen, bleibt ihr dokumentiertes Wissen für Agents, die neue Mitarbeiter betreuen, zugänglich.

## Zwei Arten von Gedächtnis

Die Plattform verwendet zwei verschiedene Gedächtnistypen:

**Benutzergedächtnis** speichert persönliche Präferenzen und individuellen Kontext. Dieses Gedächtnis ist privat für
Sie. Wenn ein Agent lernt, dass Sie detaillierte Erklärungen bevorzugen oder hauptsächlich in einem bestimmten
Technologie-Stack arbeiten, bleiben diese Informationen allein Ihre.

**Organisationsgedächtnis** speichert geteiltes Wissen, das allen Benutzern innerhalb Ihrer Organisation zugänglich ist.
Unternehmensrichtlinien, Projektdetails, Teamkonventionen und faktische Informationen gehören hierher. Wenn ein Benutzer
dokumentiert, dass „Projekt Falcon eine Microservices-Architektur verwendet", können alle Agents dieses Wissen nutzen,
um jedes Teammitglied, das an diesem Projekt arbeitet, zu unterstützen.

Diese Struktur gleicht individuelle Personalisierung mit organisatorischer Konsistenz aus. Agents passen sich den
Präferenzen jedes Benutzers an, während sie ein gemeinsames Verständnis unternehmensweiter Fakten aufrechterhalten.

## Wie Gedächtnis funktioniert

### Automatisches Lernen

Das Benutzergedächtnis erfordert keinen manuellen Aufwand. Agents extrahieren automatisch relevante Informationen aus
Ihren Konversationen. Während Sie mit einem Code-Assistenten über Python-Projekte chatten, lernt dieser Ihre
Sprachpräferenz. Während Sie mit einem Prozess-Assistenten über Fristen diskutieren, lernt dieser Ihre
Genehmigungsmuster.

Jeder Agententyp lernt anders. Ein Code-Assistent konzentriert sich auf technische Präferenzen und Arbeitsstile. Ein
Wissensabruf-Agent lernt über Ihre Interessengebiete und bevorzugten Informationsformate.

### Explizite Dokumentation

Das Organisationsgedächtnis funktioniert anders. Da dieses Wissen alle Benutzer betrifft, erfordert die Plattform eine
explizite Dokumentation anstelle einer automatischen Inferenz. Sie wählen aus, welche Informationen als
organisatorisches Wissen erhalten bleiben sollen.

Dieses Design verhindert, dass sich Fehler in der gesamten Organisation ausbreiten. Ein Agent wird einen einmaligen
Kommentar nicht versehentlich in eine dauerhafte Unternehmensrichtlinie umwandeln.

### Transparenz

Die Plattform bietet vollständige Transparenz darüber, was Agents sich merken. Jedes Gedächtnis enthält den
Konversations-Thread, in dem es entstanden ist, den Agenten, der es erstellt hat, und den genauen Zeitstempel. Wenn ein
Agent ein Gedächtnis verwendet, um seine Antwort zu informieren, wird diese Nutzung protokolliert und ist in der
Konversationsspur sichtbar. Über das Swiss AI Agent Protocol werden alle Gedächtnisoperationen in das
Observability-System der Plattform integriert.

Sie können genau sehen, was Agents über Sie wissen, woher diese Informationen stammen und wann sie verwendet werden.

## Ihre Kontrolle über das Gedächtnis

### Verwalten des Benutzergedächtnisses

Sie haben die vollständige Kontrolle über Ihre persönlichen Gedächtnisinhalte. Greifen Sie auf den
Benutzergedächtnis-Service zu, um alles zu sehen, was Agents über Sie gelernt haben. Sie können jedes Gedächtnis
bearbeiten, um das, was Agents sich merken, zu korrigieren oder zu verfeinern, bestimmte Gedächtnisinhalte zu löschen
oder alle Benutzergedächtnisinhalte vollständig zu löschen.

Die Plattform respektiert Datensouveränität und DSGVO-Anforderungen. Sie können Ihr Recht auf Vergessenwerden ausüben,
indem Sie alle Benutzergedächtnisinhalte mit einer einzigen Aktion löschen.

### Verwalten des Organisationsgedächtnisses

Das Organisationsgedächtnis folgt einem ähnlichen Muster mit einem entscheidenden Unterschied: Änderungen betreffen alle
Benutzer. Wenn Sie ein Organisationsgedächtnis bearbeiten oder löschen, modifizieren Sie Wissen, auf das sich die Agents
anderer Teammitglieder verlassen.

Der Zugriff auf die Verwaltung des Organisationsgedächtnisses ist typischerweise auf Administratoren oder Wissensmanager
beschränkt, die die Auswirkungen ihrer Änderungen verstehen.

## Erste Schritte

Navigieren Sie zum **Benutzergedächtnis**-Service in der Plattform-Benutzeroberfläche. Sie sehen alle Informationen, die
Agents über Ihre Präferenzen und Ihren Arbeitsstil gelernt haben. Jedes Gedächtnis zeigt die gespeicherten
Informationen, wann sie gelernt wurden, welcher Agent sie erstellt hat und den Konversations-Thread, in dem sie
entstanden sind. Versuchen Sie, ein Gedächtnis zu bearbeiten, um zu sehen, wie Agents sich an Ihre Korrekturen anpassen.

Greifen Sie auf den **Organisationsgedächtnis**-Service zu, um das gemeinsame Wissen Ihrer Organisation einzusehen –
Unternehmensrichtlinien, Projektinformationen und Teamkonventionen, die alle Agents verwenden. Wenn Sie über die
entsprechenden Berechtigungen verfügen, können Sie neues organisatorisches Wissen beisteuern oder bestehende
Informationen aktualisieren.

Beobachten Sie während Gesprächen mit Agents die Anzeigeereignisse, um zu sehen, wann Agents Gedächtnisinhalte abrufen
und verwenden. Diese Transparenz zeigt Ihnen genau, wie das Gedächtnis die Agenten-Antworten beeinflusst.

## Datenschutz und Datensouveränität

Das Gedächtnissystem hält sich an die Schweizer Prinzipien der Datensouveränität. Ihre persönlichen Gedächtnisinhalte
sind niemals für andere Benutzer sichtbar. Organisationsgedächtnisinhalte sind auf Ihren Mandanten beschränkt, wodurch
Informationslecks zwischen verschiedenen Organisationen, die die Plattform nutzen, verhindert werden. Große
Organisationen können Organisationsgedächtnisinhalte zusätzlich nach Abteilung oder Team isolieren.

Beide Gedächtnistypen unterstützen vollständige CRUD-Operationen (Erstellen, Lesen, Aktualisieren, Löschen) und
gewährleisten so die Einhaltung der Datenschutzbestimmungen. Alle Gedächtnisdaten verbleiben auf Schweizer Infrastruktur
mit den gleichen Datenschutzgarantien wie der Rest der Plattform.
