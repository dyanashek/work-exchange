from aiogram.fsm.state import State, StatesGroup


class CreateEmployer(StatesGroup):
    input_phone = State()
    