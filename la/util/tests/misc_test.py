"util.misc unit tests."

import unittest

import numpy as np
from numpy.testing import assert_equal

from la.util.misc import randstring, isint, isfloat, isscalar, listmap


class Test_misc(unittest.TestCase):
    "Test util.misc."
        
    def test_randstring_1(self):
        "util.misc.randstring_1"
        rs = randstring(4)
        self.assert_(len(rs) == 4, 'Wrong length string.')

def test_isa():
    "util.misc.isint, isfloat, isscalar"
    t = {}
    # The keys are tuples otherwise #1 and #6, for example, would have
    # the same key
    #                            int    float
    t[(1, 1)]                 = (True,  False)
    t[(1.1, 2)]               = (False, True)
    t[('a', 3)]               = (False, False)
    t[(True, 4)]              = (False, False)
    t[(False, 5)]             = (False, False)
    t[(np.array(1)[()], 6)]   = (True,  False)
    t[(np.array(1.1)[()], 7)] = (False, True)
    t[(1j, 8)]                = (False, False)
    for key, value in t.iteritems():
        key = key[0]
        msg = '\nisint(' + str(key) + ')'
        yield assert_equal, isint(key), value[0], msg
        msg = '\nisfloat(' + str(key) + ')'
        yield assert_equal, isfloat(key), value[1], msg
        msg = '\nisscalar(' + str(key) + ')'
        yield assert_equal, isscalar(key), (value[0] or value[1]), msg
                        
def suite():
    s = []
    u = unittest.TestLoader().loadTestsFromTestCase
    s.append(u(Test_misc))
    return unittest.TestSuite(s)

def run():   
    suite = suite()
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run()           

# ---------------------------------------------------------------------------

# listmap
#
# test to make sure listmap returns the same output as
#
#                     idx = map(list1.index, list2)        

def listmap_test():
    "listmap test"
    list1 = range(6)
    list2 = range(5)
    msg = "listmap failed on list1=%s and list2=%s and ignore_unmappable=%s"
    for i in range(100):
        np.random.shuffle(list2)
        idx1 = map(list1.index, list2)
        idx2 = listmap(list1, list2)
        ignore_unmappable = False
        yield assert_equal, idx1, idx2, msg % (list1, list2, ignore_unmappable)
        ignore_unmappable = True
        yield assert_equal, idx1, idx2, msg % (list1, list2, ignore_unmappable)              

def listmap_unmappable_test():
    "listmap unmappable test"
    msg = "listmap failed on list1=%s and list2=%s and ignore_unmappable=%s"
    for i in range(100):
        list1 = range(6)
        list2 = range(5)
        np.random.shuffle(list2)
        idx1 = map(list1.index, list2)
        list2 = ['unmappable #1'] + list2 + ['unmappable #2']
        ignore_unmappable = True
        idx2 = listmap(list1, list2, ignore_unmappable=ignore_unmappable)
        yield assert_equal, idx1, idx2, msg % (list1, list2, ignore_unmappable) 
