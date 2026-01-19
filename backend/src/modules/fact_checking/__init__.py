from src.modules.fact_checking.fact_checking import check_facts_for_html

if __name__=="__main__":


    content = """
    <p>Poivre d'Arvor said the initial French deployment involved 15 people, hours after Denmark and Greenland's foreign ministers travelled to Washington for a meeting with US Vice-President JD Vance on Wednesday.</p>
<p>Following the meeting, Danish Foreign Minister Lars Lokke Rasmussen said while the talks were constructive, there remained a "fundamental disagreement" between the two sides and later criticised Trump's bid to buy Greenland.</p>
<p>Trump, meanwhile, doubled down on his bid to bring Greenland under US control, telling reporters in the Oval Office, "we need Greenland for national security". Although he did not rule out the use of force, he said late on Wednesday that he thought something could be worked out with Denmark.</p>
<p>"The problem is there's not a thing that Denmark can do about it if Russia or China wants to occupy Greenland, but there's everything we can do. You found that out last week with Venezuela."</p>
<p>Polish Prime Minister Donald Tusk said Poland was not planning to join the European military deployment to Greenland, but warned that any US military intervention there "would be a political disaster".</p>
<p>"A conflict or attempted annexation of the territory of a Nato member by another Nato member would be the end of the world as we know it - and which for many years guaranteed our security," he told a press conference.</p>
<p>Russia's embassy in Belgium meanwhile expressed "serious concern" at what was unfolding in the Arctic, accusing Nato of building up a military presence there "under the false pretext of a growing threat from Moscow and Beijing".</p>
<p>However, the European Nato deployment consists of only a few dozen personnel as part of Danish-led joint exercises called Operation Arctic Endurance. While heavy in symbolism, it was not immediately clear how long they would stay.</p>
<p>Finland is sending two military liaison officers for what it said was a fact-finding mission during what was currently a planning stage of the operation.</p>
<p>"Right now we are not ruling anything out but we are not specifically considering anything," Janne Kuusela, head of the defence ministry's policy department, told the BBC.</p>
<p>Finland is also an Arctic nation, and Kuusela said the aim was to increase the and defence of an allied territory, following concerns about how firm a grip Nato had on Greenland.</p>
<p>Germany was sending an A400M transport plane to Nuuk on Thursday with a contingent of 13 soldiers, although officials said they would stay in Greenland only until Saturday.</p>
<p>Danish defence officials said they had decided with the government of Greenland that there would be an increased military presence around Greenland in the coming period to bolster Nato's "footprint in the Arctic for the benefit of both European and transatlantic security".</p>
<p>Macron, in his new year address to France's armed forces, said Europeans had a special responsibility to Greenland "because this territory belongs to the European Union and it's also one of our Nato allies".</p>
<p>The US already has a military base in Greenland, currently staffed by up to 150 people, and has the option of bringing in far greater numbers under existing agreements with Copenhagen. But the Danish-led initiative is seen as signalling to the Trump administration that its European allies also have a stake in security in the Arctic and North Atlantic.</p>
<p>Sweden's prime minister said Swedish army officers had been sent to Nuuk on Wednesday. Two Norwegian soldiers, one British military officer and a Dutch naval officer were also being sent.</p>
<p>Downing Street said the UK shared President Trump's concern about "the security of the High North", and said the deployment involved "stepping up with stronger exercising, to deter the Russian aggression and the Chinese activity."</p>
<p>Danish Prime Minister Mette Frederiksen said on Thursday that defence and protection of Greenland was a common concern for the entire Nato alliance.</p>
<p>Danish Defence Minister Troels Lund Poulsen said the intention was to have a military presence "in rotation", with the aim of having a more permanent military presence on the island with foreign allies taking part in exercise and training activities.</p>
<p>Copenhagen has disputed Trump's justification for wanting to control Greenland. Rasmussen, its foreign minister, said on Wednesday there was no "instant threat" from China or Russia that Denmark and Greenland could not accommodate, although he shared American security concerns to some extent.</p>
<p>A Democratic-led US delegation is due to visit Denmark on Friday for talks with Danish MPs.</p>
<p>Rasmussen spoke alongside Greenland's foreign minister after talks with Vance and US Secretary of State Marco Rubio on Wednesday.</p>
<p>"The president's ambition is on the table," the Danish diplomat told Fox News. "Of course we have our red lines. This is 2026, you trade with people but you don't trade people."</p>
<p>Greenland's Prime Minister, Jens-Frederik Nielsen, said this week that the territory was in the midst of a geopolitical crisis, and that if his people were asked to make a choice they would choose Denmark over the US.</p>
<p>"Greenland does not want to be owned by the United States. Greenland does not want to be governed by the United States. Greenland does not want to be part of the United States," he stressed.</p>
$$
    """

    checks = check_facts_for_html(content)

    for c in checks:
        print("\nCheck")
        print(c)