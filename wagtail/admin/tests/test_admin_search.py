"""
Tests for the search box in the admin side menu, and the custom search hooks.
"""
from django.contrib.auth.models import Permission
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse

from wagtail.tests.utils import WagtailTestUtils
from wagtail.admin.utils import user_has_any_page_permission
from wagtail.core.models import Site


class BaseSearchAreaTestCase(WagtailTestUtils, TestCase):
    rf = RequestFactory()

    def search_other(self, current_url='/admin/', data=None):
        request = self.rf.get(current_url, data=data)
        request.user = self.user
        request.site = Site.objects.get()
        template = Template("{% load wagtailadmin_tags %}{% search_other %}")
        return template.render(Context({'request': request}))

    def menu_search(self, current_url='/admin/', data=None):
        request = self.rf.get(current_url, data=data)
        request.user = self.user
        request.site = Site.objects.get()
        template = Template("{% load wagtailadmin_tags %}{% menu_search %}")
        return template.render(Context({'request': request}))


class TestSearchAreas(BaseSearchAreaTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.login()

    def test_other_searches(self):
        search_url = reverse('wagtailadmin_pages:search')
        query = "Hello"
        base_css = "icon icon-custom"
        test_string = '<a href="/customsearch/?q=%s" class="%s" is-custom="true">My Search</a>'
        # Testing the option link exists
        response = self.client.get(search_url, {'q': query})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')
        self.assertTemplateUsed(response, 'wagtailadmin/shared/search_area.html')
        self.assertTemplateUsed(response, 'wagtailadmin/shared/search_other.html')
        self.assertContains(response, test_string % (query, base_css), html=True)

        # Testing is_shown
        response = self.client.get(search_url, {'q': query, 'hide-option': "true"})
        self.assertNotContains(response, test_string % (query, base_css), status_code=200, html=True)

        # Testing is_active
        response = self.client.get(search_url, {'q': query, 'active-option': "true"})
        self.assertContains(response, test_string % (query, base_css + " nolink"), status_code=200, html=True)

    def test_menu_search(self):
        rendered = self.menu_search()
        self.assertIn(reverse('wagtailadmin_pages:search'), rendered)

    def test_search_other(self):
        rendered = self.search_other()
        self.assertIn(reverse('wagtailadmin_pages:search'), rendered)
        self.assertIn('/customsearch/', rendered)

        self.assertIn('Pages', rendered)
        self.assertIn('My Search', rendered)


class TestSearchAreaNoPagePermissions(BaseSearchAreaTestCase):
    """
    Test the admin search when the user does not have permission to manage
    pages. The search bar should show the first available search area instead.
    """
    def setUp(self):
        self.user = self.login()
        self.assertFalse(user_has_any_page_permission(self.user))

    def create_test_user(self):
        user = super().create_test_user()
        user.is_superuser = False
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        user.save()
        return user

    def test_dashboard(self):
        """
        Check that the menu search area on the dashboard is not searching
        pages, as they are not allowed.
        """
        response = self.client.get('/admin/')
        # The menu search bar should go to /customsearch/, not /admin/pages/search/
        self.assertNotContains(response, reverse('wagtailadmin_pages:search'))
        self.assertContains(response, 'action="/customsearch/"')

    def test_menu_search(self):
        """
        The search form should go to the custom search, not the page search.
        """
        rendered = self.menu_search()
        self.assertNotIn(reverse('wagtailadmin_pages:search'), rendered)
        self.assertIn('action="/customsearch/"', rendered)

    def test_search_other(self):
        """The pages search link should be hidden."""
        rendered = self.search_other()
        self.assertNotIn(reverse('wagtailadmin_pages:search'), rendered)
        self.assertIn('/customsearch/', rendered)

        self.assertNotIn('Pages', rendered)
        self.assertIn('My Search', rendered)

    def test_no_searches(self):
        rendered = self.menu_search(data={'hide-option': 'true'})
        self.assertEqual(rendered, '')
