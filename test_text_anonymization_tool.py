import unittest
from text_anonymization_tool import TextProcessor

class TestTextProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = TextProcessor()

    def test_redact_names_with_names(self):
        text = "Patient John Doe visited the clinic."
        redacted, detected, redacted_words, word_types = self.processor.redact_names(text)
        #self.assertNotEqual(redacted, text)
        self.assertIn("John", detected)
        self.assertIn("Doe", detected)
        self.assertTrue(all(word in redacted_words for word in detected))
        self.assertTrue(len(word_types) > 0)

    def test_redact_names_without_names(self):
        text = "No personal information here."
        redacted, detected, redacted_words, word_types = self.processor.redact_names(text)
        self.assertEqual(redacted, text)
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

    def test_redact_names_empty_string(self):
        text = ""
        redacted, detected, redacted_words, word_types = self.processor.redact_names(text)
        self.assertEqual(redacted, "")
        self.assertEqual(detected, [])
        self.assertEqual(redacted_words, [])
        self.assertEqual(word_types, [])

if __name__ == '__main__':
    unittest.main()