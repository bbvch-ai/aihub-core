---
title: Überlegungen zur Skalierung
index: 3
source_sha: "84868b217fe9843cc8efae2dcb0cd9d26206c70d5f6710afac6d8b2af6f53012"
---

# Skalierbarkeit

Der Swiss AI-Hub implementiert Skalierbarkeit als zentrales Architekturprinzip, das es Organisationen ermöglicht, ihre
KI-Fähigkeiten von Pilotprojekten zu unternehmensweiten Implementierungen zu erweitern, ohne grundlegende
Architekturänderungen vornehmen zu müssen. Das Design der Plattform stellt sicher, dass die Skalierung der Kapazität
lediglich betriebliche Anpassungen – das Bereitstellen zusätzlicher Instanzen – erfordert und keine Code-Änderungen
oder architektonische Neugestaltungen.

## Horizontale Skalierbarkeit durch ereignisgesteuerte Architektur

Die ereignisgesteuerte Architektur ermöglicht horizontale Skalierbarkeit und Systemresilienz:

**Zustandsloser Agenten-Code**: Die Agenten-Logik enthält keinen veränderlichen Zustand, wodurch jede Instanz jedes
Ereignis verarbeiten kann. Dieses zustandslose Design eliminiert den Koordinationsaufwand, der typischerweise in
verteilten Systemen erforderlich ist, und ermöglicht es neuen Instanzen, sofort nach der Bereitstellung mit der
Verarbeitung zu beginnen, ohne Synchronisation oder Zustandsübertragung.

**Lastverteilung**: Ereignisse werden zur parallelen Verarbeitung auf mehrere Agenten-Instanzen verteilt. Die
Messaging-Infrastruktur gleicht die Arbeit automatisch über die verfügbaren Instanzen aus und sorgt so für eine
optimale Ressourcennutzung, ohne dass eine manuelle Lastverteilung konfiguriert werden muss. Organisationen können
die Kapazität einfach durch Ändern der Anzahl laufender Instanzen anpassen.

**Fehlerbehebung**: Fehlgeschlagene Operationen werden ohne Zustandsverlust durch Ereigniswiederholung erneut
versucht. Wenn eine Agenten-Instanz während der Verarbeitung ausfällt, kann eine andere Instanz die Arbeit sofort
wieder aufnehmen, indem sie den Ereignisverlauf wiederholt. Dieses Resilienzmodell stellt sicher, dass keine Arbeit
verloren geht und keine manuelle Intervention zur Wiederherstellung erforderlich ist.

**Systementwicklung**: Neue Ereignistypen werden eingeführt, ohne bestehende Komponenten zu modifizieren. Die
automatische Registrierung von Ereignistypen und die Mechanismen zur sanften Degradation ermöglichen es der Plattform,
sich kontinuierlich weiterzuentwickeln. Organisationen können neue Funktionen inkrementell bereitstellen, wobei
verschiedene Versionen während Migrationsphasen gleichzeitig betrieben werden können.

## Operationelle Skalierung

Organisationen können die Agentenkapazität durch die Bereitstellung zusätzlicher Instanzen ohne architektonische
Änderungen skalieren. Die Plattform unterstützt mehrere Skalierungsdimensionen:

**Skalierung der Rechenleistung**: Stellen Sie zusätzliche Agenten-Instanzen bereit, um ein erhöhtes
Verarbeitungsvolumen zu bewältigen. Jede Instanz arbeitet unabhängig, verbraucht Ereignisse aus gemeinsamen Streams und
verarbeitet die Arbeit parallel mit anderen Instanzen.

**Geografische Verteilung**: Agenten-Instanzen können in verschiedenen geografischen Regionen betrieben werden, ohne
einen gemeinsamen Zustand zu erfordern. Die Messaging-Infrastruktur gewährleistet die Ereignisübermittlung unabhängig
vom physischen Standort und ermöglicht so globale Bereitstellungen, die die Latenz für verteilte Benutzergruppen
reduzieren.

**Inkrementelle Upgrades**: System-Upgrades werden inkrementell ohne Serviceunterbrechung bereitgestellt.
Organisationen können neue Agenten-Versionen parallel zu bestehenden Versionen bereitstellen und den Traffic
schrittweise auf aktualisierte Implementierungen umleiten, während die Möglichkeit erhalten bleibt, bei Problemen ein
Rollback durchzuführen.

### Horizontale Skalierbarkeit

Die ereignisgesteuerte Architektur ermöglicht eine mühelose Skalierung, um schwankendem Bedarf gerecht zu werden. Wenn
die Systemlast steigt, können zusätzliche Worker-Instanzen bereitgestellt werden, um Ereignisse aus denselben Streams
zu verarbeiten, ohne dass Änderungen am Anwendungscode oder an der Architektur erforderlich sind. Diese Worker
verteilen die Verarbeitungslast automatisch, indem sie Ereignisse parallel konsumieren.

Dieser Ansatz bietet mehrere operationelle Vorteile: Die Kapazität kann in Spitzenzeiten dynamisch erhöht und in
ruhigen Zeiten reduziert werden, die Systemleistung bleibt bei wachsender Arbeitslast konstant, und es entstehen keine
Engpässe durch zentralisierte Verarbeitung. Da die Ereignisverarbeitung zustandslos ist, arbeitet jeder Worker
unabhängig – wenn einer ausfällt, verarbeiten andere weiter, und der ausgefallene Worker kann neu gestartet werden,
ohne laufende Operationen zu beeinträchtigen.

Organisationen können spezifische Komponenten basierend auf tatsächlichen Nachfragemustern skalieren. Wenn die
Agenten-Ausführung mehr Kapazität erfordert, können zusätzliche Agenten-Worker bereitgestellt werden. Wenn die
Datenaufnahme zu einem Engpass wird, können weitere Pipeline-Worker hinzugefügt werden.
