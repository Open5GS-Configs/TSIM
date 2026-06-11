from abc import ABC, abstractmethod


class InfrastructureManager(ABC):
    def __init__(self, config):
        self.config = config


    @abstractmethod
    def callInfManager(self):
        pass


    @abstractmethod
    def populateVars(self):
        pass


    @abstractmethod
    def destroy(self):
        pass