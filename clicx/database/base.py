from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.exc import InvalidRequestError
from typing import Dict, Any, List, Union
import re
import weakref

class Base(DeclarativeBase):
    pass

# Global registry to track created classes
_class_cache = weakref.WeakValueDictionary()

# Combine metaclasses properly
class CombinedMeta(DeclarativeMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Skip processing for abstract classes and Base itself
        if namespace.get('__abstract__', False) or name in ('Base', 'BaseModel'):
            return super().__new__(mcs, name, bases, namespace, **kwargs)
        
        # Create a unique key for this class
        module = namespace.get('__module__', 'unknown')
        model_name = namespace.get('_name')
        
        # Create cache key
        if model_name:
            cache_key = f"model:{model_name}"
        else:
            cache_key = f"class:{module}.{name}"
        
        # Check if we already have this exact class
        if cache_key in _class_cache:
            existing_cls = _class_cache[cache_key]
            return existing_cls
        
        # Check our model registry first
        if model_name:
            from .registry import ModelRegistry
            existing_cls = ModelRegistry.get(model_name)
            if existing_cls is not None:
                _class_cache[cache_key] = existing_cls
                return existing_cls
        
        # Check SQLAlchemy's registry to see if this class already exists
        registry = Base.registry
        if hasattr(registry, '_class_registry'):
            # Look for existing class by checking table name or model name
            for reg_cls in registry._class_registry.data.values():
                if (isinstance(reg_cls, type) and 
                    hasattr(reg_cls, '_name') and 
                    model_name and 
                    getattr(reg_cls, '_name', None) == model_name):
                    # Found existing class with same model name
                    _class_cache[cache_key] = reg_cls
                    return reg_cls
        
        # Handle Odoo-style model naming BEFORE SQLAlchemy processes it
        if '_name' in namespace:
            # Use _name if specified (Odoo style: 'sale.order.line')
            model_name = namespace['_name']
            # Convert dots to underscores for table name
            namespace['__tablename__'] = model_name.replace('.', '_')
        elif '__tablename__' not in namespace:
            # Fallback to class name converted to snake_case
            table_name = mcs._camel_to_snake(name)
            namespace['__tablename__'] = table_name
            model_name = table_name.replace('_', '.')
        
        # Import Field classes here to avoid circular imports
        from .fields import Field, Many2one, One2many, Many2many
        
        # Process fields and create SQLAlchemy columns BEFORE SQLAlchemy metaclass
        fields = {}
        pending_relationships = {}
        
        # Collect fields from the class and its bases
        for base in reversed(bases):
            if hasattr(base, '__dict__'):
                for attr_name, attr_value in base.__dict__.items():
                    if isinstance(attr_value, Field):
                        fields[attr_name] = attr_value
        
        # Add fields from current class
        for attr_name, attr_value in namespace.items():
            if isinstance(attr_value, Field):
                fields[attr_name] = attr_value
        
        # Create SQLAlchemy columns and prepare relationships
        for field_name, field_obj in fields.items():
            if isinstance(field_obj, Many2one):
                # Convert comodel_name from dot notation to table name for FK
                comodel_table = field_obj.comodel_name.replace('.', '_')
                # Create foreign key column
                fk_column = Column(f"{field_name}_id", Integer, 
                                 ForeignKey(f"{comodel_table}.id", ondelete=field_obj.ondelete), 
                                 nullable=not field_obj.required)
                namespace[f"{field_name}_id"] = fk_column
                
                # Store for later relationship creation
                field_obj._fk_column = fk_column
                pending_relationships[field_name] = field_obj
                
            elif isinstance(field_obj, One2many):
                # Store for later relationship creation
                pending_relationships[field_name] = field_obj
                
            elif isinstance(field_obj, Many2many):
                # Store for later relationship creation
                pending_relationships[field_name] = field_obj
            else:
                # Regular field
                column = field_obj.get_column(field_name)
                if column is not None:
                    namespace[field_name] = column
        
        # Add id column if not present
        if 'id' not in namespace and not any(hasattr(base, 'id') for base in bases):
            namespace['id'] = Column('id', Integer, primary_key=True, autoincrement=True)
        
        # Let SQLAlchemy's metaclass do its thing
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        
        # Cache the new class
        _class_cache[cache_key] = cls
        
        # Now set our custom attributes
        if model_name:
            cls._name = model_name
        elif '_name' not in namespace:
            # Derive _name from table name
            cls._name = cls.__tablename__.replace('_', '.')
        
        # Store field definitions and relationships for later processing
        cls._fields = fields
        cls._pending_relationships = pending_relationships
        
        # Register the model using the _name (dot notation)
        from .registry import ModelRegistry
        
        # Only register if not already present
        if not ModelRegistry.is_registered(cls._name):
            ModelRegistry.register(cls._name, cls)
        
        return cls
    
    @staticmethod
    def _camel_to_snake(name):
        """Convert CamelCase to snake_case"""
        # Insert underscore before uppercase letters that follow lowercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters that follow lowercase letters or digits
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class BaseModel(Base, metaclass=CombinedMeta):
    __abstract__ = True
    
    def __init__(self, **kwargs):
        # Set field values
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    # Remove the problematic __init_subclass__ method entirely
    # The metaclass handles everything we need
    
    @classmethod
    def create(cls, values: Dict[str, Any]):
        """Create a new record"""
        from .connection import DatabaseConnection
        
        instance = cls(**values)
        db = DatabaseConnection('your_db_name')  # Configure as needed
        with db.get_session() as session:
            session.add(instance)
            session.flush()  # To get the ID
            session.refresh(instance)
            return instance
    
    @classmethod
    def search(cls, domain: List = None, limit: int = None, offset: int = None):
        """Search for records"""
        from .connection import DatabaseConnection
        
        db = DatabaseConnection('your_db_name')  # Configure as needed
        with db.get_session() as session:
            query = session.query(cls)
            
            # Apply domain filters (simplified - you'd want to implement a proper domain parser)
            if domain:
                for condition in domain:
                    if len(condition) == 3:
                        field, operator, value = condition
                        if hasattr(cls, field):
                            if operator == '=':
                                query = query.filter(getattr(cls, field) == value)
                            elif operator == '!=':
                                query = query.filter(getattr(cls, field) != value)
                            elif operator == 'in':
                                query = query.filter(getattr(cls, field).in_(value))
                            # Add more operators as needed
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    @classmethod
    def browse(cls, ids: Union[int, List[int]]):
        """Browse records by IDs"""
        from .connection import DatabaseConnection
        
        if isinstance(ids, int):
            ids = [ids]
        
        db = DatabaseConnection('your_db_name')  # Configure as needed
        with db.get_session() as session:
            return session.query(cls).filter(cls.id.in_(ids)).all()
    
    def write(self, values: Dict[str, Any]):
        """Update record"""
        from .connection import DatabaseConnection
        
        db = DatabaseConnection('your_db_name')  # Configure as needed
        with db.get_session() as session:
            # Merge current instance into session
            session.merge(self)
            
            # Update values
            for key, value in values.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            session.commit()
    
    def unlink(self):
        """Delete record"""
        from .connection import DatabaseConnection
        
        db = DatabaseConnection('your_db_name')  # Configure as needed
        with db.get_session() as session:
            session.merge(self)
            session.delete(self)
            session.commit()
    
    @property
    def env(self):
        """Access to environment (simplified)"""
        return Environment()

class Environment:
    """Simplified environment class"""
    def __init__(self):
        from .registry import ModelRegistry
        self.registry = ModelRegistry
        # Ensure relationships are resolved
        ModelRegistry.resolve_relationships()
    
    def __getitem__(self, model_name: str):
        """Get model class by name (supports dot notation)"""
        return self.registry.get(model_name)