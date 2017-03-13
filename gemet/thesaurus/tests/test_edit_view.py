from django.core.urlresolvers import reverse

from .factories import ForeignRelation, ForeignRelationFactory
from .factories import LanguageFactory, Property, PropertyFactory
from .factories import PropertyTypeFactory, RelationFactory, Relation
from .factories import TermFactory, ThemeFactory
from . import GemetTest
import json


class TestEditPropertyView(GemetTest):

    csrf_checks = False

    def setUp(self):
        self.language = LanguageFactory()
        self.concept = TermFactory()
        self.request_kwargs = {'langcode': self.language.code,
                               'id': self.concept.id,
                               'name': 'prefLabel'}

    def test_edit_property_bad_concept(self):

        url = reverse('edit_property',  kwargs={'langcode': 'en',
                                                'id': 43,
                                                'name': 'prefLabel'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_edit_property_bad_language(self):
        url = reverse('edit_property', kwargs={'langcode': 'abc',
                                               'id': self.concept.id,
                                               'name': 'prefLabel'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_edit_property_request_no_value(self):
        url = reverse('edit_property', kwargs=self.request_kwargs)
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_edit_property_correct_request(self):
        url = reverse('edit_property', kwargs=self.request_kwargs)
        response = self.app.post(url, params={'value': 'name1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.body)['value'], 'name1')
        new_property = self.concept.properties.first()
        self.assertIsNotNone(new_property)
        self.assertEquals(new_property.name, 'prefLabel')
        self.assertEquals(new_property.value, 'name1')
        self.assertEquals(new_property.status, Property.PENDING)

    # todo test behaviour if a property with that name is already defined


class TestAddPropertyView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.language = LanguageFactory()
        self.concept = TermFactory()
        self.request_kwargs = {'langcode': self.language.code,
                               'id': self.concept.id,
                               'name': 'prefLabel'}

    def test_add_property_bad_concept(self):
        url = reverse('add_property', kwargs={'langcode': 'en',
                                              'id': 43,
                                              'name': 'prefLabel'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_add_property_bad_language(self):
        url = reverse('add_property', kwargs={'langcode': 'abc',
                                              'id': self.concept.id,
                                              'name': 'prefLabel'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_add_property_request_no_value(self):
        url = reverse('add_property', kwargs=self.request_kwargs)
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_add_property_correct_request(self):
        url = reverse('add_property', kwargs=self.request_kwargs)
        response = self.app.post(url, params={'value': 'name1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.body)['value'], 'name1')
        new_property = self.concept.properties.first()
        self.assertIsNotNone(new_property)
        self.assertEquals(new_property.name, 'prefLabel')
        self.assertEquals(new_property.value, 'name1')
        self.assertEquals(new_property.status, Property.PENDING)


class TestRemoveParentRelationView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.term = TermFactory()
        self.theme = ThemeFactory()
        self.property_type = PropertyTypeFactory(label='Theme', name='theme')
        self.request_kwargs = {'source_id': self.term.id,
                               'target_id': self.theme.id,
                               'relation_type': 'theme'}

    def test_delete_relation_bad_concept(self):
        url = reverse('delete_relation', kwargs={'source_id': 31,
                                                 'target_id': self.theme.id,
                                                 'relation_type': 'theme'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete_relation_bad_parent(self):
        url = reverse('delete_relation', kwargs={'source_id': self.term.id,
                                                 'target_id': 99,
                                                 'relation_type': 'theme'})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete_relation_no_relation(self):
        url = reverse('delete_relation', kwargs=self.request_kwargs)
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete_relation_correct_request(self):
        url = reverse('delete_relation', kwargs=self.request_kwargs)
        RelationFactory(source=self.term, target=self.theme,
                        property_type=self.property_type,
                        status=Property.PUBLISHED)
        response = self.app.post(url)
        self.assertEqual(200, response.status_code)
        relation = Relation.objects.get(source=self.term, target=self.theme,
                                        property_type=self.property_type)
        self.assertEqual(relation.status, Property.DELETED_PENDING)
        # todo could test for status=pending when the behaviour will differ


class TestAddParentRelationView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.language = LanguageFactory()
        self.term = TermFactory()
        self.theme = ThemeFactory()
        self.property = PropertyFactory(language=self.language,
                                        concept=self.theme,
                                        name='prefLabel',
                                        value='Theme 1',
                                        status=Property.PUBLISHED)
        self.property_type = PropertyTypeFactory(label='Theme',
                                                 name='theme', id=10)

    def test_post_no_concept_no_parent_object(self):
        url = reverse('add_relation', kwargs={'source_id': 33,
                                              'target_id': 45,
                                              'relation_type': 'theme'})

        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_post_correct_request(self):
        url = reverse('add_relation', kwargs={'source_id': self.term.id,
                                              'target_id': self.theme.id,
                                              'relation_type': 'theme'})

        response = self.app.post(url, expect_errors=True)
        self.assertEqual(200, response.status_code)


class TestRemovePropertyView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.property = PropertyFactory(value='new property',
                                        status=Property.PUBLISHED)

    def test_delete_property_bad_concept(self):
        url = reverse('delete_property', kwargs={'pk': 43})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete_property_correct_request(self):
        url = reverse('delete_property', kwargs={'pk': self.property.pk})
        response = self.app.post(url, params={'value': 'new property'})
        self.assertEqual(200, response.status_code)

        prop = Property.objects.get(pk=self.property.pk)
        self.assertEqual(prop.status, Property.DELETED_PENDING)


class TestAddForeignRelationView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.property_type1 = PropertyTypeFactory(label='has exact Match',
                                                  name='exactMatch', id=10)
        self.property_type2 = PropertyTypeFactory(label='has close Match',
                                                  name='closeMatch', id=20)
        self.lang = LanguageFactory()
        self.concept = TermFactory()

    def test_post_bad_request(self):
        url = reverse('add_other', kwargs={'id': 10})
        response = self.app.post(url, expect_errors=True,
                                 params={'rel_type': 10})
        self.assertEqual(400, response.status_code)

    def test_post_bad_form(self):
        url = reverse('add_other', kwargs={'id': 1})
        response = self.app.post(url, expect_errors=True,
                                 params={'rel_type': 10})
        self.assertEqual(400, response.status_code)

    def test_post_correct_request(self):
        url = reverse('add_other', kwargs={'id': 1})
        response = self.app.post(url, expect_errors=True,
                                 params={'uri': 'Uri', 'rel_type': 10,
                                         'label': 'Label'})
        self.assertEqual(200, response.status_code)
        data = json.loads(response.body)
        foreign_relation = ForeignRelation.objects.get(
            concept=self.concept, property_type=self.property_type1)
        self.assertEqual(foreign_relation.id, data['id'])


class TestRemoveForeignRelationView(GemetTest):
    csrf_checks = False

    def setUp(self):
        self.term = TermFactory()
        self.property_type = PropertyTypeFactory(label='Theme', name='theme')
        self.foreign_relation = ForeignRelationFactory(
            concept=self.term, property_type=self.property_type, id=8)

    def test_delete_foreign_relation_no_relation(self):
        url = reverse('delete_other', kwargs={'pk': 7})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(400, response.status_code)

    def test_delete_foreign_relation_correct_request(self):
        url = reverse('delete_other', kwargs={'pk': 8})
        response = self.app.post(url, expect_errors=True)
        self.assertEqual(200, response.status_code)
        foreign_relation = ForeignRelation.objects.get(id=8)
        self.assertEqual(foreign_relation.status, Property.DELETED_PENDING)
