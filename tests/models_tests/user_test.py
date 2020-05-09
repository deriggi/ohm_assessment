from tests import OhmTestCase


class UserTest(OhmTestCase):
    def test_get_multi(self):
        assert self.chuck.get_multi("PHONE") == ['+14086441234', '+14086445678']
        assert self.justin.get_multi("PHONE") == []
    
    def test_tiers(self):
        assert self.chuck.is_below_tier2('Bronze')
        assert not self.chuck.is_below_tier2('Carbon')
        assert not self.chuck.is_below_tier2('Nope')


