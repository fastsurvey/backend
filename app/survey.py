from abc import ABC, abstractmethod

class Survey(ABC):
    
    def __init__(
            self,
            identifier,
    ):
        self.identifier = identifier

    @abstractmethod
    def submit(self):
        pass

    @abstractmethod
    def verify(self, token):
        pass

    @abstractmethod
    def results(self):
        pass


class SingleChoiceSurvey(Survey):
    
    def __init__(
            self,
            identifier,
            choices,
    ):
        Survey.__init__(self, identifier)
        self.choices = choices

    def submit(self):
        print('Choice submitted!')

    def verify(self, token):
        print('Token verified!')

    def results(self):
        print(f'Results: {self.choices[0]}: 60% vs. {self.choices[1]}: 40%!')


if __name__ == "__main__":
    survey = SingleChoiceSurvey('first survey', ['A', 'B'])
    survey.results()
