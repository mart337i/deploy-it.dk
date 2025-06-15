from typing import Dict, Type, Optional, TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from .base import BaseModel

class ModelRegistry:
    _registry: Dict[str, Type['BaseModel']] = {}
    _lock = threading.Lock()
    _relationships_resolved = False
    
    @classmethod
    def register(cls, model_name: str, model_class: Type['BaseModel']):
        with cls._lock:
            # Only register if not already present or if this is a different class
            existing = cls._registry.get(model_name)
            if existing is None or existing is not model_class:
                cls._registry[model_name] = model_class
    
    @classmethod
    def get(cls, model_name: str) -> Optional[Type['BaseModel']]:
        return cls._registry.get(model_name)
    
    @classmethod
    def all_models(cls) -> Dict[str, Type['BaseModel']]:
        return cls._registry.copy()
    
    @classmethod
    def is_registered(cls, model_name: str) -> bool:
        """Check if a model is already registered"""
        return model_name in cls._registry
    
    @classmethod
    def clear_registry(cls):
        """Clear the registry (useful for testing)"""
        with cls._lock:
            cls._registry.clear()
            cls._relationships_resolved = False
    
    @classmethod
    def resolve_relationships(cls):
        """Resolve all pending relationships after all models are registered"""
        if cls._relationships_resolved:
            return
            
        with cls._lock:
            if cls._relationships_resolved:  # Double-check after acquiring lock
                return
                
            for model_name, model_class in cls._registry.items():
                if hasattr(model_class, '_pending_relationships'):
                    cls._resolve_model_relationships(model_class)
            cls._relationships_resolved = True
    
    @classmethod
    def _resolve_model_relationships(cls, model_class):
        """Resolve relationships for a specific model"""
        from sqlalchemy.orm import relationship
        from .fields import Many2one, One2many, Many2many
        
        if not hasattr(model_class, '_pending_relationships'):
            return
            
        for field_name, field_obj in model_class._pending_relationships.items():
            # Skip if relationship already exists
            if hasattr(model_class, field_name) and not isinstance(getattr(model_class, field_name), (Many2one, One2many, Many2many)):
                continue
                
            if isinstance(field_obj, Many2one):
                # Find the target model class
                target_model = cls.get(field_obj.comodel_name)
                if target_model:
                    rel = relationship(
                        target_model.__name__,
                        foreign_keys=[field_obj._fk_column]
                    )
                    setattr(model_class, field_name, rel)
                    
            elif isinstance(field_obj, One2many):
                # Find the target model class
                target_model = cls.get(field_obj.comodel_name)
                if target_model:
                    rel = relationship(
                        target_model.__name__,
                        back_populates=field_obj.inverse_name
                    )
                    setattr(model_class, field_name, rel)
                    
            elif isinstance(field_obj, Many2many):
                # Find the target model class
                target_model = cls.get(field_obj.comodel_name)
                if target_model:
                    # Create association table name
                    table1 = model_class.__tablename__
                    table2 = target_model.__tablename__
                    association_table = f"{table1}_{table2}_rel"
                    
                    rel = relationship(
                        target_model.__name__,
                        secondary=association_table
                    )
                    setattr(model_class, field_name, rel)
        
        # Clean up pending relationships
        if hasattr(model_class, '_pending_relationships'):
            delattr(model_class, '_pending_relationships')