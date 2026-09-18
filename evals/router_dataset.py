"""Labeled cases for the THINK / NO_THINK router benchmark (see router_bench.py).

Labeling rubric — a case is THINK when answering it *well* needs the model to
actually work something out before replying: multi-step arithmetic, logic,
riddles or trick wording, planning under constraints, weighing trade-offs,
stepping through code. It is NO_THINK when a direct answer is fine: greetings,
simple recall, translations/rewrites/extraction, single-step arithmetic — and
anything whose real need is a *tool* (weather, search, reminders, memory)
rather than reasoning.

Deliberately multilingual: the router must not depend on the user's language,
so the same kinds of cases appear in Spanish, English, French, Portuguese,
Italian and German, including a few cross-lingual pairs of the same item.

Deliberately adversarial in both directions: lexically trivial questions that
hide a trap (the sheep riddle), and trivial questions dressed up with "think
carefully" or a long preamble. A router that keys on surface cues fails these.

Cases here must not appear as few-shot examples in the router prompt.
"""
from __future__ import annotations

THINK = "THINK"
NO_THINK = "NO_THINK"


def _case(text: str, label: str, lang: str, category: str) -> dict[str, str]:
    return {"text": text, "label": label, "lang": lang, "category": category}


CASES: list[dict[str, str]] = [
    # --- NO_THINK: chit-chat ---
    _case("Hola, ¿qué tal?", NO_THINK, "es", "chit-chat"),
    _case("¡Buenos días! ¿Cómo estás hoy?", NO_THINK, "es", "chit-chat"),
    _case("Hi! How's it going?", NO_THINK, "en", "chit-chat"),
    _case("Salut, ça va ?", NO_THINK, "fr", "chit-chat"),
    _case("Bom dia, tudo bem?", NO_THINK, "pt", "chit-chat"),
    _case("Ciao, come stai?", NO_THINK, "it", "chit-chat"),
    _case("Danke, das war sehr hilfreich!", NO_THINK, "de", "chit-chat"),
    _case("jajaja qué bueno", NO_THINK, "es", "chit-chat"),
    _case("Thanks a lot, you've been really helpful.", NO_THINK, "en", "chit-chat"),
    _case("Merci beaucoup !", NO_THINK, "fr", "chit-chat"),
    # --- NO_THINK: simple recall ---
    _case("¿Cuál es la capital de Portugal?", NO_THINK, "es", "recall"),
    _case("What year did the Berlin Wall fall?", NO_THINK, "en", "recall"),
    _case("Quelle est la capitale de l'Australie ?", NO_THINK, "fr", "recall"),
    _case("¿Quién escribió Cien años de soledad?", NO_THINK, "es", "recall"),
    _case("How many continents are there?", NO_THINK, "en", "recall"),
    _case("Qual é o maior oceano do mundo?", NO_THINK, "pt", "recall"),
    _case("Wie viele Tage hat ein Schaltjahr?", NO_THINK, "de", "recall"),
    _case("¿Cuántos gramos tiene un kilo?", NO_THINK, "es", "recall"),
    _case("Who painted the Mona Lisa?", NO_THINK, "en", "recall"),
    _case("Combien de côtés a un hexagone ?", NO_THINK, "fr", "recall"),
    _case("Was ist die Hauptstadt von Österreich?", NO_THINK, "de", "recall"),
    _case("Qual è la formula chimica dell'acqua?", NO_THINK, "it", "recall"),
    _case("¿Cuántas patas tiene una araña?", NO_THINK, "es", "recall"),
    _case("Lista los planetas del sistema solar en orden desde el Sol.", NO_THINK, "es", "recall"),
    _case("What's the plural of 'mouse'?", NO_THINK, "en", "recall"),
    # --- NO_THINK: needs a tool, not reasoning ---
    _case("¿Qué tiempo hace en Madrid ahora?", NO_THINK, "es", "tool"),
    _case("What's the weather like in Paris today?", NO_THINK, "en", "tool"),
    _case("Quel temps fait-il à Lyon en ce moment ?", NO_THINK, "fr", "tool"),
    _case("Recuérdame llamar al dentista en 20 minutos.", NO_THINK, "es", "tool"),
    _case("Remind me to take out the trash in an hour.", NO_THINK, "en", "tool"),
    _case("Recuerda que mi color favorito es el turquesa.", NO_THINK, "es", "tool"),
    _case("¿Qué recuerdas sobre mí?", NO_THINK, "es", "tool"),
    _case("Busca las últimas noticias sobre inteligencia artificial.", NO_THINK, "es", "tool"),
    _case("Cherche les dernières nouvelles sur la Ligue 1.", NO_THINK, "fr", "tool"),
    _case("What's the latest news about the Fed's interest rate decision?", NO_THINK, "en", "tool"),
    _case("Quel est le nom du président français actuel ?", NO_THINK, "fr", "tool"),
    # --- NO_THINK: transformation (translate / rewrite / extract / format) ---
    _case("Traduce al inglés: 'La reunión es mañana a las diez'.", NO_THINK, "es", "transform"),
    _case("Traduis en espagnol : « Je voudrais un café, s'il vous plaît ».", NO_THINK, "fr", "transform"),
    _case(
        "Extrae el CIF de este texto: 'Factura emitida por ACME S.L., CIF B12345678, con fecha 3 de marzo.'",
        NO_THINK,
        "es",
        "transform",
    ),
    _case("Rewrite this more formally: 'hey, can u send me the report asap?'", NO_THINK, "en", "transform"),
    _case("Corrige la ortografía: 'aber si mañana bamos al zine'.", NO_THINK, "es", "transform"),
    _case("Mets cette phrase au pluriel : « Le chat dort sur le canapé ».", NO_THINK, "fr", "transform"),
    _case("Convierte esta lista en JSON: manzana, pera, plátano.", NO_THINK, "es", "transform"),
    _case(
        "Summarize in one sentence: 'The meeting covered Q3 results, the new hiring plan, "
        "and the office move scheduled for November.'",
        NO_THINK,
        "en",
        "transform",
    ),
    _case("Pon en mayúsculas: buenos días a todos.", NO_THINK, "es", "transform"),
    _case("Dime un sinónimo de 'rápido'.", NO_THINK, "es", "transform"),
    _case("Give me a synonym for 'happy'.", NO_THINK, "en", "transform"),
    _case("Écris un message d'anniversaire court pour ma sœur.", NO_THINK, "fr", "transform"),
    _case("Escribe un tuit anunciando que abrimos nueva tienda en Sevilla.", NO_THINK, "es", "transform"),
    _case("Define 'fotosíntesis' en una frase.", NO_THINK, "es", "transform"),
    _case("Cuéntame un chiste corto.", NO_THINK, "es", "transform"),
    _case("¿Me recomiendas una película de ciencia ficción?", NO_THINK, "es", "transform"),
    # --- NO_THINK: single-step arithmetic ---
    _case("¿Cuánto es 15 + 27?", NO_THINK, "es", "trivial-math"),
    _case("What's 9 times 8?", NO_THINK, "en", "trivial-math"),
    _case("Combien font 100 divisé par 4 ?", NO_THINK, "fr", "trivial-math"),
    _case("¿Cuántos minutos hay en 3 horas?", NO_THINK, "es", "trivial-math"),
    _case("Convert 5 km to meters.", NO_THINK, "en", "trivial-math"),
    _case("¿Cuánto es el 10% de 250?", NO_THINK, "es", "trivial-math"),
    # --- NO_THINK: adversarial — long preamble or "think carefully", but trivial ---
    _case(
        "Oye, una pregunta que me lleva rondando la cabeza desde esta mañana mientras desayunaba "
        "y no consigo quitármela de encima: ¿en qué año llegó el ser humano a la Luna por primera vez?",
        NO_THINK,
        "es",
        "adversarial-trivial",
    ),
    _case(
        "I know this might sound like a silly question and I'm sorry to bother you with it, but I "
        "genuinely can't remember and it's driving me crazy — what is the chemical symbol for gold?",
        NO_THINK,
        "en",
        "adversarial-trivial",
    ),
    _case(
        "Alors voilà, c'est un peu bête mais je me demandais depuis tout à l'heure, sans vraiment "
        "savoir pourquoi : quelle est la langue officielle du Brésil ?",
        NO_THINK,
        "fr",
        "adversarial-trivial",
    ),
    _case("Dame un número aleatorio entre 1 y 100. Piénsalo bien.", NO_THINK, "es", "adversarial-trivial"),
    _case("Think carefully: what color is the sky on a clear day?", NO_THINK, "en", "adversarial-trivial"),
    _case("Réfléchis bien : quel est le contraire de « grand » ?", NO_THINK, "fr", "adversarial-trivial"),
    _case("Pensa bem: quantos dias tem uma semana?", NO_THINK, "pt", "adversarial-trivial"),
    # --- THINK: word problems with a trap in the wording ---
    _case(
        "Un granjero tiene 17 ovejas. Todas menos 9 se escapan. Luego compra el triple de las que "
        "le quedan. ¿Cuántas tiene ahora?",
        THINK,
        "es",
        "word-problem-trap",
    ),
    _case(
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
        "How much does the ball cost?",
        THINK,
        "en",
        "word-problem-trap",
    ),
    _case(
        "Si 5 máquinas tardan 5 minutos en hacer 5 piezas, ¿cuánto tardan 100 máquinas en hacer 100 piezas?",
        THINK,
        "es",
        "word-problem-trap",
    ),
    _case(
        "Un nénuphar double de taille chaque jour. S'il couvre tout l'étang en 48 jours, "
        "en combien de jours en couvre-t-il la moitié ?",
        THINK,
        "fr",
        "word-problem-trap",
    ),
    _case("¿Cuántos meses del año tienen 28 días?", THINK, "es", "word-problem-trap"),
    _case(
        "If you overtake the person in second place in a race, what place are you in?",
        THINK,
        "en",
        "word-problem-trap",
    ),
    _case(
        "El padre de María tiene cinco hijas: Nana, Nene, Nini y Nono. ¿Cómo se llama la quinta?",
        THINK,
        "es",
        "word-problem-trap",
    ),
    _case("Um tijolo pesa 1 kg mais meio tijolo. Quanto pesa um tijolo?", THINK, "pt", "word-problem-trap"),
    _case(
        "Ein Ziegelstein wiegt ein Kilo plus einen halben Ziegelstein. Wie schwer ist ein Ziegelstein?",
        THINK,
        "de",
        "word-problem-trap",
    ),
    _case(
        "Tengo 3 manzanas. Me como 2 y compro una docena más. Regalo la mitad de las que tengo. "
        "¿Cuántas me quedan?",
        THINK,
        "es",
        "word-problem-trap",
    ),
    _case(
        "Wenn drei Katzen drei Mäuse in drei Minuten fangen, wie viele Katzen braucht man, "
        "um 100 Mäuse in 100 Minuten zu fangen?",
        THINK,
        "de",
        "word-problem-trap",
    ),
    _case(
        "Trois amis paient une addition de 30 €, 10 € chacun. Le serveur rend 5 € ; ils gardent 1 € "
        "chacun et laissent 2 € de pourboire. 3 × 9 = 27, plus 2 de pourboire = 29. Où est passé l'euro manquant ?",
        THINK,
        "fr",
        "word-problem-trap",
    ),
    # --- THINK: logic ---
    _case(
        "Ana es más alta que Bea. Bea es más alta que Carla. Diego es más bajo que Carla pero más alto "
        "que Elena. ¿Quién es la segunda más baja?",
        THINK,
        "es",
        "logic",
    ),
    _case(
        "Three boxes are labeled 'apples', 'oranges' and 'mixed'. Every label is wrong. You may pick "
        "one fruit from one box. How do you relabel all three correctly?",
        THINK,
        "en",
        "logic",
    ),
    _case(
        "Tous les A sont des B. Aucun B n'est un C. Peut-on conclure qu'aucun A n'est un C ? Justifie.",
        THINK,
        "fr",
        "logic",
    ),
    _case("Si hoy es miércoles, ¿qué día de la semana será dentro de 100 días?", THINK, "es", "logic"),
    _case("Un reloj marca las 3:15. ¿Qué ángulo forman las manecillas?", THINK, "es", "logic"),
    _case(
        "Two fathers and two sons go fishing. Each catches one fish. They bring home three fish. "
        "How is that possible?",
        THINK,
        "en",
        "logic",
    ),
    _case(
        "En una fiesta cada persona saluda a todas las demás una vez. Si hubo 45 saludos, ¿cuántas personas había?",
        THINK,
        "es",
        "logic",
    ),
    _case(
        "Ho 12 monete, una è falsa e pesa meno. Con una bilancia a due piatti, qual è il numero minimo "
        "di pesate per trovarla? Spiega.",
        THINK,
        "it",
        "logic",
    ),
    # --- THINK: multi-step arithmetic ---
    _case(
        "Si invierto 1.000 € al 5% anual compuesto, ¿cuánto tendré al cabo de 3 años? Muestra el cálculo.",
        THINK,
        "es",
        "multi-step-math",
    ),
    _case(
        "A train leaves at 9:40 and arrives at 13:05, stopping 25 minutes in total. What was its "
        "average moving speed if the route is 300 km?",
        THINK,
        "en",
        "multi-step-math",
    ),
    _case(
        "Un rectángulo tiene el doble de largo que de ancho y un perímetro de 36 cm. ¿Cuál es su área?",
        THINK,
        "es",
        "multi-step-math",
    ),
    _case(
        "Je paie 3 cafés et 2 croissants 8,10 €, et 2 cafés et 3 croissants 7,90 €. Combien coûte un croissant ?",
        THINK,
        "fr",
        "multi-step-math",
    ),
    _case(
        "¿Cuál es el menor número que al dividirlo entre 2, 3, 4, 5 y 6 da siempre resto 1?",
        THINK,
        "es",
        "multi-step-math",
    ),
    _case(
        "Um trem sai de A às 8h a 60 km/h e outro sai de B às 9h a 90 km/h em direção a A. "
        "A distância é 300 km. A que horas se cruzam?",
        THINK,
        "pt",
        "multi-step-math",
    ),
    # --- THINK: planning under constraints ---
    _case(
        "Tengo 3 días en Lisboa, me gusta la comida y la historia, viajo con un niño de 6 años y no "
        "quiero coger coche. Planifícame los tres días.",
        THINK,
        "es",
        "planning",
    ),
    _case(
        "I have 4 hours, a laptop, spotty Wi-Fi, and I need to finish a report, prepare a 10-minute "
        "talk, and answer 30 emails. How should I sequence this?",
        THINK,
        "en",
        "planning",
    ),
    _case(
        "Organise un menu de la semaine pour deux personnes, végétarien, budget 40 €, sans répéter de plat principal.",
        THINK,
        "fr",
        "planning",
    ),
    _case(
        "Tengo que mudarme en dos semanas mientras trabajo a jornada completa. Hazme un plan realista por días.",
        THINK,
        "es",
        "planning",
    ),
    # --- THINK: trade-offs / analysis ---
    _case(
        "Compara PostgreSQL, MongoDB y SQLite para una app móvil offline-first con sincronización "
        "ocasional y razona cuál encaja mejor.",
        THINK,
        "es",
        "analysis",
    ),
    _case(
        "Should a small startup with 3 engineers adopt microservices? Argue both sides and give a recommendation.",
        THINK,
        "en",
        "analysis",
    ),
    _case(
        "Quelles seraient les implications de passer notre API de REST à GraphQL pour une équipe de "
        "5 personnes avec des clients mobiles anciens ?",
        THINK,
        "fr",
        "analysis",
    ),
    _case(
        "¿Me conviene más amortizar hipoteca anticipadamente o invertir ese dinero, si la hipoteca está "
        "al 3% y espero un 6% de rentabilidad pero con riesgo? Razónalo.",
        THINK,
        "es",
        "analysis",
    ),
    _case(
        "Explain why this argument is flawed: 'Every time I wash my car it rains, so washing my car causes rain.'",
        THINK,
        "en",
        "analysis",
    ),
    _case(
        "Hazme un análisis económico de la evolución del PIB de España en la última década, "
        "identificando causas y efectos.",
        THINK,
        "es",
        "analysis",
    ),
    # --- THINK: stepping through code ---
    _case(
        "Esta función debería sumar toda la lista pero da resultados incorrectos, ¿qué falla?\n"
        "def suma(xs):\n    total = 0\n    for i in range(1, len(xs)):\n        total += xs[i]\n    return total",
        THINK,
        "es",
        "code",
    ),
    _case(
        "Find the bug: this is supposed to return True for palindromes but fails on 'Racecar'.\n"
        "def is_pal(s): return s == s[::-1]",
        THINK,
        "en",
        "code",
    ),
    _case(
        "Pourquoi cette requête renvoie-t-elle des doublons ?\n"
        "SELECT c.nom FROM clients c JOIN commandes o ON o.client_id = c.id",
        THINK,
        "fr",
        "code",
    ),
    _case(
        "¿Qué imprime este código y por qué?\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)",
        THINK,
        "es",
        "code",
    ),
    # --- THINK: estimation ---
    _case(
        "Estima cuántas pelotas de tenis caben en un autobús urbano y explica tu razonamiento.",
        THINK,
        "es",
        "estimation",
    ),
    _case(
        "Roughly how many piano tuners are there in Chicago? Walk me through the estimate.",
        THINK,
        "en",
        "estimation",
    ),
]
