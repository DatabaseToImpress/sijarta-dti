def session_context(request):
    """
    Context processor to add 'role' and 'user_name' to all templates.
    """
    return {
        'role': request.session.get('role', ''),
        'user_name': request.session.get('user_name', ''),
    }
