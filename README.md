# DBML-to-SQLAlchemy

This script is meant to convert a DBML schema to SQLAlchemy mapped classes representation. Covers a few of the most common use cases.

Dependencies: [PyDBML](https://github.com/Vanderhoof/PyDBML) \
Requires Python 3.10

## Usage
```bash
* python -m venv venv
* source venv/bin/activate
* python -m pip install .
* dbml2sqlalchemy -i schema.dbml -o schema.py
```

## Acknowledgement
This work is to most parts based on https://github.com/aphilas/dbml-to-sqlalchemy.
