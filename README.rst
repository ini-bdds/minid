Minimal Viable Identifier Client
================================

A minid (Minimal Viable Identifier) is an identifier that is sufficiently simple to make creation and use trivial, while still having enough substance to make data easily findable, accessible, interoperable, and reusable (FAIR). 

The minid server code is available at `https://github.com/fair-research/minid-server <https://github.com/fair-research/minid-server>`_

A Newer Minid Client Available
------------------------------

This Minid Client will soon be discontinued and the service shutdown, please
use the newer `Minid Client here <https://github.com/fair-research/minid/tree/develop>`_.

Installation
------------

The minid client and CLI is avaialble on PyPI. You can install it with the following command::
  
  $ pip install minid
  
Alternatively, you can download the source code and install using setup tools::

  $ git clone git@github.com:ini-bdds/minid.git
  
  $ python setup.py install

Configuration
-------------

Before using the API you first need to validate your email address. Enter the following command::

  $ minid --register_user --email <email> --name <name> [--orcid <orcid>]

A unique code will be sent to your email address. You must present this code along with your 
email address when accessing the API. As a convenience you can specify this information in 
a minid configuration file (`~/.minid/minid-config.cfg`)


.. code-block:: ini

    [general]
    minid_server: http://minid.bd2k.org/minid
    user: <Name>
    email: <Email>
    orcid: <optional Orcid>
    code: <Code>


Usage
-----

The CLI supports the following simple operations (Note: the `--test` flag creates names in a test namespace that is removed periodically; remove that flag to create production minids.): 

* Create a new identifier (the `--location` option, if provided, must be at the end)::

    $ minid --test --register [--title <title>] <file_name> [--locations <loc1>..<locN>]
    
* Retrieve metadata about a file::

    $ minid --test <file_name>
    
* Retrieve metadata about an identifier::

    $ minid --test <identifier>

* Update metadata about an identifier:: 

    $ minid --test --update [--title <title>] [--status <status>] [--obsoleted_by <minid>] [--locations <loc1> <loc2>] <identifier>
    
*  View all minid options:: 

    $ minid -h

Landing pages are accessible via the minid website: minid.bd2k.org/minid/landingpage/<identifier>. 


file manifest format
--------------------
Minids can only be assigned to a single file. In order to assign a minid to a collection of files we recommend using a `BDBag <https://github.com/ini-bdds/bdbag>`_ or the minid file manifest format. 

The minid file manifest format is a JSON-based format that enumerates a list of files as JSON objects that have the following attributes:

* length: The length of the file in bytes.

* filename: The filename (or path) relative to the manifest file.

* One or more (only one of each) of the following `algorithm:checksum` key-value pairs:
  
  * md5:<md5 hex value>
  
  * sha256:<sha256 hex value>
  
  * sha512:<sha512 hex value>

* url: the URL to the file.

The manifest may be used to create a minid for a collection of files or alternatively as input to the minid batch-register command. 

Below is a sample file manifest configuration file::

  [
      {
          "length":321,
          "filename":"file1.txt",
          "md5":"5bbf5a52328e7439ae6e719dfe712200",
          "sha256":"2c8b08da5ce60398e1f19af0e5dccc744df274b826abe585eaba68c525434806",
          "url" : "globus://ddb59aef-6d04-11e5-ba46-22000b92c6ec/share/godata/file1.txt"
      },
      {
          "length": 632860,
          "filename": "minid_v0.1_Nov_2015.pdf",
          "sha256": "cacc1abf711425d3c554277a5989df269cefaa906d27f1aaa72205d30224ed5f",
          "url" : "http://bd2k.ini.usc.edu/assets/all-hands-meeting/minid_v0.1_Nov_2015.pdf"
      }
  ]


More information
----------------

"`I'll take that to go: Big data bags and minimal identifiers for exchange of large, complex datasets <https://zenodo.org/record/820878>`_" explains the motivation for Minids and the related BDBag construct, provides details on design and implementation, and gives examples of use.

"`Reproducible big data science: A case study in continuous FAIRness <https://www.biorxiv.org/content/early/2018/02/27/268755>`_" presents a use case in which BDBags and Minids are used to capture a transcription factor binding site analysis.

More information about the project can be found at: `http://minid.bd2k.org/ <http://minid.bd2k.org/>`_
