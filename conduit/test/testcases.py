from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory


class ConduitTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ConduitTestCase, cls).setUpClass()
        cls.client = Client()
        cls.factory = RequestFactory()
