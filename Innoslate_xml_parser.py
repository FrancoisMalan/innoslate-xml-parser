# GPX_Converter copyright (c) 2014 by Francois Malan francois@francoismalan.com
# Estimates mountain bike speed based on changes in elevation.

import sys
from xml.dom import minidom
import csv

from html.parser import HTMLParser

ID_requirement = 'C1Z'
ID_action = 'C1'

ID_Status   = 'P3q6z'
ID_Priority = 'Pjfa'

#HTML stripping
# developed from http://stackoverflow.com/questions/11061058/using-htmlparser-in-python-3-2
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    ''' 
       Function to strip tags and remove leading and trailing white
       space and remove most of the paragraph gaps.
    '''
    s = MLStripper()
    s.feed(html)
    return s.get_data().strip().replace('\n\n','').replace('\t',' ')
#HTML stripping


def usage():
    print("usage: GPX_Converter source_file_name target_file_name")

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
        return 'Requirement. id=%s, number=%s, name=%s, labels=%s' % (self.id, self.number, self.name, str(len(self.labels)))

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
        return 'Label: %s' % (self.name)

def parse_it(source_file_name):
    xmlObj = minidom.parse(source_file_name)

    types = set()

    requirements = {}
    actions = {}
    entities = {} # Requirements and actions

    relationships = []
    relationships_from = {}
    relationships_to = {}

    counter = 0
    Topic = xmlObj.getElementsByTagName('entity')
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
                print("Warning - unrecognised entity with schema class '%s' encountered. Skipped it" % node.attributes['id'].nodeValue)

            entities[new_entity.id] = new_entity
            if isinstance(new_entity, Requirement):
                requirements[new_entity.id] = new_entity
            elif isinstance(new_entity, Action):
                actions[new_entity.id] = new_entity

    Topic = xmlObj.getElementsByTagName('relationship')
    for node in Topic:
        relationship = Relationship()
        for child in node.childNodes:
            if child.localName == 'sourceId':
                relationship.source = child.childNodes[0].nodeValue
            elif child.localName == 'targetId':
                relationship.target = child.childNodes[0].nodeValue
            elif child.localName == 'schemaRelationId':
                relationship.reltype = child.childNodes[0].nodeValue

        if relationship.target not in relationships_to:
            relationships_to[relationship.target] = [relationship.source]
        else:
            relationships_to[relationship.target].append(relationship.source)

        if relationship.source not in relationships_from:
            relationships_from[relationship.source] = [relationship.target]
        else:
            relationships_from[relationship.source].append(relationship.target)
        relationships.append(relationship)

    Topic = xmlObj.getElementsByTagName('label')
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

    with open('Requirements.csv', 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
        data = [['number', 'name', 'description', 'priority', 'status', 'labels', 'relationships with...']]
        for requirement in requirements.values():
            assert isinstance(requirement, Requirement)
            labels_string = ''
            for label in requirement.labels:
                labels_string += "%s, " % labels[label]

            data_row = [requirement.number, requirement.name, strip_tags(requirement.description), requirement.priority, requirement.status, labels_string]
            if requirement.id in relationships_to:
                for key in relationships_to[requirement.id]:
                    if key in actions:
                        data_row.append(entities[key].number)
            if requirement.id in relationships_from:
                for key in relationships_from[requirement.id]:
                    if key in actions:
                        data_row.append(entities[key].number)
            data.append(data_row)
        a.writerows(data)

    with open('Actions.csv', 'w', newline='') as fp:
        a = csv.writer(fp, delimiter=',')
        data = [['number', 'name', 'relationships with...']]
        for action in actions.values():
            assert isinstance(action, Action)
            data_row = [action.number, action.name]
            if action.id in relationships_to:
                for key in relationships_to[action.id]:
                    if key in requirements:
                        data_row.append(entities[key].number)
            if action.id in relationships_from:
                for key in relationships_from[action.id]:
                    if key in requirements:
                        data_row.append(entities[key].number)
            data.append(data_row)
        a.writerows(data)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    else:
        source_file_name = sys.argv[1]
        parse_it(source_file_name)
