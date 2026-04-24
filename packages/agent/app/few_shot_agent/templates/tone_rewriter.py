from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.few_shot_agent import FewShotAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step import FewShotStepConfig


def build() -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="tone-rewriter",
        name=LocaleString(
            en="Professional Tone Rewriter",
            de="Professioneller Ton-Umschreiber",
            fr="Réécrivain de ton professionnel",
            it="Riscrittore di tono professionale",
        ),
        description=LocaleString(
            en="Rewrites text into a professional, clear, and diplomatic tone while preserving the message.",
            de="Schreibt Text in einen professionellen, klaren und diplomatischen Ton um.",
            fr="Réécrit le texte dans un ton professionnel, clair et diplomatique.",
            it="Riscrive il testo in un tono professionale, chiaro e diplomatico.",
        ),
        icon="mage:edit",
        number_of_input_tokens=50000,
        llm=LLMConfig(
            model_name="text-generation/gpt-oss-120b",
            default_parameter=LLMParameter(temperature=0.3, timeout=60.0),
        ),
        few_shot=FewShotStepConfig(
            system_prompt=LocaleString(
                en=(
                    "You are a professional writing coach. Rewrite the user's text to be:\n"
                    "- Professional and diplomatic in tone\n"
                    "- Clear and concise without losing meaning\n"
                    "- Free of emotional language, passive aggression, or ambiguity\n\n"
                    "Return only the rewritten text. Preserve the original language. "
                    "Do not add explanations unless the user asks."
                ),
                de=(
                    "Du bist ein professioneller Schreibcoach. Schreibe den Text des Benutzers um:\n"
                    "- Professioneller und diplomatischer Ton\n"
                    "- Klar und prägnant ohne Bedeutungsverlust\n"
                    "- Frei von emotionaler Sprache oder Mehrdeutigkeit\n\n"
                    "Gib nur den umgeschriebenen Text zurück. Behalte die Originalsprache bei."
                ),
                fr=(
                    "Vous êtes un coach en rédaction professionnelle. Réécrivez le texte :\n"
                    "- Ton professionnel et diplomatique\n"
                    "- Clair et concis sans perdre le sens\n"
                    "- Sans langage émotionnel ni ambiguïté\n\n"
                    "Retournez uniquement le texte réécrit. Conservez la langue originale."
                ),
                it=(
                    "Sei un coach di scrittura professionale. Riscrivi il testo:\n"
                    "- Tono professionale e diplomatico\n"
                    "- Chiaro e conciso senza perdere significato\n"
                    "- Senza linguaggio emotivo o ambiguità\n\n"
                    "Restituisci solo il testo riscritto. Mantieni la lingua originale."
                ),
            ),
            few_shot_examples=[
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "I already told you THREE times that the deadline is Friday. "
                            "Why hasn't anyone started working on this yet?? This is completely unacceptable."
                        ),
                        de=(
                            "Ich habe DREI Mal gesagt, dass die Deadline am Freitag ist. "
                            "Warum hat noch niemand damit angefangen?? Das ist völlig inakzeptabel."
                        ),
                        fr=(
                            "Je vous ai DÉJÀ dit TROIS fois que la deadline est vendredi. "
                            "Pourquoi personne n'a commencé ?? C'est complètement inacceptable."
                        ),
                        it=(
                            "Vi ho GIÀ detto TRE volte che la scadenza è venerdì. "
                            "Perché nessuno ha ancora iniziato?? Questo è completamente inaccettabile."
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            "I'd like to follow up on the Friday deadline for this project. "
                            "It appears that work hasn't started yet, and I want to make sure we're aligned. "
                            "Could we discuss what's needed to get this moving? I'm happy to help remove "
                            "any blockers."
                        ),
                        de=(
                            "Ich möchte an die Freitags-Deadline für dieses Projekt erinnern. "
                            "Es scheint, dass die Arbeit noch nicht begonnen hat. Können wir besprechen, "
                            "was benötigt wird? Ich helfe gerne, Hindernisse zu beseitigen."
                        ),
                        fr=(
                            "Je souhaite faire le point sur la deadline de vendredi. "
                            "Il semble que le travail n'a pas encore commencé. Pouvons-nous discuter "
                            "de ce qui est nécessaire ? Je suis disponible pour lever les blocages."
                        ),
                        it=(
                            "Vorrei fare il punto sulla scadenza di venerdì. "
                            "Sembra che il lavoro non sia ancora iniziato. Possiamo discutere "
                            "di cosa serve? Sono disponibile ad aiutare a rimuovere eventuali ostacoli."
                        ),
                    ),
                ),
                FewShotExample(
                    user=LocaleString(
                        en=(
                            "The new design looks really bad honestly. The colors are all wrong and "
                            "I don't think whoever made this even looked at the brand guidelines."
                        ),
                        de=(
                            "Das neue Design sieht ehrlich gesagt wirklich schlecht aus. Die Farben stimmen "
                            "überhaupt nicht und ich glaube nicht, dass sich jemand die Brand-Richtlinien "
                            "angeschaut hat."
                        ),
                        fr=(
                            "Le nouveau design est vraiment mauvais honnêtement. Les couleurs sont toutes fausses "
                            "et je ne pense pas que celui qui l'a fait ait regardé les directives de marque."
                        ),
                        it=(
                            "Il nuovo design è davvero brutto onestamente. I colori sono tutti sbagliati e "
                            "non credo che chi l'ha fatto abbia consultato le linee guida del brand."
                        ),
                    ),
                    agent=LocaleString(
                        en=(
                            "Thank you for sharing the new design. I have some feedback: the current color "
                            "palette doesn't fully align with our brand guidelines. Could we review the "
                            "guidelines together and adjust the palette? I think a few targeted changes would "
                            "make a big difference."
                        ),
                        de=(
                            "Danke für das neue Design. Ich habe einiges Feedback: Die aktuelle Farbpalette "
                            "stimmt nicht ganz mit unseren Brand-Richtlinien überein. Könnten wir die Richtlinien "
                            "gemeinsam durchgehen und die Palette anpassen? Einige gezielte Änderungen würden "
                            "einen grossen Unterschied machen."
                        ),
                        fr=(
                            "Merci pour le nouveau design. J'ai quelques retours : la palette de couleurs "
                            "ne correspond pas entièrement à nos directives de marque. Pourrions-nous revoir "
                            "les directives ensemble ? Quelques ajustements ciblés feraient une grande différence."
                        ),
                        it=(
                            "Grazie per il nuovo design. Ho alcuni feedback: la palette di colori attuale "
                            "non è del tutto allineata con le nostre linee guida del brand. Potremmo rivederle "
                            "insieme? Alcune modifiche mirate farebbero una grande differenza."
                        ),
                    ),
                ),
            ],
        ),
    )
