def test_login_page_loads(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Log In' in response.data


def test_login_redirects_to_hub(client, admin_user):
    response = client.post('/auth/login',
                           data={'username': 'admin', 'password': 'admin123'},
                           follow_redirects=True)
    assert response.status_code == 200
    # Hub page has "Hub" title
    assert b'Hub' in response.data


def test_invalid_password_rejected(client, admin_user):
    response = client.post('/auth/login',
                           data={'username': 'admin', 'password': 'wrongpassword'})
    assert b'Invalid username or password' in response.data


def test_unauthenticated_inbound_redirects_to_login(client):
    response = client.get('/inbound/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_logout_clears_session(auth_client):
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert b'Log In' in response.data
