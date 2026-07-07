from abc import ABC, abstractmethod
from cases import Case

class MediaService(ABC):

    @abstractmethod
    def extract(self, case: Case):
        pass

    def analyse(self, case: Case):
        self.extract(case)