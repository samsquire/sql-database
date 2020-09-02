from pprint import pprint
from operator import itemgetter
import re
from collections import defaultdict
from functools import reduce
items = [
    {"key": "C.keyword.0", "value": "databases"},
    {"key": "C.keyword.1", "value": "cat"},
    {"key": "C.keyword.2", "value": "car"},
    {"key": "C.searchterm.0", "value": "search"},
    {"key": "R.people.0.id", "value": 0},
    {"key": "R.people.1.id", "value": 1},
    {"key": "R.people.1.people_name", "value": "Paul"},
    {"key": "R.people.0.people_name", "value": "Samuel"},
    {"key": "R.items.0.search", "value": "Things"},
    {"key": "R.items.1.search", "value": "Others"},
    {"key": "R.items.0.people", "value": 0},
    {"key": "R.items.1.people", "value": 1},
    {"key": "R.products.0.id", "value": 0},
    {"key": "R.products.0.name", "value": "Things"},
    {"key": "R.products.1.id", "value": 1},
    {"key": "R.products.1.name", "value": "Others"},
    {"key": "R.products.1.price", "value": "20"},
    {"key": "R.products.0.price", "value": "30"},
]
items = sorted(items, key=itemgetter("key"))
pprint(items)


class Parser():
    def __init__(self):
        self.last_char = " "
        self.pos = 0
        self.select_clause = []
        self.join_clause = []
        self.end = False
        self.group_by = None
        self.insert_fields = []
        self.insert_values = []

    def getchar(self):
        
        char = self.statement[self.pos]
        if self.pos + 1 == len(self.statement):
            self.end = True
            return char
        self.pos = self.pos + 1
        
        return char
        
    def gettok(self):
        while (self.last_char == " "):
            self.last_char = self.getchar()
        
        if self.last_char == "(":
            self.last_char = self.getchar()
            return "openbracket"
        
        if self.last_char == ")":
            self.last_char = self.getchar()
            return "closebracket"
        
        if self.last_char == "*":
            self.last_char = self.getchar()
            return "wildcard"
        
        if self.last_char == "'":
            self.last_char = self.getchar()
            identifier = ""
            while self.end == False and self.last_char != "'":
                if self.last_char == "\\":
                    self.last_char = self.getchar()
                identifier = identifier + self.last_char
                self.last_char = self.getchar()
            if self.end and self.last_char != ")":
                identifier += self.last_char
            
            self.last_char = self.getchar()
            
            return identifier
        
        if re.match("[a-zA-Z0-9\.\_]+", self.last_char):
            identifier = ""
            while self.end == False and re.match("[a-zA-Z0-9\.\_]+", self.last_char):
                
                identifier = identifier + self.last_char
                self.last_char = self.getchar()
            
            if self.end and self.last_char != ")":
                identifier += self.last_char
            
            return identifier
    
        if self.last_char == "=":
            self.last_char = self.getchar()
            return "eq"
        
        if self.last_char == ",":
            self.last_char = self.getchar()
            return "comma"
    
    def parse_select(self, token=None):
        if token == None:
            token = self.gettok()
        if token == "comma":
            self.parse_select()
        elif token == "from":
            self.table_name = self.gettok()
            self.parse_rest()
        elif token != None:
            identifier = token
            
            token = self.gettok()
            if token == "openbracket": # we're in a function
                function_parameters = self.gettok()
                if function_parameters == "wildcard":
                    function_parameters = "*"
            else:
                self.select_clause.append(identifier)
                self.parse_select(token)
                return
            closebracket = self.gettok()
            
            self.select_clause.append(identifier + "(" + function_parameters + ")")
            self.parse_select()
    
    def parse_rest(self):
        operation = self.gettok()
        if operation == "group":
            by = self.gettok()
            group_by = self.gettok()
            self.group_by = group_by
            
        if operation == "inner":
            join = self.gettok()
            self.join_table = self.gettok()
            on = self.gettok()
            join_target_1 = self.gettok()
            
            self.gettok()
            join_target_2 = self.gettok()
            self.join_clause.append([join_target_1, join_target_2])
            self.parse_rest()
    
    def parse_insert_fields(self):
        field_name = self.gettok()
        self.insert_fields.append(field_name)
        print("Adding:" + field_name)
        token = self.gettok()
        if token == "closebracket":
            self.parse_rest_insert()
        if token == "comma":
            self.parse_insert_fields()
    
    def parse_values(self):
        value = self.gettok()
        if re.match("[0-9\.]+", value):
            value = int(value)
        self.insert_values.append(value)
        print(value)
        token = self.gettok()
        print(token)
        if token == "comma":
            self.parse_values()
        if token == "closebracket":
            print("We have finished parsing insert into")
            
        
    def parse_rest_insert(self):
        values = self.gettok()
        if values == "values":
            openbracket = self.gettok()
            self.parse_values()
    
    def parse_insert(self):
        self.insert_table = self.gettok()
        openbracket = self.gettok()
        print(openbracket)
        if openbracket == "openbracket":
            self.parse_insert_fields()
    
    def parse(self, statement):
        self.statement = statement
        token = self.gettok()
        if token == "select":
            self.parse_select()
        if token == "insert":
            into = self.gettok()
            self.parse_insert()
        print(token)


class SQLExecutor:
    def __init__(self, parser):
        self.parser = parser
    
    def get_tables(self, table_def):
        table_datas = []
        for pair in table_def:
            pair_data = []
            for selector in pair:
                table, field = selector.split(".")
                row_filter = "R.{}".format(table)
                table_data = list(filter(lambda x: x["key"].startswith(row_filter), items))
                pair_data.append((table_data, field))
            table_datas.append(pair_data)


        def table_reductions(table, metadata):
            for record in table:
                yield from reduce_table(metadata, record)
            yield metadata["current_record"]

        def reduce_table(table_metadata, record):
            components = record["key"].split(".")
            identifier = components[2]
            field_name = components[3]
            last_id = table_metadata["current_record"].get("internal_id")
            if last_id == None:
                table_metadata["current_record"] = {}
                table_metadata["current_record"]["internal_id"] = identifier
                table_metadata["current_record"][field_name] = record["value"]
            elif last_id != identifier:
                yield table_metadata["current_record"]
                # reset
                table_metadata["current_record"] = {}
                table_metadata["current_record"]["internal_id"] = identifier
                table_metadata["current_record"][field_name] = record["value"]
            elif last_id == identifier:
                table_metadata["current_record"][field_name] = record["value"]


        field_reductions = []
        for pair in table_datas:
            pair_items = []
            for item in pair:
                table, join_field = item
                field_reduction = table_reductions(table, defaultdict(dict))
                pair_items.append(field_reduction)
            field_reductions.append(pair_items)
        return table_datas, field_reductions
    
    def execute(self):
        if self.parser.insert_values:
            insert_table = self.parser.insert_table
            print("Insert statement")
            for field, value in zip(self.parser.insert_fields, self.parser.insert_values):
                table_datas, field_reductions = self.get_tables([["{}.".format(insert_table)]])
                new_insert_count = len(field_reductions[0]) + 1
                new_key = "R.{}.{}.{}".format(insert_table, new_insert_count, field)
                items.append({
                    "key": new_key,
                    "value": value
                })
                new_key = "R.{}.{}.id".format(insert_table, new_insert_count, field)
                items.append({
                    "key": new_key,
                    "value": new_insert_count
                })
                items.sort(key=itemgetter('key'))
            
        elif self.parser.group_by:
            aggregator = defaultdict(list)
            for item in items:
                k = item["key"]
                v = item["value"]
                if (k.split(".")[1] == parser.group_by):
                    aggregator[v].append(v)

            print(len(aggregator["databases"]))
            print(statement)
            for k, v in aggregator.items():
                output_line = ""
                for item in parser.select_clause:
                    if "count" in item:
                        output_line += str(len(aggregator[k]))
                    else:
                        output_line += k + " "
                print(output_line)
        elif self.parser.join_clause:
            table_datas, field_reductions = self.get_tables(self.parser.join_clause)


            def hash_join(records, index, pair):
                ids_for_key = defaultdict(list)
                if len(records) > 0:
                    scan = records
                else:
                    scan = pair[0]
                for item in scan:
                    field = table_datas[index][0][1]
                    print(field)
                    left_field = item[field]
                    ids_for_key[left_field] = item
                for item in pair[1]:
                    if item[table_datas[index][1][1]] in ids_for_key:
                        yield {**ids_for_key[item[table_datas[index][1][1]]], **item}


            records = []
            for index, pair in enumerate(field_reductions):
                records = list(hash_join(records, index, pair))

            for record in records:
                output_line = []
                for clause in parser.select_clause:
                    table, field = clause.split(".")
                    output_line.append(record[field])
                print(output_line)

        
statement = "select keyword, count(*) from items group by keyword"
parser = Parser()
parser.parse(statement)

SQLExecutor(parser).execute()

print("Inserting ted")
parser = Parser()
parser.parse("insert into people (people_name) values ('Ted')")
SQLExecutor(parser).execute()

print("Inserted ted")

parser = Parser()
parser.parse("insert into products (name, price) values ('Cat', 100)")
SQLExecutor(parser).execute()

parser = Parser()
parser.parse("insert into items (search, people) values ('Cat', 2)")
SQLExecutor(parser).execute()

pprint(items)

statement = "select products.price, people.people_name, items.search from items inner join people on people.id = items.people inner join products on items.search = products.name"
parser = Parser()
parser.parse(statement)
SQLExecutor(parser).execute()

