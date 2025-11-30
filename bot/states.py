from aiogram.fsm.state import State, StatesGroup

class DealStates(StatesGroup):
    waiting_for_ton_address = State()