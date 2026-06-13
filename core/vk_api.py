import requests
from config.settings import API_VERSION


class VKAPI:
    def __init__(self, token):
        self.token = token
    
    def call(self, method, params=None, post=False):
        params = params or {}
        params.update({'v': API_VERSION, 'access_token': self.token})
        url = f'https://api.vk.com/method/{method}'
        
        try:
            if post:
                return requests.post(url, data=params, timeout=30).json()
            return requests.get(url, params=params, timeout=10).json()
        except Exception as e:
            return {'error': {'error_msg': str(e), 'error_code': -1}}
    
    def post_to_wall(self, gid, message):
        """Пост на стену группы"""
        return self.call('wall.post', {
            'owner_id': -gid,
            'message': message,
            'from_group': 0,
            'signed': 0
        }, post=True)
    
    def get_me(self):
        """Информация о пользователе"""
        return self.call('users.get')
