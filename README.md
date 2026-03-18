# todocli

A simple command-line to-do list manager built with Python

## Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## Installation

```bash
git clone https://github.com/ysanne617/todocli.git
cd todocli
pip install -r requirements.txt
```

## Usage
- Show all current tasks:
```bash
python todo.py list
```

- Add a new task
```bash
python todo.py add "buy milk" --priority medium
```

- Delete a task
```bash
python todo.py delete 1 # delete task with ID 1
```

- Mark a task as done
```bash
python todo.py complete 2 # mark task with ID 2 as completed
```