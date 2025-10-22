
from lion.bootstrap.constants import MIN_REPOS_MOVEMENT_ID


class IsLoaded():

    def __init__(self, movement_id=0):

        try:
            self.__movement = int(movement_id)
        except Exception:
            self.__movement = 0
            self.__str_id = movement_id

    @property
    def loaded(self):
        if self.__movement:
            return self.is_loaded(self.__movement)
        else:
            return not self.__str_id.lower().endswith('|empty')

    def is_loaded(self, m=0):
        try:
            return m < MIN_REPOS_MOVEMENT_ID
        except:
            return int(m) < MIN_REPOS_MOVEMENT_ID

    def is_repos(self, m):
        try:
            return m >= MIN_REPOS_MOVEMENT_ID
        except:
            return int(m) >= MIN_REPOS_MOVEMENT_ID


if __name__ == '__main__':
    print(IsLoaded(1000002).loaded)
    # print(__t.is_repos(5223233443))
