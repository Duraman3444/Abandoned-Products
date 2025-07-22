from django.urls import reverse
from django.test import TestCase, Client


class CSVExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("dashboard_csv_export")

    def test_csv_download_success(self):
        resp = self.client.get(self.url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "attachment;" in resp["Content-Disposition"]
        # header row + >= 0 data rows (even if no applicants)
        assert resp.content.count(b"\n") >= 1
