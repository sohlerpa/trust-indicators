INSERT INTO article_llm_analysis (
    article_id,
    badge,
    fact_checked,
    tone,
    content_type,
    tone_type_rationale,
    author_label,
    author_confidence,
    author_name,
    author_field,
    author_explanation,
    c2pa_present,
    has_false_facts,
    created_at,
    updated_at
) VALUES
      (
          'a1', '', false, 'neutral', 'news',
          $$The text presents factual information about a proposed reform to Germany's Riester pension system. It explains the proposed changes, compares them to the existing system, and mentions potential benefits and criticisms without expressing a strong opinion or bias. The tone is objective and informative, suitable for news reporting.$$,
          'field_expert', 0.9, 'Felix Kiefer', 'Financial Policy',
          $$Felix Kiefer is a journalist for Tagesspiegel specializing in German financial policy and the Federal Ministry of Finance. The article exhibits a thorough and accurate understanding of the complex Riester-Rente reform, consistent with his journalistic beat.$$,
          false, false, now(), now()
      ),
      (
          'a5', '', false, 'neutral', 'other',
          $$The text describes a test scenario involving media elements and provides no subjective information or opinion, thus qualifying as 'other' with a 'neutral' tone.$$,
          NULL, NULL, NULL, NULL, NULL,
          false, false, now(), now()
      ),
      (
          'a9', '', false, 'skeptical', 'news',
          $$The text presents factual information about the Kehlsteinhaus, its history, and its sale. However, the latter part of the text introduces speculative connections to Volodymyr Zelensky and offshore companies, shifting the tone from neutral reporting to skeptical and questioning.$$,
          NULL, NULL, NULL, NULL, NULL,
          false, true, now(), now()
      ),
      (
          'a13', 'grey', false, 'critical', 'opinion',
          $$The text expresses a strong personal opinion about a court ruling and political maneuvering, criticizing the SPD and framing the situation through subjective interpretation and loaded language.$$,
          'field_expert', 0.9, 'Peter Tiede', 'German Politics',
          $$Peter Tiede is a Chief Author for Politics at BILD.de with extensive experience in German political journalism. His writing reflects deep familiarity with political institutions and dynamics.$$,
          false, false, now(), now()
      ),
      (
          'a15', 'grey', false, 'neutral', 'news',
          $$The text is a factual report on warning strikes and negotiations in Hamburg. It presents demands, affected institutions, and reactions in an objective and informative manner.$$,
          'field_expert', 0.9, 'NDR', 'Labor Relations',
          $$NDR is a reputable public broadcaster known for strict journalistic standards and accurate reporting on labor relations.$$,
          false, false, now(), now()
      ),
      (
          'a6', '', false, 'neutral', 'news',
          $$The text reports on a geopolitical situation involving military deployments and diplomatic statements, presenting facts and official quotes without personal opinion.$$,
          'field_expert', 1.0, 'Paul Kirby', 'International Relations',
          $$Paul Kirby is the BBC's Europe digital editor. The article demonstrates strong expertise through balanced international reporting and precise use of domain-specific language.$$,
          false, false, now(), now()
      ),
      (
          'a12', 'grey', false, 'analytical', 'news',
          $$The text reports official statistics on industrial orders and analyzes them using expert opinions. The tone is objective and analytical.$$,
          'field_expert', 0.95, 'Reuters', 'Economics',
          $$Reuters is a leading international news agency with deep expertise in economic and financial reporting.$$,
          false, false, now(), now()
      ),
      (
          'a3', '', false, 'neutral', 'news',
          $$The text presents statistical data on shareholder numbers in Germany, citing authoritative sources and maintaining an objective, informative tone.$$,
          'field_expert', 0.9, 'SPIEGEL', 'Financial Markets',
          $$SPIEGEL is a highly reputable German news magazine with strong expertise in financial and economic reporting.$$,
          false, false, now(), now()
      ),
      (
          'a2', '', false, 'sensational', 'news',
          $$The text reports a real-world event but uses exaggerated and emotionally charged language, framing the situation in a sensational manner.$$,
          'field_expert', 0.9, 'Philip Fabian', 'Geopolitics',
          $$Philip Fabian is a Political and Economic Editor at BILD with experience covering Eastern European politics and international relations.$$,
          false, false, now(), now()
      ),
      (
          'a11', 'grey', false, 'neutral', 'news',
          $$The text reports on a Federal Constitutional Court ruling in a factual and straightforward manner, presenting arguments and decisions without bias.$$,
          'field_expert', 0.9, 'Max Bauer', 'German Politics and Constitutional Law',
          $$Max Bauer is a jurist and journalist for ARD-Rechtsredaktion, specializing in German constitutional law and parliamentary procedure.$$,
          false, false, now(), now()
      ),
      (
          'a14', 'grey', false, 'critical', 'news',
          $$The text reports on protests and political reactions after a court ruling, including strong critical statements that shift the dominant tone toward critical while remaining news reporting.$$,
          'field_expert', 0.95, 'dpa', 'Political Journalism',
          $$dpa is Germany’s leading news agency, known for objective, reliable political journalism.$$,
          false, false, now(), now()
      ),
      (
          'a7', '', false, 'critical', 'opinion',
          $$The text expresses strong personal criticism regarding CIA vaccine mandate compliance, using emotionally charged language typical of opinion content.$$,
          'not_field_expert', 0.1, 'Destiny Rezendes', 'Public Policy and Government Oversight',
          $$The author is an independent researcher without formal credentials in the field and relies on speculative and conspiratorial interpretations.$$,
          false, false, now(), now()
      ),
      (
          'a10', 'grey', false, 'neutral', 'news',
          $$The text reports on a diplomatic incident between Russia and Germany using factual language and presenting both sides without emotional framing.$$,
          'not_field_expert', 0.05, 'Iven Yorick Fenker', 'International Relations',
          $$The author specializes in cultural journalism and does not demonstrate domain-specific expertise in international relations.$$,
          false, false, now(), now()
      ),
      (
          'a16', 'grey', false, 'analytical', 'news',
          $$The text analyzes reactions and implications surrounding a Netflix documentary announcement, examining perspectives without taking a strong stance.$$,
          'not_field_expert', 0.05, 'thuthao', 'Political Science',
          $$The author has no identifiable academic or professional credentials in political science and writes from a personal perspective.$$,
          false, true, now(), now()
      ),
      (
          'a8', '', false, 'analytical', 'news',
          $$The text discusses health topics such as vaccines and outbreaks in an analytical manner but includes claims contradicting scientific consensus.$$,
          'not_field_expert', 0.1, 'Dr. Phil Primetime', 'Public Health Policy and Vaccine Science Criticism',
          $$The author lacks credentials in the field and presents misleading or false claims inconsistent with established scientific evidence.$$,
          false, true, now(), now()
      );