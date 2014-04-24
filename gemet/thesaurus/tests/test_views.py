from django_webtest import WebTest
from django.core.urlresolvers import reverse

from .factories import (
    ConceptFactory,
    PropertyFactory,
    LanguageFactory,
    NamespaceFactory,
    RelationFactory,
    PropertyTypeFactory,
)


class TestThemesView(WebTest):

    def setUp(self):
        LanguageFactory()
        NamespaceFactory()

    def test_no_theme(self):
        url = reverse('themes', kwargs={'langcode': 'en'})
        resp = self.app.get(url)

        self.assertEqual(200, resp.status_int)
        self.assertEqual(resp.context['langcode'], 'en')
        self.assertQuerysetEqual(resp.context['themes'], [])
        self.assertEqual(resp.html.body.ul.text, '\n')

    def test_one_theme(self):
        ConceptFactory()
        PropertyFactory()

        url = reverse('themes', kwargs={'langcode': 'en'})
        resp = self.app.get(url)

        self.assertEqual(200, resp.status_int)
        self.assertEqual(resp.context['langcode'], 'en')
        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .li.a.get('href'),
                         u'{url}'.format(url=reverse('theme_concepts',
                                                     kwargs={'langcode': 'en',
                                                             'theme_id': 1}))
                         )
        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .li.a.text,
                         u'administration'
                         )

    def test_contains_more_themes(self):
        ConceptFactory()
        PropertyFactory()
        ConceptFactory(id=2,
                       code="2",
                       namespace_id=4
                       )
        PropertyFactory(concept_id=2,
                        value="agriculture",
                        )

        url = reverse('themes', kwargs={'langcode': 'en'})
        resp = self.app.get(url)

        self.assertEqual(200, resp.status_int)
        self.assertEqual(resp.context['langcode'], 'en')

        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .find_all('li')[0].a.get('href'),
                         u'{url}'.format(url=reverse('theme_concepts',
                                                     kwargs={'langcode': 'en',
                                                             'theme_id': 1}))
                         )
        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .find_all('li')[0].a.text,
                         u'administration'
                         )
        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .find_all('li')[1].a.get('href'),
                         u'{url}'.format(url=reverse('theme_concepts',
                                                     kwargs={'langcode': 'en',
                                                             'theme_id': 2}))
                         )
        self.assertEqual(resp.html.find_all('ul', {'class': 'themes'})[0]
                         .find_all('li')[1].a.text,
                         u'agriculture'
                         )


class TestThemeConceptsView(WebTest):

    def setUp(self):
        LanguageFactory()
        NamespaceFactory()

    def test_one_theme_concept(self):
        NamespaceFactory(id=1, heading="Concepts")

        ConceptFactory()
        PropertyFactory()
        ConceptFactory(id=2,
                       code="2",
                       namespace_id=1
                       )
        PropertyFactory(concept_id=2,
                        value="access to administrative documents"
                        )
        PropertyTypeFactory(id=1)
        RelationFactory(property_type_id=1,
                        source_id=1,
                        target_id=2
                        )

        url = reverse('theme_concepts',
                      kwargs={'langcode': 'en', 'theme_id': 1})
        resp = self.app.get(url)

        self.assertEqual(200, resp.status_int)
        self.assertEqual(resp.context['langcode'], 'en')

        """
        self.assertEqual(resp.html.find_all('ul', {'class': 'concepts'})[0]
                         .find_all('li')[0].a.get('href'),
                         u'{url}'.format(url=reverse('theme_concepts',
                                                     kwargs={'langcode': 'en',
                                                             'theme_id': 1}))
                         )
        """
        import pdb
        pdb.set_trace()

        self.assertEqual(resp.html.find_all('ul', {'class': 'concepts'})[0]
                         .li.text,
                         u'administration')
