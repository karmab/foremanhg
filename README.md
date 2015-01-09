			README
			======

	    foremanhg.py repository
	    ------------------------------

About the name ?
---------------

Initially named charlie.py because starting from  07/01/2015, #jesuischarlie

Freedom matters

What it does
------------

This script interacts with foreman to do the following:

- parse your plan file to create hostgroups ( optionally with the desired puppetclasses ) 
- parse your keys file and based on the key=value there, create smart class parameter overrides for those hostgroups for every associated class ( can also be done globally as default parameters of the class )
- if you specify key= in the keys files, value will rather be a random string of characters  (16 per default )

Note you can create multiple client sections in foreman.ini to reuse the script when desired
 
Requisites
------------

- python-requests package
- ~/foreman.ini in your home directory (look at sample for syntax)

Contents
--------

    README.txt                      this file
    foremanhg.py	            deploying script
    foremanhg.plan	            deployment plan
    foremanhg.keys		    parameters file
    foreman.ini		            sample configuration file to be edited to match your environment and copied to $HOME 
                                                            
Typical uses
---------

    # list available clients
    foremanhg.py -l

    # switch to specific client 
    foremanhg.py -9 NSA

    #generates global overrides
    foremanhg.py -i

    #generates hostgroups and overrides, and creates a backup file ( for replays)
    foremanhg.py -bno 

    #base the generation on a specific keys file
    foremanhg.py -no -k foremanhg.keys_20140909_0031

    #base the generation on a specific plan file
    foremanhg.py -no -p x.plan

    #get class details ( all its parameters)
    foremanhg.py -dc quickstack::neutron::controller

    #remove existing hostgroups (grabbing list from plan file)
    foremanhg.py -D

Problems?
---------

Send me a mail at karimboumedhel@gmail.com !

Mac Fly!!!

karmab
