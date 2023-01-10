Version ongoing
---------------

Internal creation of proxy auxiliaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is no longer necessary to manually defined a ``ProxyAuxiliary`` with
``CCProxy``s yourself. If you simply pass the communication channel to
each auxiliary that has to share it, ``pykiso`` will do the rest for you.
