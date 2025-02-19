from functools import reduce
import operator
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.test import TestCase, override_settings
from accounts.models import User


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class OsquerySetupViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("godzilla", "godzilla@zentral.io", get_random_string())
        cls.group = Group.objects.create(name=get_random_string())
        cls.user.groups.set([cls.group])

    # utiliy methods

    def _login_redirect(self, url):
        response = self.client.get(url)
        self.assertRedirects(response, "{u}?next={n}".format(u=reverse("login"), n=url))

    def _login(self, *permissions):
        if permissions:
            permission_filter = reduce(operator.or_, (
                Q(content_type__app_label=app_label, codename=codename)
                for app_label, codename in (
                    permission.split(".")
                    for permission in permissions
                )
            ))
            self.group.permissions.set(list(Permission.objects.filter(permission_filter)))
        else:
            self.group.permissions.clear()
        self.client.force_login(self.user)

    # index

    def test_index_redirect(self):
        self._login_redirect(reverse("osquery:index"))

    def test_index_permission_denied(self):
        self._login()
        response = self.client.get(reverse("osquery:index"))
        self.assertEqual(response.status_code, 403)

    def test_index(self):
        self._login("osquery.view_configuration")
        response = self.client.get(reverse("osquery:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "osquery/index.html")
