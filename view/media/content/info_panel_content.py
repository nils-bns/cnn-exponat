"""Statische Inhalte fuer InfoPanel Widget."""

LAYER_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "de": {
        "conv1": """
                <h2>Kanten erkennen</h2>
                <p>Die KI zerlegt dein Bild gerade in <b>helle und dunkle Übergänge</b>. Überall, wo sich Farben oder Helligkeiten ändern, erkennt sie eine Kante.</p>
                <p>In diesem ersten Schritt arbeiten <b>64 kleine Filter</b>, die wie winzige Lupen über das Bild gleiten. Jeder Filter sucht nach Merkmalen.</p>
                <p><i>Diese Kanten sind die Grundbausteine für alles, was das Netzwerk später erkennen wird.</i></p>
            """,
        "layer1": """
                <h2>Texturen entdecken</h2>
                <p>Aus den Kanten formt die KI jetzt <b>Oberflächen und Texturen</b>. Einzelne Striche werden zu Mustern zusammengesetzt.</p>
                <p>Dazu kombiniert das Netzwerk die einfachen Kanten aus dem ersten Schritt zu immer <b>komplexeren Strukturen</b>. Wie Buchstaben, die aus Ecken,
                Bögen und Kreuzungen gebildet werden.</p>
                <p><i>Je mehr Texturen erkannt werden, desto klarer wird, woraus die Oberflächen im Bild bestehen.</i></p>
            """,
        "layer2": """
                <h2>Muster zusammensetzen</h2>
                <p>Die Texturen fügen sich jetzt zu <b>wiederkehrenden Mustern</b> zusammen. Die KI erkennt zum Beispiel runde Formen, Streifen oder regelmäßige Strukturen.</p>
                <p>Mit <b>128 Filtern</b> sucht das Netzwerk nach konkreteren Hinweisen. Das Bild wird dabei auf <b>28×28 Punkte</b> verdichtet, weniger Details, aber mehr Bedeutung. Wie Wörter statt Buchstaben.</p>
                <p><i>Aus diesen Mustern formt die KI im nächsten Schritt erkennbare Teile von Objekten.</i></p>
            """,
        "layer3": """
                <h2>Teile erkennen</h2>
                <p>Aus den Mustern werden jetzt <b>erkennbare Teile</b>: ein Auge, ein Rad, eine Flosse. Die KI sieht nicht mehr nur Formen, sondern beginnt zu verstehen, <b>was</b> sie sieht. Wie Sätze statt Wörter.</p>
                <p>Hier arbeiten bereits <b>256 Filter</b>, jeder spezialisiert auf bestimmte Objektteile. Das Bild ist auf <b>14×14 Punkte</b> geschrumpft, doch das Netzwerk erkennt dafür immer mehr.</p>
                <p><i>Gleich fügt die KI alle Teile zum großen Ganzen zusammen.</i></p>
            """,
        "layer4": """
                <h2>Das Ganze verstehen</h2>
                <p>Alle Teile zusammen ergeben jetzt das <b>vollständige Bild</b>. Die KI erkennt ganze Objekte und kann sie benennen.</p>
                <p>In diesem letzten Schritt arbeiten <b>512 Filter</b> auf nur noch <b>7×7 Punkten</b>. Was als einzelne Kanten begann, ist jetzt eine Bedeutung: Die KI versucht zu <b>„versteht"</b>, was sie sieht. Wie ein Text.</p>
                <p><i>Von einfachen Kanten zu einem ganzen Objekt, das ist der Weg, den dein Bild gerade genommen hat.</i></p>
            """,
    },
    "en": {
        "conv1": """
                <h2>Detecting edges</h2>
                <p>The AI is breaking your image into <b>transitions between light and dark</b>. Wherever colors or brightness change, it detects an edge.</p>
                <p>In this first step, <b>64 tiny filters</b> slide across the image like small magnifying glasses. Each filter searches for features.</p>
                <p><i>These edges are the building blocks for everything the network will recognize later.</i></p>
            """,
        "layer1": """
                <h2>Discovering textures</h2>
                <p>From the edges, the AI now forms <b>surfaces and textures</b>. Individual strokes are assembled into patterns.</p>
                <p>The network combines the simple edges from the first step into increasingly <b>complex structures</b>. Like letters formed from corners, curves, and intersections.</p>
                <p><i>The more textures are recognized, the clearer it becomes what the surfaces in the image are made of.</i></p>
            """,
        "layer2": """
                <h2>Assembling patterns</h2>
                <p>The textures now combine into <b>recurring patterns</b>. The AI recognizes things like round shapes, stripes, or regular structures.</p>
                <p>With <b>128 filters</b>, the network for more concrete clues. The image is condensed to <b>28×28 points</b>, fewer details, but more meaning. Like words instead of letters.</p>
                <p><i>From these patterns, the AI will form recognizable parts of objects in the next step.</i></p>
            """,
        "layer3": """
                <h2>Recognizing parts</h2>
                <p>From the patterns, <b>recognizable parts</b> now emerge: an eye, a wheel, a fin. The AI no longer sees just shapes, it starts to understand <b>what</b> it is looking at. Like sentences instead of words.</p>
                <p>At this stage, <b>256 filters</b> are at work, each specialized in certain object parts. The image has shrunk to <b>14×14 points</b>, yet the network recognizes more and more.</p>
                <p><i>Next, the AI will put all the parts together to see the bigger picture.</i></p>
            """,
        "layer4": """
                <h2>Understanding the whole</h2>
                <p>All the parts now come together to form the <b>complete picture</b>. The AI recognizes entire objects and can name them.</p>
                <p>In this final step, <b>512 filters</b> work on just <b>7×7 points</b>. What started as simple edges is now meaning: The AI attempts to <b>"understand"</b> what it sees. Like a text.</p>
                <p><i>From simple edges to a whole object, that is the journey your image has just taken.</i></p>
            """,
    },
}
