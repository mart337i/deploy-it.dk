from sqlalchemy import Column, Integer, String
from clicx.database import base 
from clicx.database import fields

class ResPartner(base.BaseModel):
    _name: str = 'res.partner'
    
    name = fields.Char(size=100, required=True, string="Name")
    email = fields.Char(size=255, string="Email")
    phone = fields.Char(size=50, string="Phone")
    is_company = fields.Boolean(string="Is Company", default=False)