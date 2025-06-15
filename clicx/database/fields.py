from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy import Boolean as SQLBoolean  # Rename to avoid conflict
from typing import Any

class Field:
    """Base field class"""
    def __init__(self, string: str = None, required: bool = False, readonly: bool = False, 
                 default: Any = None, help: str = None, **kwargs):
        self.string = string
        self.required = required
        self.readonly = readonly
        self.default = default
        self.help = help
        self.kwargs = kwargs
    
    def get_column(self, name: str) -> Column:
        """Override in subclasses to return appropriate SQLAlchemy column"""
        raise NotImplementedError

class Char(Field):
    def __init__(self, size: int = 255, **kwargs):
        super().__init__(**kwargs)
        self.size = size
    
    def get_column(self, name: str) -> Column:
        return Column(name, String(self.size), nullable=not self.required, default=self.default)

class Text(Field):
    def get_column(self, name: str) -> Column:
        return Column(name, Text, nullable=not self.required, default=self.default)

class Integer(Field):
    def get_column(self, name: str) -> Column:
        return Column(name, Integer, nullable=not self.required, default=self.default)

class Float(Field):
    def __init__(self, digits: tuple = None, **kwargs):
        super().__init__(**kwargs)
        self.digits = digits
    
    def get_column(self, name: str) -> Column:
        return Column(name, Float, nullable=not self.required, default=self.default)

class Boolean(Field):
    def get_column(self, name: str) -> Column:
        return Column(name, SQLBoolean, nullable=not self.required, default=self.default or False)

class Datetime(Field):
    def get_column(self, name: str) -> Column:
        return Column(name, DateTime, nullable=not self.required, default=self.default)

class Many2one(Field):
    def __init__(self, comodel_name: str, ondelete: str = 'set null', **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.ondelete = ondelete
    
    def get_column(self, name: str) -> Column:
        # Foreign key column will be created dynamically
        return Column(f"{name}_id", Integer, ForeignKey(f"{self.comodel_name.replace('.', '_')}.id", 
                     ondelete=self.ondelete), nullable=not self.required)

class One2many(Field):
    def __init__(self, comodel_name: str, inverse_name: str, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.inverse_name = inverse_name
    
    def get_column(self, name: str) -> None:
        # One2many doesn't create a column, it's a relationship
        return None

class Many2many(Field):
    def __init__(self, comodel_name: str, relation: str = None, 
                 column1: str = None, column2: str = None, **kwargs):
        super().__init__(**kwargs)
        self.comodel_name = comodel_name
        self.relation = relation
        self.column1 = column1
        self.column2 = column2
    
    def get_column(self, name: str) -> None:
        # Many2many creates a separate table, not a column
        return None