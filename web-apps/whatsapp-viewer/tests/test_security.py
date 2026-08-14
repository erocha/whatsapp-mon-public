from pathlib import Path

from app.storage import fallback_name, normalize_phone, parse_contacts_csv
from app.repository import display_name, media_relative_path, phone_label, vcard_escape


def test_normalize_phone():
    assert normalize_phone("+55 (11) 99999-0000") == "5511999990000"


def test_fallback_name():
    assert fallback_name("5511999990000@s.whatsapp.net") == "5511999990000"
    assert fallback_name(None) == "Desconhecido"


def test_sensitive_paths_ignored():
    gitignore = (Path(__file__).parents[1] / ".gitignore").read_text()
    assert "data/" in gitignore
    assert "certs/" in gitignore


def test_whatsapp_media_paths_are_relative_to_media_root():
    expected = Path("WhatsApp Voice Notes/202622/PTT-20260530-WA0029.opus")
    assert media_relative_path("Media/WhatsApp Voice Notes/202622/PTT-20260530-WA0029.opus") == expected
    assert media_relative_path("WhatsApp/Media/WhatsApp Voice Notes/202622/PTT-20260530-WA0029.opus") == expected
    assert media_relative_path("/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Voice Notes/202622/PTT-20260530-WA0029.opus") == expected


def test_message_links_open_safely_in_new_tab():
    javascript = (Path(__file__).parents[1] / "app/static/linkify.js").read_text(encoding="utf-8")
    assert 'link.target = "_blank"' in javascript
    assert 'link.rel = "noopener noreferrer"' in javascript


def test_vcard_escaping():
    assert vcard_escape("Empresa, Nome; Sul\\SP\nFilial") == "Empresa\\, Nome\\; Sul\\\\SP\\nFilial"


def test_phone_display():
    assert phone_label("5511999990000") == "+5511999990000"
    assert display_name("Maria", "5511999990000") == "Maria · +5511999990000"
    assert display_name("5511999990000", "5511999990000") == "+5511999990000"


def test_contact_profile_media_links_are_safe():
    javascript = (Path(__file__).parents[1] / "app/static/contact-profile.js").read_text(encoding="utf-8")
    assert 'rel="noopener noreferrer"' in javascript
    assert "/api/messages/${messageId}/contact-profile" in javascript


def test_semicolon_contacts_csv():
    rows = parse_contacts_csv("Phone;Name;PushName;ShortName;IsBusiness\n13135550002;Meta AI;;Meta AI;true\n")
    assert rows == [{"phone": "13135550002", "name": "Meta AI", "push_name": "", "short_name": "Meta AI", "is_business": 1}]


def test_contacts_csv_name_fallback():
    rows = parse_contacts_csv("Phone;Name;PushName;ShortName;IsBusiness\n+5511999990000;;Maria;Mari;false\n")
    assert rows[0]["name"] == "Maria"
    assert rows[0]["is_business"] == 0


def test_contacts_csv_skips_internal_system_entries():
    rows = parse_contacts_csv("Phone;Name;PushName;ShortName;IsBusiness\n0;WhatsApp;;WhatsApp;false\n5511999990000;Maria;;;false\n")
    assert len(rows) == 1
    assert rows[0]["phone"] == "5511999990000"


def test_image_viewer_supports_click_and_escape():
    javascript = (Path(__file__).parents[1] / "app/static/image-viewer.js").read_text(encoding="utf-8")
    assert ".message .media-card img" in javascript
    assert 'imageViewer.addEventListener("cancel"' in javascript
