import unittest
from JumpScale import j
from JumpScale.grid.osis2.client import NotFound, RemoteError

class RosTest(object):
    NAME = None
    TABLE = 'user'

    def setUp(self):
        self.cl = j.clients.osis2.get()
        self.tcl = getattr(self.cl, self.NAME)
        self.bucket = getattr(self.tcl, self.TABLE)
        for e in self.bucket.list():
            self.bucket.delete(e)
            
    def tearDown(self):
        for e in self.bucket.list():
            self.bucket.delete(e)

    def test_count(self):
        self.assertEqual(self.bucket.count(), 0)
        self.test_set(name='ali')
        self.assertEqual(self.bucket.count(), 1)
        self.assertEqual(self.bucket.count({'id':'noname'}), 0)
        self.assertEqual(self.bucket.count({'id':'ali'}), 1)
        for e in self.bucket.list():
            self.bucket.delete(e)
        self.assertEqual(self.bucket.count(), 0)
        self.assertEqual(self.bucket.count({'id':'noname'}), 0)
        self.assertEqual(self.bucket.count({'id':'ali'}), 0)
    
    def test_new(self):
        self.assertIsNotNone(self.bucket.new())
  
    def test_set(self, name='My Name'):
        user = self.bucket.new()
        user.guid = j.base.idgenerator.generateGUID()
        user.id = name
        user.data = 'some random data'
        user.domain = 'mydomain'
        response = self.bucket.set(user)
        self.assertIsInstance(response, dict)
        self.assertEqual(response['_status'], 'OK', msg=response)
        return user
   
    def test_notfound(self):
        self.assertRaises(NotFound, self.bucket.get, 'somerandomid')
    
    def test_get(self):
        user = self.test_set()
        user2 = self.bucket.get(user.guid)
        self.assertEqual(user.guid, user2.guid)
    
    def test_update(self):
        user = self.test_set()
        user.domain = 'adomain'
        self.bucket.update(user)
        newuser = self.bucket.get(user.guid)
        self.assertEqual(newuser.domain, 'adomain')
    
    def test_exists(self):
        user = self.test_set()
        self.assertTrue(self.bucket.exists(user.guid))
        self.assertFalse(self.bucket.exists('ranomdid'))
    
    def test_search(self):
        randomname = j.base.idgenerator.generateGUID()
        self.test_set(name=randomname)
        results = self.bucket.search({'id': randomname})
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
    
    def test_list(self):
        self.test_set()
        results = self.bucket.list()
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
  
    def test_delete(self):
        self.test_set()
        res = self.bucket.list()
        self.assertEquals(len(res), 1)
        for e in self.bucket.list():
            self.bucket.delete(e)
        res2 = self.bucket.list()
        self.assertEquals(len(res2), 0)
      
class RosMongoTest(RosTest, unittest.TestCase):
    NAME = 'testsystem'
     
    def test_mongo_hooks(self):
        u = self.bucket.new()
        u.guid = 'myguid'
        u.id = 'ID'
        u.data = 'some random data'
        u.domain = 'mydomain'
        self.bucket.set(u)
        res = self.bucket.get('myguid')
        self.assertEquals(res.guid, 'myguid')
        self.bucket.delete('myguid')
  
        u2 = self.bucket.new()
        u2.id = 'ID'
        u2.data = 'some random data'
        u2.domain = 'mydomain'
        self.bucket.set(u2)
        res = self.bucket.list()
        self.assertEquals(len(res), 1)
        # make sure it's guid
        self.assertEquals(len(res[0].split('-')), 5)
         
    
    def test_nestedmodeldef(self):
        testsbucket = getattr(self.tcl, 'tests')
        tests = testsbucket.new()
        tests.guid = 'myguid'
        tests.id = 2
        tests.test = {'value':2}
        testsbucket.set(tests)
        
        res = testsbucket.get('myguid')
        self.assertEquals(res.test, {'value':2})
        
        tests = testsbucket.new()
        tests.guid = 'myguid'
        tests.id = 2
        tests.test = {'value':'sss'}
        
        self.assertRaises(RemoteError, testsbucket.set, tests)
        
class RosSqlTest(RosTest, unittest.TestCase):
    NAME = 'sqlnamespace'
 
class SqlAlchemySqlTest(RosTest, unittest.TestCase):
    NAME = 'testsqlnamespace'
    TABLE = 'employee'
     
    def test_sql_hooks(self):
        self.assertEquals(len(self.bucket.list()), 0)
        u = self.bucket.new()
        u.guid = 'myguid'
        u.data = 'some random data'
        u.domain = 'willbereplaceddomain'
        self.bucket.set(u)
        self.assertEquals(len(self.bucket.list()), 1)
        u = self.bucket.get('myguid')
        self.assertEquals(u.id, 'autogeneratedid')  # This id is set by the namespace hook precreate
        self.assertEquals(u.domain, 'newdomain') # set by per object hook and overrides what is in per namespace hook

if __name__ == '__main__':
    unittest.main()