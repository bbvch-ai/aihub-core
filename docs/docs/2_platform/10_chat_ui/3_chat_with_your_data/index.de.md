---
title: Chatten mit Ihren Daten
source_sha: 19540ad4b8ad3989ef6ce4619a75899810f8b4dd3ae04b923c200e5faa5b5512
---

Um Dateien hochzuladen, klicken Sie auf den „Mehr“-Button.

![Click More Button](../../../../media/open_webui/click_more_button.jpeg)

Wählen Sie dann „Dateien hochladen“. Navigieren Sie im Pop-up-Fenster zu den Dateien, die Sie verwenden möchten, und
laden Sie diese hoch.

![Select Upload Files](../../../../media/open_webui/select_upload_files.jpeg)

Nachdem Sie die Dateien hochgeladen haben, stellen Sie eine Frage.

![Ask Question with Files](../../../../media/open_webui/ask_question_with_files.jpeg)

Das Modell wird die Dateien verwenden, um die Frage zu beantworten.

![Answer Using Files](../../../../media/open_webui/answer_using_files.jpeg)

Klicken Sie auf eine Referenz, um zu sehen, welche Teile zur Beantwortung der Frage verwendet wurden.

![Click Reference Citation](../../../../media/open_webui/click_reference_citation.jpeg)

Die Zitation bietet eine klare Übersicht über die verschiedenen Teile, die zur Generierung der Antwort verwendet wurden.

![Citation Details](../../../../media/open_webui/citation_details_displayed.jpeg)

## Dateien an einen Agenten anhängen

Auch Agenten lesen angehängte Dateien, und zwar über mehrere Gesprächsrunden hinweg: Hängen Sie später eine
zweite Datei an, antwortet der Agent aus dieser, während die frühere für Fragen verfügbar bleibt, die sie
erfordern. Wie viele Dateien ein Chat annimmt, legt Ihre Administration fest; der Standardwert ist vier.

Ein Agent durchsucht jeden Anhang, statt ihn vollständig zu lesen. Deshalb nennt er die Anhänge, die er nicht
lesen konnte — eine Datei, deren Indexierung noch läuft, oder eine, die nicht verarbeitet werden konnte —
anstatt zu antworten, als wäre sie nie gesendet worden.

Eine im Chat angehängte Wissenssammlung wird von einem Agenten **nicht** gelesen. Agenten antworten aus den
Wissensdatenbanken, die in ihrem eigenen Profil konfiguriert sind; hängen Sie eine im Chat an, weist der Agent
darauf hin, statt sie stillschweigend zu ignorieren.
