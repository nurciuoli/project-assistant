from typing import List
from typing import Literal
from pydantic import BaseModel
class FileManager(BaseModel):
    name_no_ext:str
    allowed_file_ext: Literal['.txt','.py', '.html','.md']
    content:str

