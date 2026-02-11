from Back_End.agent import Agent

if __name__ == '__main__':
    a = Agent('search for best practices for autonomous agents')
    for _ in range(10):
        s = a.step()
        print(s)
        if s.get('done'):
            break

