from __future__ import annotations

import unittest

from douban_assistant.douban import (
    build_interest_update_form_data,
    extract_ck_from_cookie,
    parse_interest_editor_payload,
)


class TagWritebackTests(unittest.TestCase):
    def test_build_interest_update_form_data_keeps_existing_fields(self) -> None:
        editor = {
            "interest": "collect",
            "rating": "5",
            "ck": "-zp3",
            "comment": "有点意思",
            "private": False,
            "foldcollect": "U",
            "share_shuo": True,
        }

        data = build_interest_update_form_data(editor, ["历史", "社会"])

        self.assertEqual(data["tags"], "历史 社会")
        self.assertEqual(data["rating"], "5")
        self.assertEqual(data["ck"], "-zp3")
        self.assertEqual(data["comment"], "有点意思")
        self.assertNotIn("share-shuo", data)

    def test_parse_interest_editor_payload_extracts_current_values(self) -> None:
        payload = {
            "subject_id": "1102715",
            "cookie_header": 'bid=abc; ck="-zp3"; dbcl2="123"',
            "tags": ["哲学"],
            "html": """
            <div class="indentpop1 clearfix">
              <form action="https://book.douban.com/j/subject/1102715/interest" method="POST" class="j a_interest_form book-sns">
                <input type="radio" value="wish" name="interest" />
                <input type="radio" value="collect" name="interest" checked="checked" />
                <input id="foldcollect" name="foldcollect" value="U" type="hidden"/>
                <input id="n_rating" type="hidden" value="4" name="rating" />
                <input name="tags" type="text" class="inp-tags">
                <textarea name="comment" class="comment" id="comment" maxlength="350">短评</textarea>
                <input id="inp-private" name="private" type="checkbox" checked="checked" />
                <input name="share-shuo" type="checkbox" checked="checked" />
              </form>
            </div>
            """,
        }

        editor = parse_interest_editor_payload(payload)

        self.assertEqual(editor["action"], "https://book.douban.com/j/subject/1102715/interest")
        self.assertEqual(editor["interest"], "collect")
        self.assertEqual(editor["rating"], "4")
        self.assertEqual(editor["ck"], "-zp3")
        self.assertEqual(editor["current_tags"], ["哲学"])
        self.assertEqual(editor["comment"], "短评")
        self.assertTrue(editor["private"])
        self.assertTrue(editor["share_shuo"])

    def test_extract_ck_from_cookie_reads_cookie_token(self) -> None:
        cookie = 'bid=abc; ck="-zp3"; dbcl2="123:xyz"'

        self.assertEqual(extract_ck_from_cookie(cookie), "-zp3")


if __name__ == "__main__":
    unittest.main()
