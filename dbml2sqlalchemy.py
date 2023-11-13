"""
Parses a DBML file to output SQLAlchemy models
"""

"""
TODO:
- modify architecture
- table refs
- enums
- indexes: functional indexes, index constraints
- constraints: composite fk
- default: functional value
- references: 1-1, inline references
- cascade

N.B: 
- use snake_case for table names
- removed nullable = True from assoc tables
- skips default: NULL
- skips autoincrement — lets SQLAlchemy handle...
"""

from pydbml import PyDBML
from pathlib import Path
from textwrap import dedent, indent
from dataclasses import dataclass
from argparse import ArgumentParser
import re
import os


def snake_to_pascal(string):
    """Convert snake_case to PascaleCase for mapped class identifiers"""
    return "".join(map(lambda w: w.title(), string.split("_")))


def setdefaultattr(obj, name, value):
    """Get attribute if exists, else set to default and get"""
    if not hasattr(obj, name):
        setattr(obj, name, value)
    return getattr(obj, name)


# embellish columns before generating output
def embellish_ref(ref):
    """Add a references attribute to <Column>s from 'global' <Reference>s"""
    match (ref.type):
        case "<":
            col_refs = setdefaultattr(ref.col2[0], "references", [])
            col_refs.append(ref)
            # f"ForeignKey('{ reference.table1.name }.{ reference.col1[0].name }')"
        case ">":
            col_refs = setdefaultattr(ref.col1[0], "references", [])
            col_refs.append(ref)
            # f"ForeignKey('{ reference.table2.name }.{ reference.col2[0].name }')"
        case "-":
            pass


def embellish_refs(refs):
    """Add refs to respective column objects"""
    for ref in refs:
        embellish_ref(ref)


def parse_ref(reference):
    schema = ""
    match (reference.type):
        case "<":
            if  reference.table1.schema:
                schema = f"{ reference.table1.schema }."
            return f"ForeignKey('{schema}{ reference.table1.name }.{ reference.col1[0].name }')"
        case ">":
            if  reference.table2.schema:
                schema = f"{ reference.table2.schema }."
            return f"ForeignKey('{schema}{ reference.table2.name }.{ reference.col2[0].name }')"


def parse_refs(column):
    return (
        ', '.join([parse_ref(reference) for reference in column.references])
        if hasattr(column, "references")
        else None
    )

def _match_geometry_type(type_str):
    """Convert geometry type

    Args:
      type_str: Geometry type string of tyle geometry(geometry_type, srid),
                e.g. Geometry(POINT,25832))

    Returns:
        Geometry type for SQLAlchemy/GeoAlchemy2
    """

    # Remember: No whitespaces allowed in dbml type
    match = re.match(r"geometry\(([a-zA-Z]+),?(.*)\)", type_str)

    try:
        geo_type = match.group(1)
        srid = match.group(2)
    except AttributeError:
        return type_str

    if not srid:
        type_str = f"Geometry(geometry_type='{geo_type}')"
    else:
        type_str = f"Geometry(geometry_type='{geo_type}', srid={srid})"

    return type_str


def match_type(type_str):
    type_str = _match_geometry_type(type_str)

    # Arrays, e.g. Float[]
    type_array = re.search(r"([a-zA-Z]{1})([a-zA-Z]+)\[\]", type_str)
    if type_array:
        type_str = f"ARRAY({type_array.group(1).upper()}{type_array.group(2)})"

    # simple types
    match type_str:
        case "int" | "integer":
            return "Integer"
        case "varchar" | "text":
            return "String"
        case "date" | "time" as value:
            return value.capitalize()
        case 'float' as value:
            return value.capitalize()
        case 'datetime':
            return 'DateTime'
        case 'timestamp' | 'char' as value:
            return value.upper()
        case 'bool' | 'boolean':
            return 'Boolean'
        case 'json':
            return 'JSON'
        case 'geometry':
            return 'Geometry'
        case _:
            return type_str


def parse_type(type_str):
    colsize = r"(\w+)\((\d+)\)"

    match type_str:
        case str(type_str):
            match = re.fullmatch(colsize, type_str)

            if match:
                col_type, size = match.group(1, 2)
                return f"{match_type(col_type)}({size})"
            else:
                return match_type(type_str)
        case _:
            # enums
            return "String(256)"


def col_settings_name(setting_name):
    map_col_settings = {
        "not_null": "nullable",  # reverses meaning
        "pk": "primary_key",
        "autoinc": "autoincrement",
    }

    return map_col_settings.get(setting_name, setting_name)


def parse_default(default_str):
    if default_str == None:
        return None

    match default_str:
        case "NULL":
            return None
        case "(now())":
            return "func.now()"
        case _:
            return f"'{default_str}'"


def parse_col_settings(column):
    settings = {}

    autoincrement = False
    primary_key = False

    for prop, value in vars(column).items():
        match setting_name := col_settings_name(prop):
            case 'autoincrement':
                if value:
                    autoincrement = True
            case 'nullable':
                # value = not value
                # if value != True:
                #     settings[setting_name] = value
                pass
            case 'primary_key':
                if value != False:
                    settings[setting_name] = value
                    primary_key = value
            case 'unique':
                if value != False:
                    settings[setting_name] = value
            case "default":
                default = parse_default(value)

                # FIX - hardcoded sql function
                if default and default == "(now())":
                    settings["server_default"] = "func.now()"
                elif default:
                    settings[setting_name] = default

    # Workaround for SQLAlchemey, which only support autoincrements on primary key
    # columns
    settings_list = []
    
    # Non-keywoard arguments at the beginngin
    if autoincrement and not primary_key:
        settings_list.append('Identity()')

    for prop, value in settings.items():
        settings_list.append(f'{prop}={value}')

    return ', '.join(settings_list)


def parse_column_rhs(column):
    settings = parse_col_settings(column)
    foreign_key = parse_refs(column)
    return f"""Column({ parse_type(column.type) }{', ' + foreign_key if foreign_key else '' }{ ', ' + settings if settings else '' })"""


def parse_column(column):
    return f"""{column.name} = { parse_column_rhs(column) }"""


def join_columns(column_strings):
    spaces = " " * 4 * 3

    # do not indent first line
    return "\n".join(
        [
            column if i == 0 else indent(column, spaces)
            for i, column in enumerate(column_strings)
        ]
    )


def parse_columns(columns):
    return join_columns([parse_column(column) for column in columns])


def parse_index_subject(subject):
    match subject.__class__.__name__:
        case "Column":
            return subject.name
        case "str":
            return subject


def parse_index(index):
    subjects = [parse_index_subject(subject) for subject in index.subjects]
    return f"""Index('{index.name if index.name else f"idx_{'_'.join(subjects)}" }', {', '.join(map(lambda subject: f"'{subject}'", subjects))})"""


def parse_indexes(indexes):
    # add extra comma
    return f"""{ ', '.join([*[parse_index(index) for index in indexes]]) }"""


def all_true(iterable, pred=bool):
    return all(pred(el) for el in iterable)


def association_table(table):
    return len(table.columns) == 2 and all_true(
        table.columns, lambda col: hasattr(col, "references")
    )


def parse_assoc_table(table):
    return dedent(
        f"""\
        { table.name } = Table('{ table.name }', Base.metadata,
            Column('{ table.columns[0].name }', { parse_column_rhs(table.columns[0]).lstrip('Column(') },
            Column('{ table.columns[1].name }', { parse_column_rhs(table.columns[1]).lstrip('Column(') }
        )

    """
    )


@dataclass
class Link:
    table: "typing.Any"
    assoc_table: "typing.Any"


def embellish_assoc_references(tables):
    assoc_tables = filter(association_table, tables)

    for assoc_table in assoc_tables:
        table_pair = []

        for column in assoc_table.columns:
            # assume one reference - always true?
            match (column.references[0].type):
                case "<":
                    table_pair.append(column.references[0].table1)
                case ">":
                    # table1 (many side is association table), table2 is target table
                    table_pair.append(column.references[0].table2)

        # add reference to first table
        setdefaultattr(table_pair[0], "links", []).append(
            Link(table=table_pair[1], assoc_table=assoc_table)
        )


def parse_assoc_relationships(table):
    # assume table.links
    relationship_strs = []

    for link in table.links:
        relationship_strs.append(
            f"{link.table.name}s = relationship('{ snake_to_pascal(link.table.name) }', secondary='{link.assoc_table.name}', backref='{table.name}s')"
        )

    return relationship_strs


def parse_relationship(reference):
    match (reference.type):
        case "<":
            return f"{reference.table1.name} = relationship('{ snake_to_pascal(reference.table1.name) }', backref='{ reference.table2.name }s')"
        case ">":
            return f"{reference.table2.name} = relationship('{ snake_to_pascal(reference.table2.name) }', backref='{ reference.table1.name }s')"


def parse_relationships(table):
    spaces = " " * 4 * 3

    relationships = [
        parse_relationship(reference)
        for column in table.columns
        if hasattr(column, "references")
        for reference in column.references
    ]
    relationships += (
        parse_assoc_relationships(table) if hasattr(table, "links") else []
    )

    if len(relationships) < 1:
        return ""

    # do not indent first line
    return "\n".join(
        [
            relationship if i == 0 else indent(relationship, spaces)
            for i, relationship in enumerate(relationships)
        ]
    )


def parse_table(table):
    nl = "\n"
    indexes = parse_indexes(table.indexes) if len(table.indexes) > 0 else ""

    if association_table(table):
        return parse_assoc_table(table)

    table_args = []
    if indexes:
        table_args.append(indexes)
    table_args.append(f"{{'schema' : '{table.schema}'}}")

    ret = dedent(
        f"""\
        class {snake_to_pascal(table.name)}(Base):

            __tablename__ = '{table.name}'
            __table_args__ = ({', '.join(table_args)})

            { parse_columns(table.columns) }

            { parse_relationships(table) }


        """
    )

    return ret


def parse_dbml(in_fname):
    """Parse dbml and return python code

    Args:
      in_fname: Inpupt DBML filename
    """
    _parsed = PyDBML(Path(in_fname))
    dir(_parsed)
    embellish_refs(_parsed.refs)
    embellish_assoc_references(_parsed.tables)

    string = "".join([parse_table(table) for table in _parsed.tables])
    return re.sub(r"\n{3,}", "\n\n", string)


# INPUT = 'data/schema.dbml'
OUTPUT = "out/models.txt"

if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        required=True,
        help="Input DBML file",
        metavar="INPUT",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        required=False,
        help="Output file",
        metavar="OUTPUT",
    )

    args = parser.parse_args()

    if os.path.exists(args.input):
        with open(args.output or OUTPUT, "w") as fd:
            parsed = parse_dbml(args.input)

            fd.write(parsed)
            print(f"Models generated successfully in {args.output or OUTPUT}")
    else:
        print("Input file does not exist")
