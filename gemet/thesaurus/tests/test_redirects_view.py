from django_webtest import WebTest
from django.core.urlresolvers import reverse

from .factories import (
    LanguageFactory,
    NamespaceFactory,
)


class TestRedirectsView(WebTest):
    def setUp(self):
        LanguageFactory()

    def test_index_html(self):
        NamespaceFactory(heading='Themes')
        url = reverse('themes', kwargs={'langcode': 'en'})
        resp = self.app.get('/index_html')

        self.assertEqual(302, resp.status_int)
        self.assertRedirects(resp, url)

    def test_groups(self):
        url = reverse('groups', kwargs={'langcode': 'en'})
        resp = self.app.get('/groups')

        self.assertEqual(302, resp.status_int)
        self.assertRedirects(resp, url)
