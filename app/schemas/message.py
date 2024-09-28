from app.schemas.role import Role, BaseModelWithRoleEncoder


class Message(BaseModelWithRoleEncoder):
    role: Role
    content: str
