# encoding=utf-8
import isodate
import xmlwitch

from roald.models.concepts import Concepts


class Marc21(object):
    """
    Class for exporting data as MARC21
    """

    agency = None  # Cataloguing agency 040 $a
    transcribingAgency = None  # Transcribing agency 040 $c
    modifyingAgency = None  # Modifying agency 040 $d
    vocabulary = None  # Vocabulary code, 040 $f
    defaultLanguage = None  # Default language code for 040 $b

    def __init__(self, concepts=None, agency=None, vocabulary=None, defaultLanguage=None):
        super(Marc21, self).__init__()
        self.agency = agency
        self.vocabulary = vocabulary
        self.defaultLanguage = defaultLanguage
        if concepts is not None:
            self.load(concepts)

    def load(self, data):
        if type(data) == dict:
            self.concepts = Concepts(data)
        elif type(data) == Concepts:
            self.concepts = data
        else:
            raise ValueError

    def serialize(self):

        # Make a dictionary of narrower concepts for fast lookup
        self.narrower = {}
        for c in self.concepts:
            for x in c.get('broader', []):
                self.narrower[x] = self.narrower.get(x, []) + [c['id']]

        builder = xmlwitch.Builder(version='1.0', encoding='utf-8')

        with builder.collection(xmlns='info:lc/xmlns/marcxchange-v1'):
            for concept in self.concepts:
                self.convert_concept(builder, concept, self.concepts)
        return str(builder)

    def global_cn(self, value):
        if self.agency is None:
            return value
        else:
            return '({}){}'.format(self.agency, value)

    def convert_concept(self, builder, concept, concepts):

        if concept.get('created'):
            created = isodate.parse_datetime(concept.get('created'))
        else:
            created = isodate.isodatetime.datetime.now()
        if concept.get('created') is None:
            modified = created
        else:
            modified = isodate.parse_datetime(concept.get('created'))

        # Loop over concept types
        for conceptType in concept.get('type'):

            if conceptType == 'VirtualCompoundHeading':
                continue

            with builder.record(xmlns='http://www.loc.gov/MARC21/slim', type='Authority'):

                # Fixed leader for all records
                # Ref: <http://www.loc.gov/marc/uma/pt8-11.html#pt8>
                leader = '00000nz  a2200000n  4500'
                builder.leader(leader)

                # 001 Control number
                builder.controlfield(concept.get('id'), tag='001')

                # 003 MARC code for the agency whose system control number is contained in field 001 (Control Number).
                if self.agency is not None:
                    builder.controlfield(self.agency, tag='003')

                # 005 Date of creation
                builder.controlfield(modified.strftime('%Y%m%d%H%M%S.0'), tag='005')

                # 008 Blablabla
                field008 = '{created}|||a|z||||||          || a||     d'.format(created=created.strftime('%y%m%d'))
                builder.controlfield(field008, tag='008')

                # 035 System control number ?
                # Her kan vi legge inn ID-er fra andre systemer, f.eks. BARE?
                # For eksempel, se XML-dataene fra WebDewey

                # 024 Other Standard Identifier
                with builder.datafield(tag='024', ind1='7', ind2=' '):
                    builder.subfield(concepts.uri(concept.get('id')), code='a')
                    builder.subfield('uri', code='2')

                # 040 Cataloging source
                with builder.datafield(tag='040', ind1=' ', ind2=' '):
                    if self.agency is not None:
                        builder.subfield(self.agency, code='a')     # Original cataloging agency
                    if self.defaultLanguage is not None:
                        builder.subfield(self.defaultLanguage, code='b')      # Language of cataloging
                    if self.transcribingAgency is not None:
                        builder.subfield(self.transcribingAgency, code='c')     # Transcribing agency
                    if self.modifyingAgency is not None:
                        builder.subfield(self.modifyingAgency, code='d')     # Modifying agency
                    if self.vocabulary is not None:
                        builder.subfield(self.vocabulary, code='f')  # Subject heading/thesaurus

                # 083 DDC number
                for value in concept.get('ddc', []):
                    with builder.datafield(tag='083', ind1='0', ind2='4'):
                        builder.subfield(value, code='a')

                # 148/150/151/155 Authorized heading
                if conceptType == 'CompoundHeading':

                    # Determine tag number based on the first component:
                    rel = concepts.by_id(concept.get('component')[0])
                    tag = {
                        'Temporal': '148',
                        'Topic': '150',
                        'Geographic': '151',
                        'GenreForm': '155',
                    }[rel['type'][0]]

                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):

                        # Add the first component. Always use subfield $a. Correct???
                        builder.subfield(rel['prefLabel']['nb'], code='a')

                        # Add remaining components
                        for value in concept.get('component')[1:]:
                            rel = concepts.by_id(value)

                            # Determine subfield code from type:
                            sf = {
                                'Topic': 'x',
                                'Temporal': 'y',
                                'Geographic': 'z',
                                'GenreForm': 'v',
                            }[rel['type'][0]]

                            # OBS! 150 har også $b.. Men når brukes egentlig den??
                            builder.subfield(rel['prefLabel']['nb'], code=sf)

                else:  # Not a compound heading
                    for lang, value in concept.get('prefLabel').items():
                        tag = {
                            'Temporal': '148',
                            'Topic': '150',
                            'Geographic': '151',
                            'GenreForm': '155',
                        }[conceptType]
                        if lang == 'nb':

                            # Always use subfield $a. Correct???
                            with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                                builder.subfield(value, code='a')

                    # Add 448/450/451/455 See from tracings
                    for lang, values in concept.get('altLabel', {}).items():
                        tag = {
                            'Temporal': '448',
                            'Topic': '450',
                            'Geographic': '451',
                            'GenreForm': '455',
                        }[conceptType]
                        if lang == 'nb':
                            for value in values:
                                with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                                    # Always use subfield $a. Correct???
                                    builder.subfield(value, code='a')
                    for value in concept.get('acronym', {}):
                        tag = {
                            'Temporal': '448',
                            'Topic': '450',
                            'Geographic': '451',
                            'GenreForm': '455',
                        }[conceptType]
                        with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                            builder.subfield(value, code='a')

                            # Heading in the tracing field is an acronym for the heading in the 1XX field.
                            # Ref: http://www.loc.gov/marc/authority/adtracing.html
                            builder.subfield('d', code='g')

                # 548/550/551/555 See also
                for value in concept.get('broader', []):
                    rel = concepts.by_id(value)
                    tag = {
                        'Temporal': '548',
                        'Topic': '550',
                        'Geographic': '551',
                        'GenreForm': '555',
                    }[rel['type'][0]]
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        builder.subfield(rel['prefLabel']['nb'], code='a')
                        builder.subfield('g', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                        builder.subfield(self.global_cn(value), code='0')

                for value in self.narrower.get(concept['id'], []):
                    rel = concepts.by_id(value)
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        builder.subfield(rel['prefLabel']['nb'], code='a')
                        builder.subfield('h', code='w')  # Ref: http://www.loc.gov/marc/authority/adtracing.html
                        builder.subfield(self.global_cn(value), code='0')

                for value in concept.get('related', []):
                    rel = concepts.by_id(value)
                    tag = {
                        'Temporal': '548',
                        'Topic': '550',
                        'Geographic': '551',
                        'GenreForm': '555',
                    }[rel['type'][0]]
                    with builder.datafield(tag=tag, ind1=' ', ind2=' '):
                        builder.subfield(rel['prefLabel']['nb'], code='a')
                        builder.subfield(self.global_cn(value), code='0')

                # 680 Notes
                for value in concept.get('note', []):
                    with builder.datafield(tag='680', ind1=' ', ind2=' '):
                        builder.subfield(value, code='i')
