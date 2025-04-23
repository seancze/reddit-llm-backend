from enum import Enum


class Route(str, Enum):
    NOSQL = "nosql"
    VECTOR = "vector"
