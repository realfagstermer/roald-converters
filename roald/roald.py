# encoding=utf-8
import codecs
import json
import os

from .models import Roald2
from .models import Marc21
from .models import Skos
from .models import Concepts


class Roald(object):
    """
    Roald

    Example:

    >>> roald = roald.Roald()
    >>> roald.importRoald2()
    >>> roald.save('realfagstermer.json')
    >>> roald.exportMarc21('realfagstermer.marc21.xml')
    """

    def __init__(self):
        super(Roald, self).__init__()
        self.concepts = Concepts()

    def load(self, filename, format='roald3'):
        """
            - filename : the filename to a 'roald3' file or path to a 'roald2' directory.
            - format : 'roald3' or 'roald2'.
        """
        filename = os.path.expanduser(filename)
        if format == 'roald3':
            data = json.load(codecs.open(filename, 'r', 'utf-8'))
            self.concepts.load(data['concepts'])
        elif format == 'roald2':
            self.concepts.load(Roald2().read(filename))
        else:
            raise ValueError('Unknown format')

    def save(self, filename):
        filename = os.path.expanduser(filename)
        data = {
            'concepts': self.concepts.get()
        }
        json.dump(data, codecs.open(filename, 'w', 'utf-8'), indent=2)

    def export(self, filename, format, **kwargs):
        filename = os.path.expanduser(filename)
        if format == 'marc21':
            m21 = Marc21(self.concepts, **kwargs)
            with open(filename, 'w') as f:
                f.write(m21.serialize())
        elif format == 'rdfskos':
            skos = Skos(self.concepts, **kwargs)
            # with open(filename, 'w') as f:
            #     f.write(skos.convert(self.concepts))

    def authorize(self, value):
        # <value> can take a compound heading value like "$a Component1 $x Component2 $x Component3"
        return self.concepts.get(term=value)
        # parts = [[x.strip()[0], x.strip()[1:].strip()] for x in value.split('$') if len(x.strip()) > 0]
        # for part in parts:
