# DBML-to-SQLAlchemy

This script is meant to convert a DBML schema to SQLAlchemy mapped classes representation. Covers a few of the most common use cases.

Dependencies: [PyDBML](https://github.com/Vanderhoof/PyDBML) \
Requires Python 3.10

## Usage
```bash
git clone https://github.com/nevilleomangi/dbml-to-sqlalchemy
cd dbml-to-sqlalchemy

# N.B. requires python 10
python -m venv venv
source venv/bin/activate

# python parse.py -i <schema.dbml> [-o <output.txt>]
python parse.py -i schema.dbml
```
