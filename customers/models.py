from django.db import models





class MongoUser:
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']

    def __str__(self):
        return self.username

    @property
    def is_authenticated(self):
        return True

    @property
    def pk(self):
        return self.id


