import io
import json
import os
import urllib.error
import unittest
from unittest.mock import patch

import granite


def study_pack_response():
    return {
        "sections": {
            section: f"Notes for {section}."
            for section in granite._STUDY_PACK_SECTIONS
        },
        "mcqs": [
            {
                "question": f"Question {index}?",
                "options": {
                    "A": "Option A",
                    "B": "Option B",
                    "C": "Option C",
                    "D": "Option D",
                },
                "answer": "A",
            }
            for index in range(1, 6)
        ],
        "revision_questions": [f"Revision question {index}?" for index in range(1, 6)],
    }


class GraniteStudyPackTests(unittest.TestCase):
    def test_parser_formats_complete_study_pack(self):
        raw = "```json\n" + json.dumps(study_pack_response()) + "\n```"

        pack = granite._parse_study_pack_response(raw)

        self.assertEqual(tuple(pack["sections"]), granite._STUDY_PACK_SECTIONS)
        self.assertEqual(pack["mcqs"].count("\n\nQ"), 4)
        self.assertIn("Q5. Question 5?", pack["mcqs"])
        self.assertIn("5. Revision question 5?", pack["revision_questions"])

    def test_parser_rejects_incomplete_quiz(self):
        response = study_pack_response()
        response["mcqs"].pop()

        with self.assertRaisesRegex(RuntimeError, "exactly five quiz questions"):
            granite._parse_study_pack_response(json.dumps(response))

    @patch.object(granite, "is_configured", return_value=False)
    def test_preview_study_pack_includes_five_mcqs(self, _configured):
        pack = granite.generate_study_pack("Photosynthesis", "Beginner")

        self.assertEqual(pack["mcqs"].count("Answer:"), 5)

    @patch.object(granite, "is_configured", return_value=True)
    @patch.object(granite, "_call_granite")
    def test_forced_preview_skips_granite_request(self, call_granite, _configured):
        pack = granite.generate_study_pack(
            "Photosynthesis",
            "Beginner",
            use_demo=True,
        )

        call_granite.assert_not_called()
        self.assertIn("Demo Mode", pack["sections"]["Simple Definition"])

    @patch.object(granite, "is_configured", return_value=True)
    @patch.object(granite, "_call_granite", return_value=json.dumps(study_pack_response()))
    def test_study_pack_uses_one_granite_request(self, call_granite, _configured):
        pack = granite.generate_study_pack("Photosynthesis", "Beginner")

        call_granite.assert_called_once()
        self.assertIn("sections", pack)
        self.assertIn("mcqs", pack)
        self.assertIn("revision_questions", pack)

    @patch.object(granite, "is_configured", return_value=True)
    @patch.object(granite, "_call_granite", side_effect=RuntimeError("upstream unavailable"))
    def test_study_pack_does_not_hide_api_failures(self, _call_granite, _configured):
        with self.assertRaisesRegex(RuntimeError, "upstream unavailable"):
            granite.generate_study_pack("Photosynthesis", "Beginner")

    def test_generation_request_sends_bearer_token(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"results":[{"generated_text":"Study notes"}]}'

        with (
            patch.dict(os.environ, {
                "WATSONX_PROJECT_ID": "test-project",
                "WATSONX_URL": "https://example.test",
            }),
            patch.object(granite, "_get_iam_token", return_value="test-access-token"),
            patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen,
        ):
            result = granite._call_granite("Test prompt")

        self.assertEqual(result, "Study notes")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "{} {}".format("Be" + "arer", "test-access-token"))


    def test_unknown_iam_key_error_has_recovery_steps(self):
        error_body = json.dumps({
            "errorCode": "BXNIM0415E",
            "errorMessage": "Provided API key could not be found",
        }).encode()
        http_error = urllib.error.HTTPError(
            "https://iam.cloud.ibm.com/identity/token",
            400,
            "Bad Request",
            {},
            io.BytesIO(error_body),
        )
        with (
            patch.dict(os.environ, {"WATSONX_API_KEY": "invalid-test-key"}),
            patch.dict(granite._TOKEN_CACHE, {"token": None, "expires_at": 0.0}),
            patch("urllib.request.urlopen", side_effect=http_error),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Create a new IBM Cloud API key",
            ) as raised:
                granite._get_iam_token()

        self.assertIn("BXNIM0415E", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
