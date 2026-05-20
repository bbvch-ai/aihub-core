from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.few_shot_agent import FewShotAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step import FewShotStepConfig


def build() -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="structured-data-extractor",
        name=LocaleString(
            en="Structured Data Extractor",
            de="Strukturierter Datenextraktor",
            fr="Extracteur de données structurées",
            it="Estrattore di dati strutturati",
        ),
        description=LocaleString(
            en="Extracts structured JSON data from unstructured text like invoices, contracts, or reports.",
            de="Extrahiert strukturierte JSON-Daten aus unstrukturiertem Text wie Rechnungen oder Berichten.",
            fr="Extrait des données JSON structurées de texte non structuré comme des factures ou rapports.",
            it="Estrae dati JSON strutturati da testo non strutturato come fatture o report.",
        ),
        icon="mage:box-3d",
        number_of_input_tokens=100000,
        llm=LLMConfig(
            model_name="text-generation/gemma-4-31B-it",
            default_parameter=LLMParameter(temperature=0.0, timeout=60.0),
        ),
        few_shot=FewShotStepConfig(
            system_prompt=LocaleString(
                en=(
                    "You are a data extraction specialist. Extract structured information from the provided text "
                    "and return it as clean JSON.\n\n"
                    "Rules:\n"
                    "- Return ONLY valid JSON — no markdown fences, no explanation before or after\n"
                    "- Use null for missing fields, never guess or fabricate data\n"
                    "- Normalize dates to ISO 8601 format (YYYY-MM-DD)\n"
                    "- Normalize monetary amounts to numbers with currency code\n"
                    "- If the document type is unclear, infer the most likely schema from the content"
                ),
                de=(
                    "Du bist ein Datenextraktionsspezialist. Extrahiere strukturierte Informationen aus dem "
                    "bereitgestellten Text und gib sie als sauberes JSON zurück.\n\n"
                    "Regeln:\n"
                    "- NUR gültiges JSON zurückgeben — keine Markdown-Blöcke, keine Erklärungen\n"
                    "- null für fehlende Felder verwenden, niemals Daten erfinden\n"
                    "- Daten im ISO 8601-Format normalisieren (JJJJ-MM-TT)\n"
                    "- Geldbeträge als Zahlen mit Währungscode normalisieren"
                ),
                fr=(
                    "Vous êtes un spécialiste de l'extraction de données. Extrayez les informations structurées "
                    "et retournez du JSON valide.\n\n"
                    "Règles :\n"
                    "- Retourner UNIQUEMENT du JSON valide\n"
                    "- Utiliser null pour les champs manquants\n"
                    "- Normaliser les dates en ISO 8601 (AAAA-MM-JJ)\n"
                    "- Normaliser les montants avec code devise"
                ),
                it=(
                    "Sei un esperto di estrazione dati. Estrai informazioni strutturate dal testo fornito "
                    "e restituisci JSON valido.\n\n"
                    "Regole:\n"
                    "- Restituire SOLO JSON valido\n"
                    "- Usare null per i campi mancanti\n"
                    "- Normalizzare le date in ISO 8601 (AAAA-MM-GG)\n"
                    "- Normalizzare gli importi con codice valuta"
                ),
            ),
            few_shot_examples=[
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "Invoice #2024-1587\nDate: March 15, 2024\nFrom: Acme Solutions AG, Zurich\n"
                            "To: TechCorp GmbH, Bern\n\n"
                            "Consulting Services (Feb 2024): 40 hours @ CHF 200/hr = CHF 8,000.00\n"
                            "Cloud Infrastructure Setup: CHF 3,500.00\n"
                            "Subtotal: CHF 11,500.00\nVAT (8.1%): CHF 931.50\n"
                            "Total: CHF 12,431.50\nPayment due: April 14, 2024"
                        ),
                        de=(
                            "Rechnung #2024-1587\nDatum: 15. März 2024\nVon: Acme Solutions AG, Zürich\n"
                            "An: TechCorp GmbH, Bern\n\n"
                            "Beratungsleistungen (Feb 2024): 40 Stunden à CHF 200/Std = CHF 8'000.00\n"
                            "Cloud-Infrastruktur-Setup: CHF 3'500.00\n"
                            "Zwischensumme: CHF 11'500.00\nMWSt (8.1%): CHF 931.50\n"
                            "Total: CHF 12'431.50\nZahlungsfrist: 14. April 2024"
                        ),
                        fr=(
                            "Facture #2024-1587\nDate : 15 mars 2024\nDe : Acme Solutions AG, Zurich\n"
                            "À : TechCorp GmbH, Berne\n\n"
                            "Services de conseil (fév 2024) : 40h à CHF 200/h = CHF 8'000.00\n"
                            "Installation infrastructure cloud : CHF 3'500.00\n"
                            "Sous-total : CHF 11'500.00\nTVA (8.1%) : CHF 931.50\n"
                            "Total : CHF 12'431.50\nÉchéance : 14 avril 2024"
                        ),
                        it=(
                            "Fattura #2024-1587\nData: 15 marzo 2024\nDa: Acme Solutions AG, Zurigo\n"
                            "A: TechCorp GmbH, Berna\n\n"
                            "Servizi di consulenza (feb 2024): 40 ore a CHF 200/ora = CHF 8'000.00\n"
                            "Setup infrastruttura cloud: CHF 3'500.00\n"
                            "Subtotale: CHF 11'500.00\nIVA (8.1%): CHF 931.50\n"
                            "Totale: CHF 12'431.50\nScadenza: 14 aprile 2024"
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            '{"document_type": "invoice", "invoice_number": "2024-1587", '
                            '"date": "2024-03-15", "vendor": {"name": "Acme Solutions AG", "city": "Zurich"}, '
                            '"client": {"name": "TechCorp GmbH", "city": "Bern"}, '
                            '"line_items": ['
                            '{"description": "Consulting Services (Feb 2024)", "quantity": 40, '
                            '"unit": "hours", "unit_price": 200.00, "amount": 8000.00, "currency": "CHF"}, '
                            '{"description": "Cloud Infrastructure Setup", "quantity": 1, '
                            '"unit": "fixed", "unit_price": 3500.00, "amount": 3500.00, "currency": "CHF"}], '
                            '"subtotal": 11500.00, "vat_rate": 8.1, "vat_amount": 931.50, '
                            '"total": 12431.50, "currency": "CHF", "payment_due": "2024-04-14"}'
                        ),
                        de=(
                            '{"document_type": "invoice", "invoice_number": "2024-1587", '
                            '"date": "2024-03-15", "vendor": {"name": "Acme Solutions AG", "city": "Zurich"}, '
                            '"client": {"name": "TechCorp GmbH", "city": "Bern"}, '
                            '"line_items": ['
                            '{"description": "Beratungsleistungen (Feb 2024)", "quantity": 40, '
                            '"unit": "hours", "unit_price": 200.00, "amount": 8000.00, "currency": "CHF"}, '
                            '{"description": "Cloud-Infrastruktur-Setup", "quantity": 1, '
                            '"unit": "fixed", "unit_price": 3500.00, "amount": 3500.00, "currency": "CHF"}], '
                            '"subtotal": 11500.00, "vat_rate": 8.1, "vat_amount": 931.50, '
                            '"total": 12431.50, "currency": "CHF", "payment_due": "2024-04-14"}'
                        ),
                        fr=(
                            '{"document_type": "invoice", "invoice_number": "2024-1587", '
                            '"date": "2024-03-15", "vendor": {"name": "Acme Solutions AG", "city": "Zurich"}, '
                            '"client": {"name": "TechCorp GmbH", "city": "Berne"}, '
                            '"line_items": ['
                            '{"description": "Services de conseil (fév 2024)", "quantity": 40, '
                            '"unit": "hours", "unit_price": 200.00, "amount": 8000.00, "currency": "CHF"}, '
                            '{"description": "Installation infrastructure cloud", "quantity": 1, '
                            '"unit": "fixed", "unit_price": 3500.00, "amount": 3500.00, "currency": "CHF"}], '
                            '"subtotal": 11500.00, "vat_rate": 8.1, "vat_amount": 931.50, '
                            '"total": 12431.50, "currency": "CHF", "payment_due": "2024-04-14"}'
                        ),
                        it=(
                            '{"document_type": "invoice", "invoice_number": "2024-1587", '
                            '"date": "2024-03-15", "vendor": {"name": "Acme Solutions AG", "city": "Zurigo"}, '
                            '"client": {"name": "TechCorp GmbH", "city": "Berna"}, '
                            '"line_items": ['
                            '{"description": "Servizi di consulenza (feb 2024)", "quantity": 40, '
                            '"unit": "hours", "unit_price": 200.00, "amount": 8000.00, "currency": "CHF"}, '
                            '{"description": "Setup infrastruttura cloud", "quantity": 1, '
                            '"unit": "fixed", "unit_price": 3500.00, "amount": 3500.00, "currency": "CHF"}], '
                            '"subtotal": 11500.00, "vat_rate": 8.1, "vat_amount": 931.50, '
                            '"total": 12431.50, "currency": "CHF", "payment_due": "2024-04-14"}'
                        ),
                    ),
                ),
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "Meeting with Sarah Chen and Marc Dubois on Jan 8, 2025 at 14:00 in Room 4B.\n"
                            "Topic: Q1 Budget Review. Decision: Increase marketing budget by 15% to CHF 230k.\n"
                            "Action: Marc to prepare revised budget by Jan 20. Sarah to inform stakeholders."
                        ),
                        de=(
                            "Besprechung mit Sarah Chen und Marc Dubois am 8. Jan 2025 um 14:00 in Raum 4B.\n"
                            "Thema: Q1 Budget-Review. Entscheidung: Marketing-Budget um 15% auf CHF 230k erhöhen.\n"
                            "Massnahme: Marc erstellt bis 20. Jan überarbeitetes Budget. Sarah informiert Stakeholder."
                        ),
                        fr=(
                            "Réunion avec Sarah Chen et Marc Dubois le 8 janv. 2025 à 14h00, Salle 4B.\n"
                            "Sujet : Revue budget T1. Décision : Augmenter le budget marketing de 15% à CHF 230k.\n"
                            "Action : Marc prépare le budget révisé avant le 20 janv. Sarah informe les parties."
                        ),
                        it=(
                            "Riunione con Sarah Chen e Marc Dubois l'8 gen 2025 alle 14:00, Sala 4B.\n"
                            "Tema: Revisione budget Q1. Decisione: Aumentare budget marketing del 15% a CHF 230k.\n"
                            "Azione: Marc prepara il budget rivisto entro il 20 gen. Sarah informa gli stakeholder."
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            '{"document_type": "meeting_notes", "date": "2025-01-08", "time": "14:00", '
                            '"location": "Room 4B", '
                            '"participants": ["Sarah Chen", "Marc Dubois"], '
                            '"topic": "Q1 Budget Review", '
                            '"decisions": [{"description": "Increase marketing budget by 15%", '
                            '"new_value": 230000, "currency": "CHF"}], '
                            '"action_items": ['
                            '{"assignee": "Marc Dubois", "task": "Prepare revised budget", '
                            '"due_date": "2025-01-20"}, '
                            '{"assignee": "Sarah Chen", "task": "Inform stakeholders", '
                            '"due_date": null}]}'
                        ),
                        de=(
                            '{"document_type": "meeting_notes", "date": "2025-01-08", "time": "14:00", '
                            '"location": "Raum 4B", '
                            '"participants": ["Sarah Chen", "Marc Dubois"], '
                            '"topic": "Q1 Budget-Review", '
                            '"decisions": [{"description": "Marketing-Budget um 15% erhöhen", '
                            '"new_value": 230000, "currency": "CHF"}], '
                            '"action_items": ['
                            '{"assignee": "Marc Dubois", "task": "Überarbeitetes Budget erstellen", '
                            '"due_date": "2025-01-20"}, '
                            '{"assignee": "Sarah Chen", "task": "Stakeholder informieren", '
                            '"due_date": null}]}'
                        ),
                        fr=(
                            '{"document_type": "meeting_notes", "date": "2025-01-08", "time": "14:00", '
                            '"location": "Salle 4B", '
                            '"participants": ["Sarah Chen", "Marc Dubois"], '
                            '"topic": "Revue budget T1", '
                            '"decisions": [{"description": "Augmenter budget marketing de 15%", '
                            '"new_value": 230000, "currency": "CHF"}], '
                            '"action_items": ['
                            '{"assignee": "Marc Dubois", "task": "Préparer budget révisé", '
                            '"due_date": "2025-01-20"}, '
                            '{"assignee": "Sarah Chen", "task": "Informer les parties", '
                            '"due_date": null}]}'
                        ),
                        it=(
                            '{"document_type": "meeting_notes", "date": "2025-01-08", "time": "14:00", '
                            '"location": "Sala 4B", '
                            '"participants": ["Sarah Chen", "Marc Dubois"], '
                            '"topic": "Revisione budget Q1", '
                            '"decisions": [{"description": "Aumentare budget marketing del 15%", '
                            '"new_value": 230000, "currency": "CHF"}], '
                            '"action_items": ['
                            '{"assignee": "Marc Dubois", "task": "Preparare budget rivisto", '
                            '"due_date": "2025-01-20"}, '
                            '{"assignee": "Sarah Chen", "task": "Informare stakeholder", '
                            '"due_date": null}]}'
                        ),
                    ),
                ),
            ],
        ),
    )
