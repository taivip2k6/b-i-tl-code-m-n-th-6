import unittest

from app import LEVELS, app, db, User


class CryptoQuestTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        self.client = app.test_client()
        with app.app_context():
            db.drop_all()
            db.create_all()

    def test_progression_and_explanations(self):
        reg = self.client.post('/register', json={
            'username': 'student',
            'password': 'secret123',
            'confirm_password': 'secret123'
        })
        self.assertEqual(reg.status_code, 201)

        login = self.client.post('/login', json={
            'username': 'student',
            'password': 'secret123'
        })
        self.assertEqual(login.status_code, 200)

        level1 = self.client.get('/level/1')
        self.assertEqual(level1.status_code, 200)
        payload = level1.get_json()
        self.assertIn('explanation', payload)
        self.assertGreaterEqual(payload['level'], 1)

        response = self.client.post('/decode/1', json={
            'ciphertext': 'Khoor, Zruog!',
            'param': '3'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    def test_vigenere_level_uses_matching_ciphertext(self):
        self.client.post('/register', json={
            'username': 'teacher',
            'password': 'secret123',
            'confirm_password': 'secret123'
        })
        self.client.post('/login', json={
            'username': 'teacher',
            'password': 'secret123'
        })

        with app.app_context():
            user = User.query.filter_by(username='teacher').first()
            user.current_level = 2
            db.session.commit()

        response = self.client.post('/decode/2', json={
            'ciphertext': 'Rijvs, Uyvjn!',
            'param': 'KEY'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    def test_levels_4_and_5_use_simple_answers(self):
        self.client.post('/register', json={
            'username': 'teacher',
            'password': 'secret123',
            'confirm_password': 'secret123'
        })
        self.client.post('/login', json={
            'username': 'teacher',
            'password': 'secret123'
        })

        with app.app_context():
            user = User.query.filter_by(username='teacher').first()
            user.current_level = 5
            db.session.commit()

        level4 = self.client.post('/decode/4', json={
            'ciphertext': LEVELS[3]['ciphertext'],
            'param': 'treasure'
        })
        self.assertEqual(level4.status_code, 200)
        self.assertTrue(level4.get_json()['success'])

        level5 = self.client.post('/decode/5', json={
            'ciphertext': LEVELS[4]['ciphertext'],
            'param': 'unlock'
        })
        self.assertEqual(level5.status_code, 200)
        self.assertTrue(level5.get_json()['success'])

    def test_security_level_is_supported(self):
        self.client.post('/register', json={
            'username': 'teacher',
            'password': 'secret123',
            'confirm_password': 'secret123'
        })
        self.client.post('/login', json={
            'username': 'teacher',
            'password': 'secret123'
        })

        with app.app_context():
            user = User.query.filter_by(username='teacher').first()
            user.current_level = 6
            db.session.commit()

        level6 = self.client.get('/level/6')
        self.assertEqual(level6.status_code, 200)

        response = self.client.post('/decode/6', json={
            'ciphertext': 'Two sessions used the same nonce to encrypt the treasure map.',
            'param': 'nonce_reuse'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])


if __name__ == '__main__':
    unittest.main()
