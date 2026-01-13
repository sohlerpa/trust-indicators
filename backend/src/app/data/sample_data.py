from datetime import datetime

from pydantic import HttpUrl

from src.app.models.models import ArticleRecord, XPostRecord

ARTICLES: list[ArticleRecord] = [
    ArticleRecord(
        id="a1",
        title="Riester-Rente 2.0: So soll die private Altersvorsorge künftig funktionieren",
        source="zeit.de",
        published_at=datetime(2025, 12, 9, 10, 15, 00),
        image_url=HttpUrl(
            "https://www.tagesspiegel.de/images/15031465/alternates/BASE_21_9_W1000/1765204232000/colorful-collage-businessman-riding-bicycle-with-money-wheels-climbing-spiral-staircase-to-red-flag.jpeg"),
        url=HttpUrl(
            "https://www.tagesspiegel.de/politik/riester-rente-20-so-soll-die-private-altersvorsorge-kunftig-funktionieren-15030828.html"),
        author="Felix Kiefer",
        content_html="<p>Nach dem Beschluss der Rentenreform hat Finanzminister Klingbeil sein Konzept für ein neues Altersvorsorgedepot vorgelegt. Für Verbraucher soll alles einfacher werden. Was ändert sich?</p>"
                     "<p>Was vor einem Vierteljahrhundert als revolutionär galt, ist heute für viele Sparerinnen und Sparer zu einem Symbol des Scheiterns geworden. Wollte der Staat mit der Riester-Rente die private Altersvorsorge stärken und Druck vom umlagefinanzierten Rentensystem nehmen, fällt das Fazit aus Sicht von Sparern wie Anbietern heute meist negativ aus: zu unrentabel, zu teuer, zu kompliziert.</p>"
                     "<p>Reformieren wollte das System schon die Ampelkoalition. Nach ihrem Scheitern nimmt es sich nun auch die schwarz-rote Koalition vor. Bundesfinanzminister Lars Klingbeil (SPD) hat ein Gesetz für eine grundlegende Änderung der privaten Altersvorsorge auf den Weg gebracht. „Kostengünstiger, renditestärker, unbürokratischer, flexibler, einfacher und transparenter“ soll sie werden, heißt es in Klingbeils Gesetzentwurf. Doch was ändert sich konkret gegenüber dem Modell, dem der mittlerweile 82-jährige Walter Riester als Arbeitsminister seinen Namen gegeben hat?</p>"
                     "<h2>Mehr Rendite durch Aufhebung der Garantie</h2>"
                     "<p>Zunächst einmal der Grundgedanke. Bisher müssen Anbieter garantieren, dass Rentner zumindest ihre eingezahlten Beträge zurückerhalten. Nun soll es erstmals ein staatlich gefördertes Altersvorsorgeprodukt ohne Beitragsgarantie geben. Sparer können also etwa in Fonds investieren, die deutlich mehr Rendite abwerfen. Anders als bei der Riester-Rente haben sie aber keinen Anspruch darauf, dass sie das eingezahlte Geld später auch zurückbekommen. Wer weiterhin auf Sicherheit setzen will, für den bleiben zwei Varianten mit einer Garantie von 80 Prozent oder gar 100 Prozent. Das geringere Risiko käme allerdings auf Kosten der Rendite."
                     " 480 Euro an staatlicher Grundzulage sind unter Riester 2.0 möglich.</p>"
                     "<p>Ein weiterer Kritikpunkt am bisherigen Riester-Modell sind die hohen Kosten, die die ohnehin geringe Rendite weiter auffressen. Jeder vierte eingezahlte Euro eines durchschnittlichen Riester-Vertrags geht laut der NGO Finanzwende dafür drauf. Klingbeil plant nun einen Kostendeckel. Zumindest bei einem Standardprodukt, das alle Banken anbieten und bei dem Verbraucher keine aktive Entscheidung treffen müssen, sollen sie maximal 1,5 Prozent betragen. Der Bundesverband deutscher Banken äußerte allerdings bereits Bedenken, ein tragfähiges Produkt zu den Konditionen anbieten zu können.</p>"
                     "<h2>Keine starren Zulagen mehr</h2>"
                     "<p>Kern der Reform dürfte allerdings sein, überhaupt mehr Menschen in die private Altersvorsorge zu bekommen. Die Riester-Rente hat das nicht geschafft: Nur 40 Prozent der anspruchsberechtigten Deutschen haben sich überhaupt dafür entschieden. Ein Viertel davon hat seinen Vertrag mittlerweile wieder gekündigt, ein weiteres Viertel lässt ihn ruhen. So zahlen aktuell weniger als zehn Millionen Menschen in ihre Riester-Rente ein und erhalten staatliche Beiträge.</p>"
                     "<p>Eine aktuelle Sonderauswertung der Deutschen Rentenversicherung zeigt, dass selbst davon nur die Hälfte überhaupt die volle staatliche Grundzulage von jährlich 175 Euro erhält. Der Grund dürfte die Komplexität des Modells sein: Die Zulage muss jährlich beantragt werden und sie erhält nur in Gänze, wer mindestens vier Prozent des Vorjahreseinkommens abzüglich der staatlichen Zulagen einzahlt. Wer also eine Gehaltserhöhung erhält, aber seine Riester-Einzahlung nicht ändert, rutscht aus der Förderung.</p>"
                     "<p>Klingbeil will die Riester-Rente 2.0 deutlich einfacher aufstellen. Die starre und immer wieder zu beantragende Zulage wird abgeschafft. Der Mindesteigenbetrag sinkt auf 120 Euro. Stattdessen soll man künftig relativ zum eingezahlten Betrag profitieren, Menschen mit geringerer Sparfähigkeit dabei stärker.</p>"
                     "<p>Denn bis zu einer Grenze von 1200 Euro jährlich will der Staat künftig für jeden investierten Euro 30 Cent dazugeben. Bis zur Höchstgrenze von 1800 sind es zumindest 20 Cent je Euro. So sind 480 Euro staatliche Grundzulagen möglich. Dazu kommt eine Kinderzulage von 25 Prozent, maximal 300 Euro pro Kind. Wer unter 25 ist, erhält zudem einmalig 200 Euro. Für besonders junge Sparer plant Schwarz-Rot zudem die Frühstart-Rente.</p>"
                     "<p>Wie beim bisherigen Riester-Modell sollen die Sparbeträge in der Einzahlungsphase steuerfrei sein und erst bei Auszahlung versteuert werden. Wer bereits einen Riestervertrag hat, kann entweder seine bisherige Förderung fortsetzen oder in eine neue Förderung wechseln. Grundsätzlich soll das Wechseln von Anbietern künftig einfacher werden. So sollen die Abschlusskosten von Altersvorsorgeverträgen auf die gesamte Vertragslaufzeit verteilt werden, sodass bei einem Vertragswechsel eine Doppelbelastung verhindert wird.</p>"
                     "<p>Noch müssen die Pläne allerdings im Kabinett (voraussichtlich am 17. Dezember) sowie im Deutschen Bundestag beschlossen werden. Änderungen sind also noch möglich. An den Start gehen sollen die Riester-Rente 2.0 sowie die Frühstart-Rente dann zum Jahreswechsel 2027.</p>"
        ,
    ),
    ArticleRecord(
        id="a2",
        title="Ballon-Terror! Litauen ruft Notstand aus",
        source="bild.de",
        published_at=datetime(2025, 12, 9, 18, 57, 00),
        image_url=HttpUrl(
            "https://images.bild.de/6937da9211f914c89b8576e7/520f6ec8ef5bad321741870131cf5360,8f8a71ae?w=992"),
        url=HttpUrl(
            "https://www.bild.de/politik/inland/hybrider-angriff-von-putin-kumpel-notlage-nato-land-reagiert-auf-ballon-terror-6937da9211f914c89b8576e7"),
        author="Philip Fabian",
        content_html="<h2>Hybrider Angriff von Putin-Kumpel: Ballon-Terror! Litauen ruft Notstand aus</h2>"
                     "<p>Hält sich dank Putin an der Macht und provoziert die Nachbarländer: Belarus-Diktator Alexander Lukaschenko (71)</p>"
                     "<p>Vilnius – Der Terror aus dem Nachbarland hört nicht auf! Litauen ruft wegen Ballons aus Belarus den Notstand aus. Innenminister Wladislaw Kondratowitsch begründet den Schritt nicht nur mit Störungen des Flugverkehrs, sondern auch mit Interessen der nationalen Sicherheit. EU-Kommissionspräsidentin Ursula von der Leyen spricht von einem „inakzeptablen hybriden Angriff“.</p>"
                     "<p>Die Regierung in Minsk weist die Vorwürfe zurück. Fakt ist aber: In Litauen musste in den vergangenen Wochen mehrfach vorübergehend der Betrieb an Flughäfen wegen aus Belarus einfliegender Wetterballons ausgesetzt werden. Schmuggler nutzen die Ballons üblicherweise, um Zigaretten illegal ins Land zu bringen – zuletzt flogen immer mehr davon ein.</p>"
                     "<p>Die litauische Regierung sieht dahinter eine „hybride Attacke“ der belarussischen Führung in Minsk. Mit der Sperrung wollte Vilnius Minsk zwingen, die Ballonflüge zu stoppen.</p>"
                     "︎<p>Auch die Grenze zwischen beiden Ländern war wochenlang geschlossen. Lkw kamen seit Ende Oktober nicht durch. Erst am 19. November öffnete das kleine Litauen (2,9 Mio. Einwohner) die Grenze wieder.</p>"
                     "︎<p>Und: Kinder machen schon in der Schule ihren „Drohnenführerschein“.</p>"
                     "<p>Im November beschloss Litauens „Rat für staatliche Verteidigung“ außerdem ein 500-Mio.-Euro-Paket zum Schutz vor russischen Spionage- und Kamikaze-Drohnen und zur Abwehr staatlich organisierter belarusischer Schmuggler-Ballons – ein Riesenposten im Haushalt des kleinen Landes (mehr als 5 Prozent des Litauen-BIPs von etwa 78 Mrd. Euro 2024).</p>"
                     "<p>Vize-Verteidigungsminister Tomas Godliauskas erklärte damals BILD, dass die Drohnen- und Ballongefahr aus Putins Reich „nicht nur theoretisch, sondern ganz praktisch unser Leben bereits erschwert und unterbricht“. Darum müsse die Politik sofort handeln, um die Bevölkerung, die kritische Infrastruktur und den Luftverkehr im Land zu schützen.</p>"
        ,
    ),
    ArticleRecord(
        id="a3",
        title="Mehr als 14 Millionen Deutsche besitzen Aktien",
        source="spiegel.de",
        published_at=datetime(2026, 1, 13, 13, 22, 00),
        image_url=HttpUrl(
            "https://cdn.prod.www.spiegel.de/images/9f1aa452-5e4a-4239-b481-eba8497b109c_w1920_r1.778_fpx50_fpy53.webp"),
        url=HttpUrl(
            "https://www.spiegel.de/wirtschaft/unternehmen/rekordzahlen-des-deutschen-aktieninstituts-mehr-als-14-millionen-deutsche-besitzen-aktien-a-ebc734c3-f3c3-4551-a700-24fcd559ac5e"),
        author="",
        content_html=(
            "<p>Deutschland hat so viele Aktionäre wie nie zuvor: 14,1 Millionen Deutsche besaßen 2025 "
            "Aktien, ETFs oder Aktienfonds – rund zwei Millionen mehr als im Vorjahr.</p>"
            "<p>Im Verlauf des Jahres 2025 besaßen durchschnittlich 14,1 Millionen Menschen in Deutschland "
            "Aktienfonds, ETFs oder Aktien. Das zeigen Zahlen des Deutschen Aktieninstituts (DAI). "
            "Nach zwei Jahren mit rückläufigen Aktionärszahlen wurde damit der Rekord von 2022 "
            "mit seinerzeit fast 12,9 Millionen Aktionärinnen und Aktionären deutlich übertroffen.</p>"
            "<p>Damit investierte knapp jede fünfte Person ab 14 Jahren direkt oder indirekt am Aktienmarkt. "
            "Seit 2020 werden in der DAI-Statistik auch ausländische Aktionäre mit Wohnsitz in Deutschland "
            "erfasst, was allein für einen Zuwachs von rund 500.000 sorgte.</p>"
            "<p>Vor allem das Interesse der jungen Generation trug zum Anstieg bei. 4,9 Millionen Menschen "
            "unter 40 Jahren besaßen Aktien, ETFs oder Aktienfonds – 1,2 Millionen mehr als im Vorjahr. "
            "Diese Altersgruppe machte damit rund 60 Prozent des Gesamtanstiegs aus. Auch bei Frauen "
            "und in Ostdeutschland verzeichnete das Institut ein starkes Wachstum.</p>"
            "<p>»Aktienfonds, ETFs und Aktien sind in der Mitte der Gesellschaft verankert«, heißt es vom "
            "Deutschen Aktieninstitut. Der gesellschaftliche Rückenwind für die Aktie sei so stark wie "
            "nie zuvor.</p>"
            "<p>Das Institut fordert deshalb, die Aktienanlage stärker in allen drei Säulen der Altersvorsorge "
            "zu verankern. Die derzeitigen Pläne der Bundesregierung zur Ergänzung der Rente durch private "
            "Aktienvorsorge seien bislang zu zaghaft.</p>"
            "<p>Die Aktionärszahlen basieren auf einer repräsentativen Umfrage des Marktforschungsinstituts "
            "Kantar, bei der jährlich rund 28.000 Menschen in Deutschland ab 14 Jahren zu ihrem "
            "Anlageverhalten befragt werden.</p>"
            "<p>Im internationalen Vergleich investieren Deutsche ihr Vermögen dennoch vergleichsweise "
            "zurückhaltend am Kapitalmarkt. Einer Studie der Vereinigung für Finanzmärkte in Europa (AFME) "
            "zufolge investieren Privathaushalte in Deutschland rund 103 Prozent der jährlichen "
            "Wirtschaftsleistung in Aktien, ETFs oder Fonds – deutlich weniger als etwa in Dänemark "
            "(194 Prozent) oder den Niederlanden (164 Prozent).</p>"
        ),
    )
]

X_POSTS: list[XPostRecord] = [
    XPostRecord(
        id="x1",
        handle="@exampleUser1",
        display_name="Example User 1",
        text="First X post",
        created_at=datetime(2025, 12, 21, 11, 15, 00)
    ),
    XPostRecord(
        id="x2",
        handle="@exampleUser2",
        display_name="Example User 2",
        text="Second X post",
        created_at=datetime(2025, 12, 21, 12, 34, 28)
    ),
]


def load_all_articles() -> list[ArticleRecord]:
    return ARTICLES


def get_article_by_id(article_id: str) -> ArticleRecord | None:
    return next((a for a in ARTICLES if a.id == article_id), None)
