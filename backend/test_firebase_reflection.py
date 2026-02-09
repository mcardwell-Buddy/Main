from backend.memory import memory

if __name__ == '__main__':
    key = 'last_reflection:search for best practices for autonomous agents'
    data = memory.safe_call('get', key)
    print('Reflection stored in Firebase:')
    print(data)
