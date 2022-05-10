import io
import logging
import tempfile
import time
from pathlib import PurePath

from django.core.management import call_command
from django.http import FileResponse
from qfieldcloud.authentication.models import AuthToken
from qfieldcloud.core import utils
from qfieldcloud.core.models import Job, ProcessProjectfileJob, Project, User
from qfieldcloud.subscription.models import AccountType
from rest_framework import status
from rest_framework.test import APITransactionTestCase

from .utils import get_filename, testdata_path

logging.disable(logging.CRITICAL)


class QfcTestCase(APITransactionTestCase):
    def setUp(self):
        # Create a user
        self.user1 = User.objects.create_user(username="user1", password="abc123")
        self.user1.save()

        self.user2 = User.objects.create_user(username="user2", password="abc123")
        self.user2.save()

        self.token1 = AuthToken.objects.get_or_create(user=self.user1)[0]

        # Create a project
        self.project1 = Project.objects.create(
            name="project1", is_public=False, owner=self.user1
        )
        self.project1.save()

    def get_file_contents(self, project, filename, version=None):
        qs = ""
        if version:
            qs = f"?version={version}"

        response = self.client.get(f"/api/v1/files/{project.id}/{filename}/{qs}")

        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(get_filename(response), PurePath(filename).name)

        if isinstance(response, FileResponse):
            return b"".join(response.streaming_content)
        else:
            return response.content

    def test_push_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

    def test_push_download_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        self.assertEqual(
            self.get_file_contents(self.project1, "file.txt"),
            open(testdata_path("file.txt"), "rb").read(),
        )

    def test_push_download_file_with_path(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/foo/bar/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # Pull the file
        response = self.client.get(
            f"/api/v1/files/{self.project1.id}/foo/bar/file.txt/",
            stream=True,
        )

        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(get_filename(response), "file.txt")

        self.assertEqual(
            self.get_file_contents(self.project1, "foo/bar/file.txt"),
            open(testdata_path("file.txt"), "rb").read(),
        )

    def test_push_list_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/aaa/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        file_path = testdata_path("file2.txt")
        # Push a second file
        response = self.client.post(
            "/api/v1/files/{}/file2.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 2)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))

        json = response.json()
        json = sorted(json, key=lambda k: k["name"])

        self.assertEqual(json[0]["name"], "aaa/file.txt")
        self.assertEqual(json[0]["size"], 13)
        self.assertEqual(json[1]["name"], "file2.txt")
        self.assertEqual(json[1]["size"], 13)
        self.assertEqual(
            json[0]["sha256"],
            "8663bab6d124806b9727f89bb4ab9db4cbcc3862f6bbf22024dfa7212aa4ab7d",
        )
        self.assertEqual(
            json[1]["sha256"],
            "fcc85fb502bd772aa675a0263b5fa665bccd5d8d93349d1dbc9f0f6394dd37b9",
        )

    def test_push_list_file_with_space_in_name(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        project_file = "aaa bbb/project qgis 1.2.qgs"
        response = self.client.post(
            f"/api/v1/files/{self.project1.id}/{project_file}/",
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, project_file
        )

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))

        json = response.json()

        self.assertEqual(json[0]["name"], "aaa bbb/project qgis 1.2.qgs")

    def test_push_list_file_versions(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/aaa/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # Wait 2 seconds to be sure the file timestamps are different
        time.sleep(2)

        file_path = testdata_path("file2.txt")
        # Push another file with the same name (i.e. push another
        # version)
        response = self.client.post(
            "/api/v1/files/{}/aaa/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))

        versions = sorted(
            response.json()[0]["versions"], key=lambda k: k["last_modified"]
        )

        self.assertEqual(len(versions), 2)
        self.assertNotEqual(versions[0]["last_modified"], versions[1]["last_modified"])

        self.assertEqual(
            versions[0]["sha256"],
            "8663bab6d124806b9727f89bb4ab9db4cbcc3862f6bbf22024dfa7212aa4ab7d",
        )
        self.assertEqual(
            versions[1]["sha256"],
            "fcc85fb502bd772aa675a0263b5fa665bccd5d8d93349d1dbc9f0f6394dd37b9",
        )

        self.assertEqual(versions[0]["size"], 13)
        self.assertEqual(versions[1]["size"], 13)

    def test_push_download_specific_version_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # Wait 2 seconds to be sure the file timestamps are different
        time.sleep(2)

        file_path = testdata_path("file2.txt")
        # Push another file with the same name (i.e. push another
        # version)
        response = self.client.post(
            "/api/v1/files/{}/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        self.assertNotEqual(
            self.get_file_contents(self.project1, "file.txt"),
            open(testdata_path("file.txt"), "rb").read(),
        )

        self.assertEqual(
            self.get_file_contents(self.project1, "file.txt"),
            open(testdata_path("file2.txt"), "rb").read(),
        )

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))

        versions = sorted(
            response.json()[0]["versions"], key=lambda k: k["last_modified"]
        )

        # Pull the oldest version
        self.assertEqual(
            self.get_file_contents(
                self.project1, "file.txt", versions[0]["version_id"]
            ),
            open(testdata_path("file.txt"), "rb").read(),
        )

        # Pull the newest version
        self.assertEqual(
            self.get_file_contents(
                self.project1, "file.txt", versions[1]["version_id"]
            ),
            open(testdata_path("file2.txt"), "rb").read(),
        )

    def test_push_delete_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        # Push a file
        response = self.client.post(
            "/api/v1/files/{}/aaa/file.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        file_path = testdata_path("file2.txt")
        # Push a second file
        response = self.client.post(
            "/api/v1/files/{}/file2.txt/".format(self.project1.id),
            {"file": open(file_path, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 2)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(len(response.json()), 2)

        # Delete a file
        response = self.client.delete(
            "/api/v1/files/{}/aaa/file.txt/".format(self.project1.id)
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(len(response.json()), 1)

    def test_one_qgis_project_per_project(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        qgis_project_file = "foo/bar/file.qgs"
        # Push a QGIS project file
        response = self.client.post(
            f"/api/v1/files/{self.project1.id}/{qgis_project_file}/",
            {
                "file": open(file_path, "rb"),
            },
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename,
            qgis_project_file,
        )

        # Push again the same QGIS project file (this is allowed)
        response = self.client.post(
            f"/api/v1/files/{self.project1.id}/{qgis_project_file}/",
            {
                "file": open(file_path, "rb"),
            },
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename,
            qgis_project_file,
        )

        failing_qgis_project_file = "foo/bar/file2.qgs"
        # Push another QGIS project file
        response = self.client.post(
            f"/api/v1/files/{self.project1.id}/{failing_qgis_project_file}/",
            {
                "file": open(file_path, "rb"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename,
            qgis_project_file,
        )

        # Push another QGIS project file
        response = self.client.post(
            "/api/v1/files/{}/foo/bar/file2.qgz/".format(self.project1.id),
            {
                "file": open(file_path, "rb"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename,
            qgis_project_file,
        )

        response = self.client.delete(
            f"/api/v1/files/{self.project1.id}/{qgis_project_file}/",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

    def test_upload_1mb_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        big_file = tempfile.NamedTemporaryFile()
        with open(big_file.name, "wb") as bf:
            bf.truncate(1024 * 1024 * 1)

        # Push the file
        response = self.client.post(
            "/api/v1/files/{}/bigfile.big/".format(self.project1.id),
            data={"file": open(big_file.name, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))

        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(len(response.json()), 1)
        self.assertEqual("bigfile.big", response.json()[0]["name"])
        self.assertGreater(response.json()[0]["size"], 1000000)
        self.assertLess(response.json()[0]["size"], 1100000)

    def test_upload_10mb_file(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        big_file = tempfile.NamedTemporaryFile()
        with open(big_file.name, "wb") as bf:
            bf.truncate(1024 * 1024 * 10)

        # Push the file
        response = self.client.post(
            "/api/v1/files/{}/bigfile.big/".format(self.project1.id),
            data={"file": open(big_file.name, "rb")},
            format="multipart",
        )
        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 1)

        # List files
        response = self.client.get("/api/v1/files/{}/".format(self.project1.id))

        self.assertTrue(status.is_success(response.status_code))
        self.assertEqual(len(response.json()), 1)
        self.assertEqual("bigfile.big", response.json()[0]["name"])
        self.assertGreater(response.json()[0]["size"], 10000000)
        self.assertLess(response.json()[0]["size"], 11000000)

    def test_purge_old_versions_command(self):
        """This tests manual purging of old versions with the management command"""

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        acctype_3 = AccountType.objects.create(storage_keep_versions=3, code="acc3")
        self.user1.useraccount.account_type = acctype_3
        self.user1.useraccount.save()

        def count_versions():
            """counts the versions in first file of project1"""
            file = list(self.project1.files)[0]
            return len(file.versions)

        def read_version(n):
            """returns the content of version in first file of project1"""
            file = list(self.project1.files)[0]
            return file.versions[n]._data.get()["Body"].read().decode()

        # Create 20 versions (direct upload to s3)
        bucket = utils.get_s3_bucket()
        key = f"projects/{self.project1.id}/files/file.txt/"
        for i in range(20):
            test_file = io.BytesIO(f"v{i}".encode())
            bucket.upload_fileobj(test_file, key)

        # Ensure it worked
        self.assertEqual(count_versions(), 20)
        self.assertEqual(read_version(0), "v0")
        self.assertEqual(read_version(19), "v19")

        # Run management command on other project should have no effect
        other = Project.objects.create(name="other", owner=self.user1)
        call_command("purge_old_file_versions", "--force", "--projects", other.pk)
        self.assertEqual(count_versions(), 20)

        # Run management command should leave 3
        call_command("purge_old_file_versions", "--force")
        self.assertEqual(count_versions(), 3)
        self.assertEqual(read_version(0), "v17")
        self.assertEqual(read_version(2), "v19")

        # Run management command is idempotent
        call_command("purge_old_file_versions", "--force")
        self.assertEqual(count_versions(), 3)
        self.assertEqual(read_version(0), "v17")
        self.assertEqual(read_version(2), "v19")

    def test_purge_old_versions(self):
        """This tests automated purging of old versions when uploading files"""

        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        apipath = f"/api/v1/files/{self.project1.id}/file.txt/"

        def count_versions():
            """counts the versions in first file of project1"""
            file = list(self.project1.files)[0]
            return len(file.versions)

        def read_version(n):
            """returns the content of version in first file of project1"""
            file = list(self.project1.files)[0]
            return file.versions[n]._data.get()["Body"].read().decode()

        # As PRO account, 10 version should be kept out of 20
        acctype_10 = AccountType.objects.create(storage_keep_versions=10, code="acc10")
        self.user1.useraccount.account_type = acctype_10
        self.user1.useraccount.save()
        for i in range(20):
            test_file = io.StringIO(f"v{i}")
            self.client.post(apipath, {"file": test_file}, format="multipart")
        self.assertEqual(count_versions(), 10)
        self.assertEqual(read_version(0), "v10")
        self.assertEqual(read_version(9), "v19")

        # As COMMUNITY account, 3 version should be kept
        acctype_3 = AccountType.objects.create(storage_keep_versions=3, code="acc3")
        self.user1.useraccount.account_type = acctype_3
        self.user1.useraccount.save()

        # But first we check that uploading to another project doesn't affect a projct
        otherproj = Project.objects.create(name="other", owner=self.user1)
        otherpath = f"/api/v1/files/{otherproj.id}/file.txt/"
        self.client.post(otherpath, {"file": io.StringIO("v1")}, format="multipart")
        self.assertEqual(count_versions(), 10)
        self.assertEqual(read_version(0), "v10")
        self.assertEqual(read_version(9), "v19")

        # As COMMUNITY account, 3 version should be kept out of 20 new ones
        for i in range(20, 40):
            test_file = io.StringIO(f"v{i}")
            self.client.post(apipath, {"file": test_file}, format="multipart")
        self.assertEqual(count_versions(), 3)
        self.assertEqual(read_version(0), "v37")
        self.assertEqual(read_version(2), "v39")

    def test_multiple_file_uploads_one_process_job(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token1.key)

        self.assertEqual(Project.objects.get(pk=self.project1.pk).files_count, 0)
        self.assertEqual(
            Project.objects.get(pk=self.project1.pk).project_filename, None
        )

        file_path = testdata_path("file.txt")
        qgis_project_file = "foo/bar/file.qgs"

        for i in range(10):
            # Push a QGIS project file
            response = self.client.post(
                f"/api/v1/files/{self.project1.id}/{qgis_project_file}/",
                {
                    "file": open(file_path, "rb"),
                },
                format="multipart",
            )
            self.assertTrue(status.is_success(response.status_code))

        jobs = ProcessProjectfileJob.objects.filter(
            project=self.project1,
            status__in=[Job.Status.PENDING, Job.Status.QUEUED, Job.Status.STARTED],
        )

        self.assertEqual(jobs.count(), 1)
