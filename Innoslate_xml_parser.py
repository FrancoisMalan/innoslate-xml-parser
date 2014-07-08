# Innoslate XML parser copyright (c) 2014 by Francois Malan francois@scs-space.com
# Extracts CSV files from the SKA SDP Innoslate project's exported XML

# This script is written to be run in Python 2.x (Tested in 2.7)

import sys
import csv
from xml.dom import minidom
from HTMLParser import HTMLParser

ID_requirement = 'C1Z'
ID_action = 'C1'

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

#HTML stripping


def usage():
    print("usage: Innoslate_xml_parser source_file_name")


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
    entities = {} # Requirements and actions

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

        if new_entity is not None:
            if isinstance(new_entity, Requirement) or isinstance(new_entity, Action):
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
                        if child.attributes['schemaAttributeId'].nodeValue == ID_Status:
                            new_entity.status = child.childNodes[1].childNodes[0].nodeValue
                        elif child.attributes['schemaAttributeId'].nodeValue == ID_Priority:
                            new_entity.priority = child.childNodes[1].childNodes[0].nodeValue
            else:
                print("Warning - unrecognised entity with schema class '%s' encountered. Skipped it" %
                      node.attributes['id'].nodeValue)

            entities[new_entity.id] = new_entity

            if isinstance(new_entity, Requirement):
                requirements[new_entity.id] = new_entity
            elif isinstance(new_entity, Action):
                actions[new_entity.id] = new_entity

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
            elif child.localName == 'description':
                label.description = child.childNodes[0].nodeValue
        labels[label.id] = label.name

    return (requirements, actions, entities, relationhip_types, relationships_by_source, labels)


def write_requirements_csv(requirements, entities, relationships, labels):
    """
    Writes the parsed requirements to CSV
    """
    with open('Requirements.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
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

def write_actions_csv(actions, entities, relationships):
    """
    Writes the parsed actions to CSV
    """
    with open('Actions.csv', 'wb') as fp:
        writer = csv.writer(fp, delimiter=',')
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        source_file_name = sys.argv[1]
        (requirements, actions, entities, relationhip_types, relationships, labels) = parse_it(source_file_name)
        write_actions_csv(actions, entities, relationships)
        write_requirements_csv(requirements, entities, relationships, labels)
