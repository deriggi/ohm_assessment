from tests import OhmTestCase


class UserTest(OhmTestCase):
    def test_get_multi(self):
        assert self.chuck.get_multi("PHONE") == ['+14086441234', '+14086445678']
        assert self.justin.get_multi("PHONE") == []

        # confirm that data conforms to unique constraints in db
        assert self.justin.username !=  self.chuck.username
        assert self.chuck.username !=  self.elvis.username 
    
    def test_tiers(self):
        assert self.chuck.is_below_tier('Bronze')
        assert not self.chuck.is_below_tier('Carbon')
        assert not self.chuck.is_below_tier('Nope')


