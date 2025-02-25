from pydantic import BaseModel, computed_field


class ImageSchema(BaseModel):
    name: str

    @computed_field
    def repository(self) -> str:
        return self.name.split(":")[0]

    @computed_field
    def tag(self) -> str:
        return self.name.split(":")[1] or "latest"


class ContainerSchema(BaseModel):
    name: str
    image: ImageSchema
    port: int
    type: str
