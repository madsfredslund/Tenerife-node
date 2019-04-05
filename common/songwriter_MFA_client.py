#!/usr/bin/python
"""
   @author: Mads Fredslund Andersen
"""
import time
import xmlrpclib

server_name = "iodinepipe.kvmtenerife.prv"
server_port = 8048


def master_calib(date):
    """
    :param date: A date string. Format should be YYYMMDD,
    """

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.start_master_calib(date)
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1


def all_science(date):
    """
    :param date: A date string. Format should be YYYMMDD,
    """

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.start_science(date)
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1


def all_night(date):
    """
    :param date: A date string. Format should be YYYMMDD,
    """

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.start_all_night(date)
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1

def test(date):
    """
    :param date: A date string. Format should be YYYMMDD,
    """

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.test_daemon(date)
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1


def reduce_spectrum(filename, calib_date='nearest', fast=False):
    """
    :param filename: A filename string. Should be the absolute path.
    :param calib_date: A date string. Format should be YYYMMDD or use 'nearest'
    :param fast: A boolean. If True the fast reduction mode is used.
    """

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.reduce_spectrum(filename, calib_date, fast)
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1


def stop():

    #attempt connection to server
    server = xmlrpclib.ServerProxy('http://{0}:{1}/'.format(server_name, server_port))

    try:
        print server.stop()
    except Exception, e:
        print 'Could not connect to the server!'
        print e
	return "error"

    return 1


