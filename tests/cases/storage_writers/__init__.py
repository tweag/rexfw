import unittest
from pickle import load
from tempfile import mkdtemp
import os

from rexfw.storage_writers import (FileSystemPickleStorageWriter,
                                   CloudPickleStorageWriter,
                                   sanitize_basename,
                                   pickle_to_stream)


class testFunctions(unittest.TestCase):

    def testSanitizeBasename(self):
        res1 = sanitize_basename('/this/is/a/path')
        expected1 = '/this/is/a/path/'
        self.assertEqual(res1, expected1)

        res2 = sanitize_basename('/this/is/a/path/')
        expected2 = '/this/is/a/path/'
        self.assertEqual(res2, expected2)

    def testPickleToStream(self):
        obj = ['a', 'list', 42]
        res = load(pickle_to_stream(obj))
        expected = obj
        self.assertEqual(res, expected)


class testFileSystemPickleStorageWriter(unittest.TestCase):
    def setUp(self):
        self._tmpdir = mkdtemp()
        self._writer = FileSystemPickleStorageWriter(self._tmpdir)

    def testConstructFilePath(self):
        res1 = self._writer._construct_file_path('test.txt', '/a/base/name')
        expected1 = '/a/base/name/test.txt'
        self.assertEqual(res1, expected1)

        res2 = self._writer._construct_file_path('test.txt', '/a/base/name/')
        expected2 = '/a/base/name/test.txt'
        self.assertEqual(res2, expected2)

        res3 = self._writer._construct_file_path('test.txt')
        expected3 = self._tmpdir + '/test.txt'
        self.assertEqual(res3, expected3)

    def testWrite(self):
        obj = ['a', 'list', 42]
        self._writer.write(obj, 'a_file.pickle')
        with open(self._tmpdir + '/a_file.pickle', 'rb') as ipf:
            res1 = load(ipf)
            self.assertEqual(obj, res1)

        different_basename = self._tmpdir + '/some_dir'
        os.mkdir(different_basename)
        self._writer.write(obj, 'another_file.pickle', different_basename)
        with open(different_basename + '/another_file.pickle', 'rb') as ipf:
            res2 = load(ipf)
            self.assertEqual(obj, res2)
    

class testCloudPickleStorageWriter(unittest.TestCase):

    def testConstructObjectName(self):
        writer1 = CloudPickleStorageWriter(None, None, 'some/base/name/')

        res1 = writer1._construct_object_name('some_file.pickle', 'a/base/name')
        expected1 = 'a/base/name/some_file.pickle'
        self.assertEqual(res1, expected1)

        res2 = writer1._construct_object_name('some_file.pickle', 'a/base/name/')
        expected2 = 'a/base/name/some_file.pickle'
        self.assertEqual(res2, expected2)

        res3 = writer1._construct_object_name('some_file.pickle')
        expected3 = 'some/base/name/some_file.pickle'
        self.assertEqual(res3, expected3)

        writer2 = CloudPickleStorageWriter(None, None, 'some/base/name')
        
        res4 = writer1._construct_object_name('some_file.pickle')
        expected4 = 'some/base/name/some_file.pickle'
        self.assertEqual(res4, expected4)
