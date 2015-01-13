# Innoslate XML parser copyright (c) 2014 by Francois Malan francois@scs-space.com
# Extracts CSV files from the SKA SDP Innoslate project's exported XML

# This script is written to be run in Python 2.x (Tested in 2.7)

import sys
import csv
from xml.dom import minidom
from HTMLParser import HTMLParser

ID_requirement = 'C1Z'
ID_action = 'C1'
ID_asset = 'C8'

ID_Status   = 'P3q6z'
ID_Priority = 'Pjfa'

ID_REL_Satisfies     = 'R4N'
ID_REL_Satisfied_by  = 'R4M'
ID_REL_Decomposes    = 'R30'
ID_REL_Decomposed_by = 'R2Z'
ID_REL_Sourced_by    = 'R4T'
ID_REL_Receives_IO   = 'R44'

#HTML stripping
# developed from http://stackoverflow.com/questions/11061058/using-htmlparser-in-python-3-2
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    """
       Function to strip tags and remove leading and trailing white
       space and remove most of the paragraph gaps.
    """
    s = MLStripper()
    s.feed(html)
    return s.get_data().strip().replace('\n\n', '').replace('\t', ' ')

#/HTML stripping


def usage():
    print("usage: python parse_innoslate_xml source_file_name")


class Requirement():
    id = ""
    name = ""
    description = ""
    number = ""
    status = ""
    priority = ""
    labels = []

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return 'Requirement. id=%s, number=%s, name=%s, labels=%s' % (
            self.id, self.number, self.name, str(len(self.labels)))


class Action():
    id = ""
    name = ""
    description = ""
    number = ""
    labels = []

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return 'Action. id=%s, number=%s, name=%s, labels=%s' % (self.id, self.number, self.name, str(len(self.labels)))

class Asset():
    id = ""
    name = ""
    number = ""
    description = ""

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return 'Asset. id=%s, number=%s, name=%s, labels=%s' % (self.id, self.number, self.name, str(len(self.labels)))

class Relationship():
    source = ""
    target = ""
    reltype = ""

    def __init__(self):
        pass

    def __repr__(self):
        return 'Relationship: %s -> %s' % (self.source, self.target)

class Label():
    id = ""
    name = ""
    description = ""

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return 'Label: %s' % self.name


def parse_it(source_file_name):
    """
    Parses the CSV file that was exported from Innoslate
    @param source_file_name:
    """
    xml_obj = minidom.parse(source_file_name)

    requirements = {}
    actions = {}
    assets = {}
    entities = {} # Requirements, Actions and Assets

    # Parse all Requirements and Actions (these are both represented by type 'entity')
    Topic = xml_obj.getElementsByTagName('entity')
    for node in Topic:
        new_entity = None
        for child in node.childNodes:
            # Any kind of 'entity'. Read the schemaClassId to determine its type
            if child.localName == 'schemaClassId':
                if child.childNodes[0].nodeValue == ID_requirement:
                    id = node.attributes['id'].nodeValue
                    new_entity = Requirement(id)
                    break
                elif child.childNodes[0].nodeValue == ID_action:
                    id = node.attributes['id'].nodeValue
                    new_entity = Action(id)
                    break
                elif child.childNodes[0].nodeValue == ID_asset:
                    id = node.attributes['id'].nodeValue
                    new_entity = Asset(id)
                    break

        if new_entity is not None:
            if isinstance(new_entity, Requirement) or isinstance(new_entity, Action) or isinstance(new_entity, Asset):
                new_entity.labels = []
                for child in node.childNodes:
                    if child.localName == 'name':
                        new_entity.name = child.childNodes[0].nodeValue
                    elif child.localName == 'description':
                        if child.childNodes is not None and len(child.childNodes) > 0:
                            new_entity.description = child.childNodes[0].nodeValue
                    elif child.localName == 'number':
                        new_entity.number = child.childNodes[0].nodeValue
                    elif child.localName == 'labelId':
                        new_entity.labels.append(child.childNodes[0].nodeValue)
                    elif child.localName == 'stringAttribute':
                        assert isinstance(new_entity, Requirement)
                        if child.attributes['schemaPropertyId'].nodeValue == ID_Status:
                            new_entity.status = child.childNodes[1].childNodes[0].nodeValue
                        elif child.attributes['schemaPropertyId'].nodeValue == ID_Priority:
                            new_entity.priority = child.childNodes[1].childNodes[0].nodeValue
            else:
                print("Warning - unrecognised entity with schema class '%s' encountered. Skipped it" %
                      node.attributes['id'].nodeValue)

            entities[new_entity.id] = new_entity

            if isinstance(new_entity, Requirement):
                requirements[new_entity.id] = new_entity
            elif isinstance(new_entity, Action):
                actions[new_entity.id] = new_entity
            elif isinstance(new_entity, Asset):
                assets[new_entity.id] = new_entity

    # Parse all Relationships Types from the schema; making sure that we understand them correctly
    Topic = xml_obj.getElementsByTagName('schemaRelation')
    relationhip_types = {}
    for node in Topic:
        id = node.attributes['id'].nodeValue
        assert id not in relationhip_types
        for child in node.childNodes:
            if child.localName == 'name':
                relationhip_types[id] = child.childNodes[0].nodeValue
                break

    recognized_relationship_types = {ID_REL_Satisfies,ID_REL_Satisfied_by, ID_REL_Decomposes,ID_REL_Decomposed_by,
                                     ID_REL_Sourced_by,ID_REL_Receives_IO}
    for t in recognized_relationship_types:
        assert t in relationhip_types
    assert relationhip_types[ID_REL_Satisfies]     == 'satisfies'
    assert relationhip_types[ID_REL_Satisfied_by]  == 'satisfied by'
    assert relationhip_types[ID_REL_Decomposes]    == 'decomposes'
    assert relationhip_types[ID_REL_Decomposed_by] == 'decomposed by'
    assert relationhip_types[ID_REL_Sourced_by]    == 'sourced by'
    assert relationhip_types[ID_REL_Receives_IO]   == 'receives'

    # Parse all Relationships
    relationships_by_source = {}
    Topic = xml_obj.getElementsByTagName('relationship')
    for node in Topic:
        relationship = Relationship()
        for child in node.childNodes:
            if child.localName == 'sourceId':
                relationship.source = child.childNodes[0].nodeValue
            elif child.localName == 'targetId':
                relationship.target = child.childNodes[0].nodeValue
            elif child.localName == 'schemaRelationId':
                relationship.reltype = child.childNodes[0].nodeValue
                assert relationship.reltype in relationhip_types

        if relationship.source not in relationships_by_source:
            relationships_by_source[relationship.source] = [relationship]
        else:
            relationships_by_source[relationship.source].append(relationship)

    # Parse all Labels
    Topic = xml_obj.getElementsByTagName('label')
    labels = {}
    for node in Topic:
        id = node.attributes['id'].nodeValue
        label = Label(id)
        for child in node.childNodes:
            if child.localName == 'name':
                label.name = child.childNodes[0].nodeValue
            elif (child.localName == 'description') and (len(child.childNodes) > 0):
                assert len(child.childNodes) == 1
                label.description = child.childNodes[0].nodeValue
        labels[label.id] = label.name

    return (requirements, actions, assets, entities, relationships_by_source, labels)


def write_requirements_csv(requirements, entities, relationships, labels):
    """
    Writes the parsed requirements to CSV
    """
    with open('Requirements.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
        writer.writerow(['sep=,'])
        header_row = ['Number', 'Name', 'Description', 'Priority', 'Status', 'Labels', 'Decomposes', 'Decomposed by',
                       'Satisfied by']
        writer.writerow(header_row)

        for requirement in requirements.values():
            assert isinstance(requirement, Requirement)
            labels_string = ''
            for label in requirement.labels:
                labels_string += "%s, " % labels[label]

            decomposes_string = ''
            decomposedby_string = ''
            satisfiedby_string = ''
            if requirement.id in relationships:
                requirement_relationships = relationships[requirement.id]
                for relationship in requirement_relationships:
                    if relationship.target in entities:
                        target_string = "%s %s, " % (entities[relationship.target].number, entities[relationship.target].name)
                        if relationship.reltype == ID_REL_Decomposes:
                            decomposes_string += target_string
                        elif relationship.reltype == ID_REL_Decomposed_by:
                            decomposedby_string += target_string
                        elif relationship.reltype == ID_REL_Satisfied_by:
                            satisfiedby_string += target_string

            data_row = [requirement.number, requirement.name, strip_tags(requirement.description), requirement.priority,
                        requirement.status, labels_string, decomposes_string, decomposedby_string, satisfiedby_string]
            writer.writerow([unicode(s).encode("utf-8") for s in data_row])

def write_requirements_action_matrix_csv(requirements, actions, entities, relationships, labels):
    """
    Writes a CSV that maps requiresments to actions as a tracebility matrix
    """
    with open('Requirements_Functions_matrix.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
        writer.writerow(['sep=,'])

        header_row = ['REQ/ACT Number', 'REQ_Name', 'REQ_Description', 'REQ_Labels']
        row_two = ['ACT_Name']
        row_two.extend(['']*3)
        row_three = ['ACT_Descripton']
        row_three.extend(['']*3)
        row_four = ['ACT_Labels']
        row_four.extend(['']*3)
        actions_id_to_column_index = {}

        column_index = 3    # zero-based
        for action in actions.values():
            assert isinstance(action, Action)
            column_index += 1
            actions_id_to_column_index[action.id] = column_index
            header_row.append(action.number)
            row_two.append(action.name)
            row_three.append(action.description)
            labels_string = ''
            for label in action.labels:
                labels_string += "%s, " % labels[label]
            row_four.append(labels_string)
        writer.writerow(header_row)
        writer.writerow(row_two)
        writer.writerow(row_three)
        writer.writerow(row_four)

        for requirement in requirements.values():
            assert isinstance(requirement, Requirement)
            labels_string = ''
            for label in requirement.labels:
                labels_string += "%s, " % labels[label]
            row = [requirement.number, requirement.name, requirement.description, labels_string]

            # Now find all the actions that satisfy this requirement, and map them in the matrix
            row.extend(['.']*column_index)
            if requirement.id in relationships:
                requirement_relationships = relationships[requirement.id]
                for relationship in requirement_relationships:
                    if relationship.reltype == ID_REL_Satisfied_by:
                        if (relationship.target in entities) and isinstance(entities[relationship.target], Action):
                            target = entities[relationship.target]
                            assert relationship.target in actions_id_to_column_index
                            row[actions_id_to_column_index[relationship.target]] = 'X'

            writer.writerow([unicode(s).encode("utf-8") for s in row])

def write_actions_csv(actions, entities, relationships):
    """
    Writes the parsed actions to CSV
    """
    with open('Actions.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
        writer.writerow(['sep=,'])
        header_row = ['Number', 'Name', 'Decomposes', 'Decomposed by', 'Satisfies']
        writer.writerow(header_row)
        for action in actions.values():
            assert isinstance(action, Action)

            decomposes_string = ''
            decomposedby_string = ''
            satisfies_string = ''
            if action.id in relationships:
                relationships_of_this_action = relationships[action.id]
                for relationship in relationships_of_this_action:
                    if relationship.target in entities:
                        target_string = "%s %s, " % (entities[relationship.target].number, entities[relationship.target].name)
                        if relationship.reltype == ID_REL_Decomposes:
                            decomposes_string += target_string
                        elif relationship.reltype == ID_REL_Decomposed_by:
                            decomposedby_string += target_string
                        elif relationship.reltype == ID_REL_Satisfies:
                            satisfies_string += target_string

            data_row = [action.number, action.name, decomposes_string, decomposedby_string, satisfies_string]
            writer.writerow([unicode(s).encode("utf-8") for s in data_row])

def write_assets_csv(assets, entities, relationships):
    """
    Writes the parsed 'assets' to CSV
    """
    with open('Assets.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
        writer.writerow(['sep=,'])
        header_row = ['Number', 'Name', 'Description', 'Decomposes', 'Decomposed by']
        writer.writerow(header_row)

        for asset in assets.values():
            assert isinstance(asset, Asset)

            decomposes_string = ''
            decomposedby_string = ''
            if asset.id in relationships:
                requirement_relationships = relationships[asset.id]
                for relationship in requirement_relationships:
                    if relationship.target in entities:
                        target_string = "%s %s, " % (entities[relationship.target].number, entities[relationship.target].name)
                        if relationship.reltype == ID_REL_Decomposes:
                            decomposes_string += target_string
                        elif relationship.reltype == ID_REL_Decomposed_by:
                            decomposedby_string += target_string

            data_row = [asset.number, asset.name, strip_tags(asset.description), decomposes_string,
                        decomposedby_string]
            writer.writerow([unicode(s).encode("utf-8") for s in data_row])

def detect_and_write_duplicate_entities(entities, file_name):
    """
    Traverses the provided list of entities, lists all entities that don't have a unique 'number' field.
    This field needs to be unique, as it corresponds to the entity's ID in Innoslate.
    @param entities: a list or collection
    @param file_name: the text file to which duplicated entities need to be written
    """
    entity_numbers = set()
    duplicate_entity_occurences = {}
    for entity in entities:
        assert (isinstance(entity, Requirement) or isinstance(entity, Action) or isinstance(entity, Asset))
        if entity.number not in entity_numbers:
            entity_numbers.add(entity.number)
        else:
            if entity.number not in duplicate_entity_occurences:
                duplicate_entity_occurences[entity.number] = 2
            else:
                duplicate_entity_occurences[entity.number] += 1

    if len(duplicate_entity_occurences) > 0:
        with open(file_name, 'wb') as duplicates_file:
            writer = csv.writer(duplicates_file, delimiter=',')
            writer.writerow(['sep=,'])
            header_row = ['Entity Number', '# of occurrences']
            writer.writerow(header_row)
            for number in duplicate_entity_occurences:
                data_row = [number, str(duplicate_entity_occurences[number])]
                writer.writerow([unicode(s).encode("utf-8") for s in data_row])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        source_file_name = sys.argv[1]
        (requirements, actions, assets, entities, relationships, labels) = parse_it(source_file_name)
        write_actions_csv(actions, entities, relationships)
        write_assets_csv(assets, entities, relationships)
        write_requirements_csv(requirements, entities, relationships, labels)
        write_requirements_action_matrix_csv(requirements, actions, entities, relationships, labels)
        detect_and_write_duplicate_entities(actions.values(), '_duplicate_actions.csv')
        detect_and_write_duplicate_entities(assets.values(), '_duplicate_assets.csv')
        detect_and_write_duplicate_entities(requirements.values(), '_duplicate_requirements.csv')