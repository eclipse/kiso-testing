def pytest_collection_modifyitems(session, config, items):
    for item in items:
        for marker in item.iter_markers(name="test_key"):
            test_key = marker.args[0]
            item.user_properties.append(("test_key", test_key))
