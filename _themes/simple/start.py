#!/usr/bin/python
#coding=utf-8
import os,sys
import subprocess

if __name__ == '__main__':
    script = "python -m SimpleHTTPServer 8001"
    cli=script.split(' ')
    subprocess.call(cli)

