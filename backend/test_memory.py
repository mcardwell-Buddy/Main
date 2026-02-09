from backend.memory import memory

if __name__ == '__main__':
    print('Memory backend:', type(memory).__name__)
    key = 'test_key'
    value = {'ok': True}
    print('Set:', memory.safe_call('set', key, value))
    print('Get:', memory.safe_call('get', key))
