import tempfile
import unittest
import zipfile
from base64 import b64decode
from pathlib import Path

from app import create_app, db
from app.config import Config
from app.models import ClassGroup, Flag, Session

PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ"
    "lS0X6WQAAAABJRU5ErkJggg=="
)


class ExportDocxTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        Config.UPLOAD_FOLDER = str(root / "uploads")
        Config.TESTING = True

        self.app = create_app()
        self.client = self.app.test_client()
        upload_path = Path(Config.UPLOAD_FOLDER) / "sample.png"
        upload_path.write_bytes(PNG_BYTES)
        with self.app.app_context():
            class_group = ClassGroup(name="Biology")
            db.session.add(class_group)
            db.session.flush()
            map_session = Session(name="Field notes", class_id=class_group.id)
            db.session.add(map_session)
            db.session.flush()
            note = Flag(
                session_id=map_session.id,
                region_id="region-1",
                x=37.12,
                y=127.45,
                text_content="Found a sample near the stream.",
                file_path="uploads/sample.png",
                author_name="Min",
            )
            db.session.add(note)
            db.session.commit()

        with self.client.session_transaction() as flask_session:
            flask_session["admin_logged_in"] = True

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    def test_export_zip_with_session_docx_and_attachments_when_admin_requests_export(self) -> None:
        response = self.client.get("/admin/export_docx")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/zip")
        self.assertIn("classmap_export_", response.headers["Content-Disposition"])
        self.assertIn(".zip", response.headers["Content-Disposition"])

        archive_path = Path(self.temp_dir.name) / "export.zip"
        archive_path.write_bytes(response.data)
        with zipfile.ZipFile(archive_path) as export_zip:
            names = export_zip.namelist()
            self.assertIn("Biology/", names)
            self.assertIn("Biology/Field notes/", names)
            self.assertIn("Biology/Field notes/Field notes.docx", names)
            self.assertIn("Biology/Field notes/sample.png", names)
            docx_bytes = export_zip.read("Biology/Field notes/Field notes.docx")

        docx_path = Path(self.temp_dir.name) / "session.docx"
        docx_path.write_bytes(docx_bytes)
        with zipfile.ZipFile(docx_path) as docx:
            docx_names = docx.namelist()
            self.assertIn("word/document.xml", docx_names)
            self.assertIn("word/media/image1.png", docx_names)
            self.assertIn("word/_rels/document.xml.rels", docx_names)
            document_xml = docx.read("word/document.xml").decode("utf-8")
            relationships_xml = docx.read("word/_rels/document.xml.rels").decode("utf-8")

        self.assertIn("ClassMap Export", document_xml)
        self.assertIn("Biology (Active)", document_xml)
        self.assertIn("Field notes (Active)", document_xml)
        self.assertIn("Min", document_xml)
        self.assertIn("Attachment: sample.png", document_xml)
        self.assertIn('r:embed="rId1"', document_xml)
        self.assertIn("Target=\"media/image1.png\"", relationships_xml)
        self.assertIn("Found a sample near the stream.", document_xml)
