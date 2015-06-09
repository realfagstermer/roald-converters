# encoding=utf-8
from __future__ import print_function
import unittest
from lxml import etree
from StringIO import StringIO
import pytest

from roald.models.concepts import Concepts


class TestConverter(unittest.TestCase):

    def test_set_type(self):
        concepts = Concepts()
        concepts.load({
            'REAL012789': {
                'id': 'REAL012789',
                'prefLabel': {'nb': 'Fornybar energi'}
            },
            'REAL013995': {
                'id': 'REAL013995',
                'prefLabel': {'nb': 'Livssyklusanalyse'}
            },
            'REAL022146': {
                'id': 'REAL022146',
                'component': ['REAL012789', 'REAL013995']
            }
        })
        self.assertEqual('REAL012789', concepts.by_term('Fornybar energi')['id'])
        self.assertEqual('REAL013995', concepts.by_term('Livssyklusanalyse')['id'])
        self.assertEqual('REAL022146', concepts.by_term('Fornybar energi : Livssyklusanalyse')['id'])
