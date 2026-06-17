from typing import Protocol

class Animal(Protocol):
    """This is not instead of ABC, this is only for type checking"""
    def feed(self) -> None:
        pass

class Bird(Animal, Protocol):
    def fly(self) -> None:
        pass

class Duck:
    def feed(self) -> None:
        print("Duck eats")

    def fly(self) -> None:
        print("Duck flies")

def feed(animal: Animal) -> None:
    animal.feed()

def feed_bird(bird: Bird) -> None:
    bird.feed()
    bird.fly()

duck = Duck()
feed_bird(duck)