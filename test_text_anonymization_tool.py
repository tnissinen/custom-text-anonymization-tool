import unittest
from text_anonymization_tool import TextProcessor


class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()

    def check_redacted_dates(self, text, is_date=True):
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)

        if is_date:
            self.assertNotEqual(redacted, text)
            self.assertIn("DATE*", redacted)
        else:
            self.assertEqual(redacted, text)
            self.assertEqual(detected, [])

    def test_redact_dates_1(self):
        self.check_redacted_dates("Vertailussa on kuvat 25.7.14. Nikamacorpusten muoto on tavallinen.")
        self.check_redacted_dates("Vertailussa 25.7. kuvat.")
        self.check_redacted_dates("Vertailussa 21.4 kuvat.")
        self.check_redacted_dates("Vertailussa 1.5.2019 kuvat.")
        self.check_redacted_dates("Vertailussa 01.03.04 kuvat.")
        self.check_redacted_dates("Vertailussa 01.01.1994 kuvat.")
        self.check_redacted_dates("Vertailussa 1.3 kuvat.")

        self.check_redacted_dates("Nikaman korkeus 41.3 cm", is_date=False)
        self.check_redacted_dates("Nikaman korkeus 1.32 cm", is_date=False)

    def test_redact_dates_2(self):
        self.check_redacted_dates("Vertailussa on kuvat 25/6/12. Nikamacorpusten muoto on tavallinen. Toinen kuvaus 4/11/20.")
        self.check_redacted_dates("Vertailussa 25/7 kuvat.")
        self.check_redacted_dates("Vertailussa 2/2004 kuvat.")
        self.check_redacted_dates("Vertailussa 1/5/2019 kuvat.")
        self.check_redacted_dates("Vertailussa 01/03/04 kuvat.")
        self.check_redacted_dates("Vertailussa 01/01/1994 kuvat.")
        self.check_redacted_dates("Vertailussa 1/3 kuvat.")

        self.check_redacted_dates("Verenpaine mitattu 80/100. Potilas terve.", is_date=False)

    def test_redact_dates_3(self):
        self.check_redacted_dates("Vertailussa on kuvat 250622. Nikamacorpusten muoto on tavallinen. ")
        self.check_redacted_dates("Vertailussa 20230701 kuvat.")
        self.check_redacted_dates("Vertailussa 06081994 kuvat.")
        self.check_redacted_dates("Vertailussa 110519 kuvat.")

        self.check_redacted_dates("Tutkimuksen numero 20132445", is_date=False)

    def test_redact_names_with_names(self):
        text = "Lausuttavana on kuvat Janne Markkasen tutkimuksesta."
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)

        detected_lower = [d.lower() for d in detected]
        self.assertIn("janne markkasen", detected_lower)
        self.assertTrue(len(word_types) > 0)

    def test_redact_names_without_names_1(self):
        text = "No personal information here."
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertEqual(redacted, text)
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

    def test_redact_names_without_names_2(self):
        text = "Ei vertailututkimuksia PACS:issa. Glenohumeraalinivel säännöllinen. Subakromiaalitila on jonkin verran madaltunut kiertäjäkalvosimen problematiikkaan viitaten."
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertEqual(redacted, text)
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

    def test_redact_names_without_names_3(self):
        text = "Sternumin haavainfektio keuhkotubin hoidossa. Kyseessä 78-vuotias mies. P.k. kontrolli thorax CT. Verenpaine matala 50/80. Ei kuumetta."
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertEqual(redacted, text)
        self.assertEqual(detected, [])

    def test_redact_names_without_names_4(self):
        text = "Uudisluun muodostusta ei nivelen reunoissa ole korkeintaan hienoista terävöitymistä. Molemmin puolin trochanter majorin alueella on jänneinsertioiden alueella kalkkia entesiitti-tyyppisesti. SI-nivelet vaikuttavat avoimilta"
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertEqual(redacted, text)
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

    def test_redact_names_empty_string(self):
        text = ""
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertEqual(redacted, "")
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

    def test_redact_names_basic(self):
        text = "Potilas 1: Nimi: Matti Meikäläinen, Syntymäaika: 12.05.1980, Sähköposti: matti.meikalainen@example.com, Hetu: 120580-123A, Osoite: Katu 1, Helsinki, Diagnoosi: Diabetes, Historia: Potilas on ollut diabeteksen hoidossa 10 vuotta. Verensokeritasot ovat olleet hyvin hallinnassa insuliinihoidolla. Verotiedot: Tulot: 50,000€, Veronumero: 123456789"
        redacted, detected, redacted_words, word_types = self.processor.process_text(text)
        self.assertNotEqual(redacted, text)

        self.assertIn("matti meikalainen", [d.lower() for d in detected])
        self.assertIn("120580-123a", [d.lower() for d in detected])
        self.assertIn("12.05.1980", [d.lower() for d in detected])
        self.assertIn("matti.meikalainen@example.com", [d.lower() for d in detected])
        self.assertIn("helsinki", [d.lower() for d in detected])


if __name__ == '__main__':
    unittest.main()