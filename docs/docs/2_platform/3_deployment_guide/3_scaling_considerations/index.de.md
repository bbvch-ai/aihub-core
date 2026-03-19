---
title: Überlegungen zur Skalierung
source_sha: "a50d139722017db95769329c80beccfc761bdfec8e799a906f192d4a1ef528cc"
---

# Skalierbarkeit

Der Swiss AI Hub implementiert Skalierbarkeit als Kernarchitekturprinzip und ermöglicht es Organisationen, ihre KI-Fähigkeiten von Pilotprojekten bis hin zu unternehmensweiten Deployments ohne grundlegende architektonische Änderungen zu erweitern. Das Design der Plattform stellt sicher, dass die Skalierung der Kapazität lediglich operative Anpassungen – das Deployment zusätzlicher Instanzen – erfordert, anstatt Code-Modifikationen oder architektonische Neugestaltungen.

## Horizontale Skalierbarkeit durch ereignisgesteuerte Architektur

Die ereignisgesteuerte Architektur ermöglicht horizontale Skalierbarkeit und Systemresilienz:

**Zustandsloser Agent-Code**: Die Agent-Logik enthält keinen veränderlichen Zustand, wodurch jede Instanz jedes Ereignis verarbeiten kann. Dieses zustandslose Design eliminiert den Koordinationsaufwand, der typischerweise in verteilten Systemen erforderlich ist, und ermöglicht es neuen Instanzen, die Verarbeitung sofort nach dem Deployment zu beginnen, ohne Synchronisation oder Zustandsübertragung.

**Lastverteilung**: Ereignisse werden auf mehrere Agent-Instanzen zur parallelen Verarbeitung verteilt. Die Messaging-Infrastruktur verteilt die Arbeit automatisch auf die verfügbaren Instanzen und gewährleistet so eine optimale Ressourcenauslastung, ohne dass eine manuelle Lastverteilungskonfiguration erforderlich ist. Organisationen können die Kapazität anpassen, indem sie einfach die Anzahl der laufenden Instanzen ändern.

**Fehlerwiederherstellung**: Fehlgeschlagene Operationen werden durch Ereigniswiederholung ohne Zustandsverlust erneut versucht. Wenn eine Agent-Instanz während der Verarbeitung ausfällt, kann eine andere Instanz die Arbeit sofort wieder aufnehmen, indem sie den Ereignisverlauf wiederholt. Dieses Resilienzmodell stellt sicher, dass keine Arbeit verloren geht und keine manuelle Intervention zur Wiederherstellung erforderlich ist.

**Systementwicklung**: Neue Ereignistypen werden eingeführt, ohne bestehende Komponenten zu modifizieren. Die automatische Ereignistyp-Registrierung und die Mechanismen zur graceful Degradation ermöglichen es der Plattform, sich kontinuierlich weiterzuentwickeln. Organisationen können neue Funktionen inkrementell deployen, wobei verschiedene Versionen während Migrationsphasen gleichzeitig betrieben werden.

## Operative Skalierung

Organisationen können die Agent-Kapazität durch das Deployment zusätzlicher Instanzen ohne architektonische Änderungen skalieren. Die Plattform unterstützt mehrere Skalierungsdimensionen:

**Rechenskalierung**: Deployen Sie zusätzliche Agent-Instanzen, um ein erhöhtes Verarbeitungsvolumen zu bewältigen. Jede Instanz arbeitet unabhängig, konsumiert Ereignisse aus gemeinsam genutzten Streams und verarbeitet Aufgaben parallel zu anderen Instanzen.

**Geografische Verteilung**: Agent-Instanzen können in verschiedenen geografischen Regionen betrieben werden, ohne einen gemeinsamen Zustand zu erfordern. Die Messaging-Infrastruktur gewährleistet die Ereignisbereitstellung unabhängig vom physischen Standort und ermöglicht so globale Deployments, die die Latenz für verteilte Benutzerpopulationen reduzieren.

**Inkrementelle Upgrades**: System-Upgrades werden inkrementell ohne Serviceunterbrechung deployt. Organisationen können neue Agent-Versionen parallel zu bestehenden Versionen deployen, den Traffic schrittweise auf aktualisierte Implementierungen verlagern und gleichzeitig die Möglichkeit beibehalten, bei Problemen ein Rollback durchzuführen.

### Horizontale Skalierbarkeit

Die ereignisgesteuerte Architektur ermöglicht eine mühelose Skalierung, um schwankende Anforderungen zu erfüllen. Wenn die Systemlast steigt, können zusätzliche Worker-Instanzen deployt werden, um Ereignisse aus denselben Streams zu verarbeiten, ohne Änderungen am Anwendungscode oder an der Architektur vorzunehmen. Diese Worker verteilen die Verarbeitungslast automatisch, indem sie Ereignisse parallel konsumieren.

Dieser Ansatz bietet mehrere operative Vorteile: Die Kapazität kann in Spitzenzeiten dynamisch erhöht und in ruhigen Zeiten reduziert werden, die Systemleistung bleibt bei wachsender Arbeitslast konstant, und es gibt keine Engpässe durch zentralisierte Verarbeitung. Da die Ereignisverarbeitung zustandslos ist, arbeitet jeder Worker unabhängig – fällt einer aus, verarbeiten andere weiter, und der ausgefallene Worker kann neu gestartet werden, ohne laufende Operationen zu beeinträchtigen.

Organisationen können spezifische Komponenten basierend auf den tatsächlichen Nachfragemustern skalieren. Wenn die Agent-Ausführung mehr Kapazität erfordert, können zusätzliche Agent-Worker deployt werden. Wenn die Datenaufnahme zu einem Engpass wird, können weitere Pipeline-Worker hinzugefügt werden.
