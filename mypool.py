from pyrope.core import Quiz 

from mytask import Einstein
from pyrope import examples

from pyrope.templates import IntegerDivision, QuadraticEquation

pool = Quiz(
    title='mein eigenes quiz',
    navigation='sequential',
    weights={0:3,1:2,2:4},
    items = [
    Einstein(),
    Quiz(
        title = 'Unterquiz',
        navigation = 'free',
        select=2,
        items = [
        IntegerDivision(),
        Quiz(
            title = 'Leichte Aufgaben',
            navigation = 'sequential',
            weights = { 0: 1, 1: 1},
            shuffle=False,
            select=3,
            items = [
            examples.FortyTwo(),
            Einstein(),
            examples.CinemaTickets(),
            examples.Factor()
        ]),
        QuadraticEquation(),
    ]),
    examples.Factor()
],
)
pool[1].weights = {
    0: 4,
    2: 2
}