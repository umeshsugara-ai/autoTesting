def pytest_sessionstart(session):
    import autotester.browser.observe as o
    print("PATHPROOF", o.__file__)
