#!/usr/bin/env python
"""
Run script for the Voting System project.
This script changes to the core directory and runs the Django development server.
"""

import os
import sys
import subprocess

def main():
    # Change to the core directory
    os.chdir('core')
    
    # Run the Django development server
    cmd = [sys.executable, 'manage.py', 'runserver']
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    subprocess.run(cmd)

if __name__ == '__main__':
    main()
