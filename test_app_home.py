import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class HomePreviewTests(unittest.TestCase):
    def setUp(self):
        self.app_path = Path(__file__).with_name("app.py")

    def open_page(self, page):
        app = AppTest.from_file(str(self.app_path), default_timeout=10).run()
        app.radio[0].set_value(page).run()
        self.assertFalse(app.exception)
        return app

    def test_examples_generate_study_packs_in_preview_mode(self):
        app = AppTest.from_file(str(self.app_path), default_timeout=10).run()

        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["demo_mode"])
        self.assertTrue(
            any("Welcome, Student!" in element.value for element in app.markdown)
        )
        self.assertFalse(any("Dataset" in element.value for element in app.markdown))
        self.assertNotIn("kh_btn", {button.key for button in app.button})

        for key in (
            "home_example_simplify",
            "home_example_explain",
            "home_example_quiz",
            "home_example_revision",
        ):
            app.button(key=key).click().run()

            self.assertFalse(app.exception)
            assistant_message = app.session_state["chat_history"][-1]
            self.assertEqual(assistant_message["role"], "assistant")
            self.assertTrue(assistant_message["preview_mode"])
            self.assertIn("study_pack", assistant_message)
            self.assertEqual(
                tuple(assistant_message["study_pack"]["sections"]),
                (
                    "Simple Definition",
                    "Easy Explanation",
                    "Real-Life Example",
                    "Important Exam Points",
                    "Short Summary",
                    "Difficult Words",
                ),
            )
            self.assertEqual(assistant_message["study_pack"]["mcqs"].count("Answer:"), 5)

    def test_light_appearance_switches_stylesheet(self):
        app = AppTest.from_file(str(self.app_path), default_timeout=10).run()
        app.toggle(key="light_mode").set_value(True).run()

        self.assertFalse(app.exception)
        self.assertTrue(app.session_state["light_mode"])
        self.assertTrue(
            any("app-light-mode" in element.value for element in app.markdown)
        )

    def test_simplify_page_uses_preview_mode(self):
        app = self.open_page("Simplify Content")
        app.text_area(key="s_ta").set_value(
            "Photosynthesis uses sunlight, water, and carbon dioxide to make "
            "glucose and oxygen in plant cells."
        )
        app.button(key="s_btn").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["history"]), 1)

    def test_study_materials_page_uses_preview_mode(self):
        app = self.open_page("Study Materials")
        app.button(key="sm_btn").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["history"]), 1)

    def test_quiz_page_uses_preview_mode(self):
        app = self.open_page("Quiz Generator")
        app.text_area(key="qz_input").set_value(
            "The water cycle moves water through evaporation, condensation, "
            "precipitation, and collection. The sun warms water, which rises "
            "as vapor and later returns to Earth as rain."
        )
        app.button(key="qz_generate_btn").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["quiz_parsed"]), 5)
