# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/Jamie-BitFlight/apt-registry-explorer/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                       |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/\_\_init\_\_.py |        3 |        0 |    100% |           |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/\_meta.py       |        5 |        2 |     60% |       7-8 |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/cli.py          |      170 |        4 |     98% |247, 264, 282, 344 |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/discovery.py    |       82 |       24 |     71% |36-67, 97, 157-158, 183-184 |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/packages.py     |      118 |       18 |     85% |78-102, 180, 249-250 |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/sources.py      |       93 |       10 |     89% |99-100, 103-104, 107, 128, 135, 166, 187-188 |
| packages/apt-registry-explorer/src/apt\_registry\_explorer/tui.py          |       63 |       22 |     65% |85-97, 113-128, 142-143, 153-154 |
| **TOTAL**                                                                  |  **534** |   **80** | **85%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/Jamie-BitFlight/apt-registry-explorer/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/Jamie-BitFlight/apt-registry-explorer/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Jamie-BitFlight/apt-registry-explorer/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/Jamie-BitFlight/apt-registry-explorer/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FJamie-BitFlight%2Fapt-registry-explorer%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/Jamie-BitFlight/apt-registry-explorer/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.