from Back_End.action_readiness_engine import ActionReadinessEngine
from Back_End.session_context import SessionContextManager

engine = ActionReadinessEngine()

# Test the method directly
msg = 'Navigate somewhere'
result = engine._try_resolve_source_url(msg)
print(f'_try_resolve_source_url("{msg}") = {result}')

# Check pronoun detection
pronouns = {'there', 'here', 'this site', 'that site', 'this page', 'that page', 'from there'}
print(f'Has pronoun ref: {any(ref in msg for ref in pronouns)}')

# Now test with context
manager = SessionContextManager()
ctx = manager.get_or_create('test_session')

ctx.set_last_ready_mission({
    'intent': 'extract',
    'action_object': 'names',
    'action_target': 'linkedin.com',
    'source_url': 'https://linkedin.com',
    'constraints': None,
})

engine2 = ActionReadinessEngine(session_context={})
engine2._context_obj = ctx

result2 = engine2._try_resolve_source_url(msg)
print(f'With context: _try_resolve_source_url("{msg}") = {result2}')

