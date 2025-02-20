from abc import ABC


class Model(ABC):
    def validate(self):
        pass

    def model_dump(self):
        return vars(self)

    @classmethod
    def model_load(cls, data: dict):
        return cls(**data)

    def __str__(self):
        return str(vars(self))
