Automatically apply errata to RFCs
==================================

The RFC_ series is a suite of documents published by the `RFC Editor`_ for the benefit of the
Internet community.  It contains technical and organizational documents about the Internet,
including the specifications and policy documents produced by four document streams within
the RFC series:  the Internet Engineering Task Force (IETF), the Internet Research Task
Force (IRTF), the Internet Architecture Board (IAB), and Independent Submissions.  Documents
in the RFC series are identified by a number and are frozen forever and cannot be changed.

The RFC Editor maintains a database of errata that have been submitted by the consumers of
RFCs.  These errata, once reported, can be verified, rejected or "held for document update."
The visibility of errata to the consumers of RFCs has historically been poor or nonexistent.
This program is part of an effort to raise the visibility of these errata.

This program pulls down a copy of the errata database from the `RFC Editor`_ and the text version
of an RFC_.  It then merges the errata and the text of the RFC_ to produce an HTML file.

.. _Internet-Draft: https://en.wikipedia.org/wiki/Internet_Draft
.. _RFC: https://en.wikipedia.org/wiki/Request_for_Comments
.. _RFC 7996 bis: https://datatracker.ietf.org/doc/draft-7996-bis
.. _RFC Editor: https://www.rfc-editor.org

Usage
=====

rfc-errata pulls all needed information to run from the `RFC Editor`_ website.  The tool can be
run either to update all RFCs that have errata or only a specific set of RFCs

**Basic Usage**: ``rfc-errata [options] [<list of RFCs>]``

**Options**
   The following parameters affect how svgcheck behaves, however none are required.

    ===============  ======================= ==================================================
    Short            Long                    Description
    ===============  ======================= ==================================================
    ``-s``           ``--server=``           provide a server to download errata and RFCs from
    .                ``--no-network``        do not download files from the website
    .                ``--templates=``        directory containing templates to be used
    .                ``--text=``             directory to store unmodified text RFCs in
    .                ``--html=``             directory to place modified HTML RFCs in
    .                ``--css=``              relative location for CSS files at final website
    .                ``--all``               update all RFCs rather than a list of RFCs
    .                ``--reported=``         apply 'reported' errata (yes/no)
    .                ``--held=``             apply 'held for update' errata (yes/no)
    .                ``--rejected=``         apply 'rejected' errata (yes/no)
    .                ``--verified=``         apply 'verified' errata (yes/no)
    .                ``--force``             rebuild all HTML files rather than using timestamps
    ``-v``           ``--verbose``           print extra information
    ``-V``           ``--version``           display the version number and exit
    ===============  ======================= ==================================================

Dependencies
============

None
